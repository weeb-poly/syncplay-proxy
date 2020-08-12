import argparse
import codecs
import hashlib
import os
import time
from string import Template
import logging

from twisted.enterprise import adbapi
from twisted.internet import task, reactor
from twisted.internet.protocol import Factory

try:
    from OpenSSL import crypto
    from OpenSSL.SSL import TLSv1_2_METHOD
    from twisted.internet import ssl
except:
    pass

import syncplay
from syncplay import constants
from syncplay.messages import getMessage
from syncplay.protocols import SyncServerProtocol
from syncplay.utils import RoomPasswordProvider, NotControlledRoom, RandomStringGenerator, meetsMinVersion, playlistIsValid, truncateText


class SyncFactory(Factory):
    isolateRooms: bool
    port: str
    password: str
    _salt: str
    disableReady: bool
    disableChat: bool
    maxChatMessageLength: int
    maxUsernameLength: int
    # certPath: Optional[str]
    serverAcceptsTLS: bool
    _TLSattempts: int

    def __init__(self, port: str = '', password: str = '', motdFilePath=None, isolateRooms: bool = False, salt=None,
                 disableReady: bool = False, disableChat: bool = False, maxChatMessageLength: int = constants.MAX_CHAT_MESSAGE_LENGTH,
                 maxUsernameLength: int = constants.MAX_USERNAME_LENGTH, statsDbFile=None, tlsCertPath=None):
        logging.info(getMessage("welcome-server-notification").format(syncplay.version))
        self.isolateRooms = isolateRooms
        self.port = port

        if password:
            password = password.encode('utf-8')
            password = hashlib.md5(password).hexdigest()
        self.password = password

        if salt is None:
            salt = RandomStringGenerator.generate_server_salt()
            logging.warning(getMessage("no-salt-notification").format(salt))
        self._salt = salt
        self._motdFilePath = motdFilePath
        self.disableReady = disableReady
        self.disableChat = disableChat

        self.maxChatMessageLength = maxChatMessageLength
        self.maxUsernameLength = maxUsernameLength

        if not isolateRooms:
            self._roomManager = RoomManager()
        else:
            self._roomManager = PublicRoomManager()

        self._statsDbHandle = None
        if statsDbFile is not None:
            self._statsDbHandle = DBManager(statsDbFile)
            self._statsRecorder = StatsRecorder(self._statsDbHandle, self._roomManager)
            statsDelay = 5 * (int(self.port) % 10 + 1)
            self._statsRecorder.startRecorder(statsDelay)

        self.certPath = tlsCertPath
        self.serverAcceptsTLS = False
        self._TLSattempts = 0
        if self.certPath is not None:
            self._allowTLSconnections(self.certPath)
        else:
            self.options = None

    def buildProtocol(self, addr):
        return SyncServerProtocol(self)

    def sendState(self, watcher: 'Watcher', doSeek: bool = False, forcedUpdate: bool = False) -> None:
        room = watcher.room
        if room:
            paused, position = room.isPaused(), room.getPosition()
            setBy = room.setBy
            watcher.sendState(position, paused, doSeek, setBy, forcedUpdate)

    def getFeatures(self) -> dict:
        features = {
            "isolateRooms": self.isolateRooms,
            "readiness": not self.disableReady,
            "managedRooms": True,
            "chat": not self.disableChat,
            "maxChatMessageLength": self.maxChatMessageLength,
            "maxUsernameLength": self.maxUsernameLength,
            "maxRoomNameLength": constants.MAX_ROOM_NAME_LENGTH,
            "maxFilenameLength": constants.MAX_FILENAME_LENGTH
        }
        return features

    def getMotd(self, userIp, username: str, room, clientVersion: str) -> str:
        oldClient = False
        if constants.WARN_OLD_CLIENTS:
            if not meetsMinVersion(clientVersion, constants.RECENT_CLIENT_THRESHOLD):
                oldClient = True
        if self._motdFilePath and os.path.isfile(self._motdFilePath):
            args = {"version": syncplay.version, "userIp": userIp, "username": username, "room": room}
            tmpl = codecs.open(self._motdFilePath, "r", "utf-8-sig").read()
            try:
                motd = Template(tmpl).substitute(args)
                if oldClient:
                    motdwarning = getMessage("new-syncplay-available-motd-message").format(clientVersion)
                    motd = f"{motdwarning}\n{motd}"
                if len(motd) < constants.SERVER_MAX_TEMPLATE_LENGTH:
                    return motd
                else:
                    return getMessage("server-messed-up-motd-too-long").format(constants.SERVER_MAX_TEMPLATE_LENGTH, len(motd))
            except ValueError:
                return getMessage("server-messed-up-motd-unescaped-placeholders")
        elif oldClient:
            return getMessage("new-syncplay-available-motd-message").format(clientVersion)
        else:
            return ""

    def addWatcher(self, watcherProtocol, username: str, roomName: str) -> None:
        roomName = truncateText(roomName, constants.MAX_ROOM_NAME_LENGTH)
        username = self._roomManager.findFreeUsername(username)
        watcher = Watcher(self, watcherProtocol, username)
        self.setWatcherRoom(watcher, roomName, asJoin=True)

    def setWatcherRoom(self, watcher: 'Watcher', roomName: str, asJoin: bool = False) -> None:
        roomName = truncateText(roomName, constants.MAX_ROOM_NAME_LENGTH)
        self._roomManager.moveWatcher(watcher, roomName)
        if asJoin:
            self.sendJoinMessage(watcher)
        else:
            self.sendRoomSwitchMessage(watcher)

        room = watcher.room
        roomSetByName = room.setBy.name if room.setBy else None
        watcher.setPlaylist(roomSetByName, room.playlist)
        watcher.setPlaylistIndex(roomSetByName, room.playlistIndex)
        if RoomPasswordProvider.isControlledRoom(roomName):
            for controller in room.controllers:
                watcher.sendControlledRoomAuthStatus(True, controller, roomName)

    def sendRoomSwitchMessage(self, watcher: 'Watcher') -> None:
        l = lambda w: w.sendSetting(watcher.name, watcher.room, None, None)
        self._roomManager.broadcast(watcher, l)
        l = lambda w: w.sendSetReady(watcher.name, watcher.isReady(), False)
        self._roomManager.broadcastRoom(watcher, l)

    def removeWatcher(self, watcher: 'Watcher') -> None:
        if watcher and watcher.room:
            self.sendLeftMessage(watcher)
            self._roomManager.removeWatcher(watcher)

    def sendLeftMessage(self, watcher: 'Watcher') -> None:
        l = lambda w: w.sendSetting(watcher.name, watcher.room, None, {"left": True})
        self._roomManager.broadcast(watcher, l)

    def sendJoinMessage(self, watcher: 'Watcher') -> None:
        l = lambda w: w.sendSetting(watcher.name, watcher.room, None, {"joined": True, "version": watcher.version, "features": watcher.getFeatures()}) if w != watcher else None
        self._roomManager.broadcast(watcher, l)
        l = lambda w: w.sendSetReady(watcher.name, watcher.isReady(), False)
        self._roomManager.broadcastRoom(watcher, l)

    def sendFileUpdate(self, watcher: 'Watcher') -> None:
        if watcher.getFile():
            l = lambda w: w.sendSetting(watcher.name, watcher.room, watcher.getFile(), None)
            self._roomManager.broadcast(watcher, l)

    def forcePositionUpdate(self, watcher: 'Watcher', doSeek, watcherPauseState) -> None:
        room = watcher.room
        if room.canControl(watcher):
            paused, position = room.isPaused(), watcher.getPosition()
            setBy = watcher
            l = lambda w: w.sendState(position, paused, doSeek, setBy, True)
            room.setPosition(watcher.getPosition(), setBy)
            self._roomManager.broadcastRoom(watcher, l)
        else:
            watcher.sendState(room.getPosition(), watcherPauseState, False, watcher, True)  # Fixes BC break with 1.2.x
            watcher.sendState(room.getPosition(), room.isPaused(), True, room.setBy, True)

    def getAllWatchersForUser(self, forUser):
        return self._roomManager.getAllWatchersForUser(forUser)

    def authRoomController(self, watcher: 'Watcher', password, roomBaseName=None) -> None:
        room = watcher.room
        roomName = roomBaseName if roomBaseName else room.name
        try:
            success = RoomPasswordProvider.check(roomName, password, self._salt)
            if success:
                watcher.room.addController(watcher)
            self._roomManager.broadcast(watcher, lambda w: w.sendControlledRoomAuthStatus(success, watcher.name, room._name))
        except NotControlledRoom:
            newName = RoomPasswordProvider.getControlledRoomName(roomName, password, self._salt)
            watcher.sendNewControlledRoom(newName, password)
        except ValueError:
            self._roomManager.broadcastRoom(watcher, lambda w: w.sendControlledRoomAuthStatus(False, watcher.name, room._name))

    def sendChat(self, watcher, message) -> None:
        message = truncateText(message, self.maxChatMessageLength)
        messageDict = {"message": message, "username": watcher.name}
        self._roomManager.broadcastRoom(watcher, lambda w: w.sendChatMessage(messageDict))

    def setReady(self, watcher, isReady, manuallyInitiated: bool = True) -> None:
        watcher.setReady(isReady)
        self._roomManager.broadcastRoom(watcher, lambda w: w.sendSetReady(watcher.name, watcher.isReady(), manuallyInitiated))

    def setPlaylist(self, watcher, files) -> None:
        room = watcher.room
        if room.canControl(watcher) and playlistIsValid(files):
            watcher.room.setPlaylist(files, watcher)
            self._roomManager.broadcastRoom(watcher, lambda w: w.setPlaylist(watcher.name, files))
        else:
            watcher.setPlaylist(room.name, room.playlist)
            watcher.setPlaylistIndex(room.name, room.playlistIndex)

    def setPlaylistIndex(self, watcher, index) -> None:
        room = watcher.room
        if room.canControl(watcher):
            watcher.room.setPlaylistIndex(index, watcher)
            self._roomManager.broadcastRoom(watcher, lambda w: w.setPlaylistIndex(watcher.name, index))
        else:
            watcher.setPlaylistIndex(room.name, room.playlistIndex)

    def _allowTLSconnections(self, path: str) -> None:
        try:
            privKey = open(path+'/privkey.pem', 'rt').read()
            certif = open(path+'/cert.pem', 'rt').read()
            chain = open(path+'/chain.pem', 'rt').read()

            self.lastEditCertTime = os.path.getmtime(path+'/cert.pem')

            privKeyPySSL = crypto.load_privatekey(crypto.FILETYPE_PEM, privKey)
            certifPySSL = crypto.load_certificate(crypto.FILETYPE_PEM, certif)
            chainPySSL = [crypto.load_certificate(crypto.FILETYPE_PEM, chain)]

            cipherListString = "ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:"\
                               "ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:"\
                               "ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384"
            accCiphers = ssl.AcceptableCiphers.fromOpenSSLCipherString(cipherListString)

            try:
                contextFactory = ssl.CertificateOptions(privateKey=privKeyPySSL, certificate=certifPySSL,
                                                        extraCertChain=chainPySSL, acceptableCiphers=accCiphers,
                                                        raiseMinimumTo=ssl.TLSVersion.TLSv1_2)
            except AttributeError:
                contextFactory = ssl.CertificateOptions(privateKey=privKeyPySSL, certificate=certifPySSL,
                                                        extraCertChain=chainPySSL, acceptableCiphers=accCiphers,
                                                        method=TLSv1_2_METHOD)

            self.options = contextFactory
            self.serverAcceptsTLS = True
            self._TLSattempts = 0
            logging.info("TLS support is enabled.")
        except Exception:
            self.options = None
            self.serverAcceptsTLS = False
            self.lastEditCertTime = None
            logging.exception("Error while loading the TLS certificates.")
            logging.info("TLS support is not enabled.")

    def checkLastEditCertTime(self):
        try:
            outTime = os.path.getmtime(self.certPath+'/cert.pem')
        except:
            outTime = None
        return outTime

    def updateTLSContextFactory(self) -> None:
        self._allowTLSconnections(self.certPath)
        self._TLSattempts += 1
        if self._TLSattempts < constants.TLS_CERT_ROTATION_MAX_RETRIES:
            self.serverAcceptsTLS = True


class StatsRecorder:
    _dbHandle: 'DBManager'
    _roomManagerHandle: 'RoomManager'

    def __init__(self, dbHandle: 'DBManager', roomManager: 'RoomManager'):
        self._dbHandle = dbHandle
        self._roomManagerHandle = roomManager

    def startRecorder(self, delay) -> None:
        try:
            self._dbHandle.connect()
            reactor.callLater(delay, self._scheduleClientSnapshot)
        except:
            logging.error("Failed to initialize stats database. Server Stats not enabled.")

    def _scheduleClientSnapshot(self) -> None:
        self._clientSnapshotTimer = task.LoopingCall(self._runClientSnapshot)
        self._clientSnapshotTimer.start(constants.SERVER_STATS_SNAPSHOT_INTERVAL)

    def _runClientSnapshot(self) -> None:
        try:
            snapshotTime = int(time.time())
            rooms = self._roomManagerHandle.exportRooms()
            for room in rooms.values():
                for watcher in room.watchers:
                    self._dbHandle.addVersionLog(snapshotTime, watcher.version)
        except:
            pass


class DBManager:
    _dbPath: str

    def __init__(self, dbpath: str):
        self._dbPath = dbpath
        self._connection = None

    def __del__(self) -> None:
        if self._connection is not None:
            self._connection.close()

    def connect(self) -> None:
        self._connection = adbapi.ConnectionPool("sqlite3", self._dbPath, check_same_thread=False)
        self._createSchema()

    def _createSchema(self) -> None:
        initQuery = 'CREATE TABLE IF NOT EXISTS clients_snapshots (snapshot_time integer, version string)'
        self._connection.runQuery(initQuery)

    def addVersionLog(self, timestamp, version) -> None:
        content = (timestamp, version, )
        self._connection.runQuery("INSERT INTO clients_snapshots VALUES (?, ?)", content)


class RoomManager:
    # _rooms: Dict[str, Room]

    def __init__(self):
        self._rooms = {}

    def broadcastRoom(self, sender: 'Watcher', whatLambda) -> None:
        room = sender.room
        if room and room.name in self._rooms:
            for receiver in room.watchers:
                whatLambda(receiver)

    def broadcast(self, sender: 'Watcher', whatLambda) -> None:
        for room in self._rooms.values():
            for receiver in room.watchers:
                whatLambda(receiver)

    def getAllWatchersForUser(self, sender: 'Watcher') -> list:
        watchers = []
        for room in self._rooms.values():
            for watcher in room.watchers:
                watchers.append(watcher)
        return watchers

    def moveWatcher(self, watcher: 'Watcher', roomName: str) -> None:
        roomName = truncateText(roomName, constants.MAX_ROOM_NAME_LENGTH)
        self.removeWatcher(watcher)
        room = self._getRoom(roomName)
        room.addWatcher(watcher)

    def removeWatcher(self, watcher: 'Watcher') -> None:
        oldRoom = watcher.room
        if oldRoom:
            oldRoom.removeWatcher(watcher)
            self._deleteRoomIfEmpty(oldRoom)

    def _getRoom(self, roomName: str) -> 'Room':
        if roomName not in self._rooms:
            if RoomPasswordProvider.isControlledRoom(roomName):
                self._rooms[roomName] = ControlledRoom(roomName)
            else:
                self._rooms[roomName] = Room(roomName)
        return self._rooms[roomName]

    def _deleteRoomIfEmpty(self, room: 'Room') -> None:
        if room.isEmpty() and room.name in self._rooms:
            del self._rooms[room.name]

    def findFreeUsername(self, username: str) -> str:
        username = truncateText(username, constants.MAX_USERNAME_LENGTH)
        allnames = set()
        for room in self._rooms.values():
            for watcher in room.watchers:
                allnames.add(watcher.name.lower())
        while username.lower() in allnames:
            username += '_'
        return username

    def exportRooms(self) -> dict:
        return self._rooms


class PublicRoomManager(RoomManager):
    def broadcast(self, sender: 'Watcher', what) -> None:
        self.broadcastRoom(sender, what)

    def getAllWatchersForUser(self, sender: 'Watcher'):
        return sender.room.watchers

    def moveWatcher(self, watcher: 'Watcher', room: str) -> None:
        oldRoom = watcher.room
        l = lambda w: w.sendSetting(watcher.name, oldRoom, None, {"left": True})
        self.broadcast(watcher, l)
        RoomManager.moveWatcher(self, watcher, room)
        watcher.setFile(watcher.getFile())


class Room:
    STATE_PAUSED = 0
    STATE_PLAYING = 1

    _name: str
    # _watchers: Dict[str, Watcher]
    _playState: int
    # _setBy: Optional[Watcher]
    _playlist: list
    # _playlistIndex: Optional[int]
    _lastUpdate: float
    # _position: Union[int, float]

    def __init__(self, name: str):
        self._name = name
        self._watchers = {}
        self._playState = self.STATE_PAUSED
        self._setBy = None
        self._playlist = []
        self._playlistIndex = None
        self._lastUpdate = time.time()
        self._position = 0

    def __str__(self, *args, **kwargs) -> str:
        return self.name

    @property
    def name(self) -> str:
        return self._name

    def getPosition(self):
        age = time.time() - self._lastUpdate
        if self._watchers and age > 1:
            watcher = min(self._watchers.values())
            self._setBy = watcher
            self._position = watcher.getPosition()
            self._lastUpdate = time.time()
            return self._position
        elif self._position is not None:
            pos = self._position
            if self._playState == self.STATE_PLAYING:
                pos += age
            return pos
        else:
            return 0

    def setPaused(self, paused=STATE_PAUSED, setBy=None) -> None:
        self._playState = paused
        self._setBy = setBy

    def setPosition(self, position, setBy=None) -> None:
        self._position = position
        for watcher in self._watchers.values():
            watcher.setPosition(position)
            self._setBy = setBy

    def isPlaying(self) -> bool:
        return self._playState == self.STATE_PLAYING

    def isPaused(self) -> bool:
        return self._playState == self.STATE_PAUSED

    @property
    def watchers(self) -> list:
        return list(self._watchers.values())

    def addWatcher(self, watcher: 'Watcher') -> None:
        if self._watchers:
            watcher.setPosition(self.getPosition())
        self._watchers[watcher.name] = watcher
        watcher.room = self

    def removeWatcher(self, watcher: 'Watcher') -> None:
        if watcher.name not in self._watchers:
            return
        del self._watchers[watcher.name]
        watcher.room = None
        if not self._watchers:
            self._position = 0

    def isEmpty(self) -> bool:
        return not bool(self._watchers)

    @property
    def setBy(self):
        return self._setBy

    def canControl(self, watcher: 'Watcher') -> bool:
        return True

    @property
    def playlist(self):
        return self._playlist

    @playlist.setter
    def playlist(self, files) -> None:
        self.setPlaylist(files)

    def setPlaylist(self, files, setBy=None) -> None:
        self._playlist = files

    @property
    def playlistIndex(self):
        return self._playlistIndex
    
    @playlistIndex.setter
    def playlistIndex(self, index) -> None:
        self.setPlaylistIndex(index)

    def setPlaylistIndex(self, index, setBy=None) -> None:
        self._playlistIndex = index


class ControlledRoom(Room):
    # _controllers: Dict[str, Watcher]

    def __init__(self, name: str):
        super().__init__(name)
        self._controllers = {}

    def getPosition(self):
        age = time.time() - self._lastUpdate
        if self._controllers and age > 1:
            watcher = min(self._controllers.values())
            self._setBy = watcher
            self._position = watcher.getPosition()
            self._lastUpdate = time.time()
            return self._position
        elif self._position is not None:
            pos = self._position
            if self._playState == self.STATE_PLAYING:
                pos += age
            return pos
        else:
            return 0

    def addController(self, watcher: 'Watcher') -> None:
        self._controllers[watcher.name] = watcher

    def removeWatcher(self, watcher: 'Watcher') -> None:
        Room.removeWatcher(self, watcher)
        if watcher.name in self._controllers:
            del self._controllers[watcher.name]

    def setPaused(self, paused=Room.STATE_PAUSED, setBy=None) -> None:
        if self.canControl(setBy):
            Room.setPaused(self, paused, setBy)

    def setPosition(self, position, setBy=None) -> None:
        if self.canControl(setBy):
            Room.setPosition(self, position, setBy)

    def setPlaylist(self, files, setBy=None) -> None:
        if self.canControl(setBy) and playlistIsValid(files):
            self._playlist = files

    def setPlaylistIndex(self, index, setBy=None) -> None:
        if self.canControl(setBy):
            self._playlistIndex = index

    def canControl(self, watcher: 'Watcher') -> bool:
        return watcher.name in self._controllers

    @property
    def controllers(self) -> dict:
        return self._controllers


class Watcher:
    _server: SyncFactory
    _name: str
    _lastUpdatedOn: float

    def __init__(self, server: SyncFactory, connector, name: str):
        self._ready = None
        self._server = server
        self._connector = connector
        self._name = name
        self._room = None
        self._file = None
        self._position = None
        self._lastUpdatedOn = time.time()
        self._sendStateTimer = None
        self._connector.setWatcher(self)
        reactor.callLater(0.1, self._scheduleSendState)

    def setFile(self, file_) -> None:
        if file_ and "name" in file_:
            file_["name"] = truncateText(file_["name"], constants.MAX_FILENAME_LENGTH)
        self._file = file_
        self._server.sendFileUpdate(self)

    def setReady(self, ready) -> None:
        self._ready = ready

    def getFeatures(self):
        features = self._connector.getFeatures()
        return features

    def isReady(self):
        if self._server.disableReady:
            return None
        return self._ready

    @property
    def room(self):
        return self._room

    @room.setter
    def room(self, room) -> None:
        self._room = room
        if room is None:
            self._deactivateStateTimer()
        else:
            self._resetStateTimer()
            self._askForStateUpdate(True, True)

    @property
    def name(self):
        return self._name

    @property
    def version(self):
        return self._connector.getVersion()

    def getFile(self):
        return self._file

    def setPosition(self, position) -> None:
        self._position = position

    def getPosition(self):
        if self._position is None:
            return None
        if self._room.isPlaying():
            timePassedSinceSet = time.time() - self._lastUpdatedOn
        else:
            timePassedSinceSet = 0
        return self._position + timePassedSinceSet

    def sendSetting(self, user: str, room: Room, file_, event) -> None:
        self._connector.sendUserSetting(user, room, file_, event)

    def sendNewControlledRoom(self, roomBaseName: str, password) -> None:
        self._connector.sendNewControlledRoom(roomBaseName, password)

    def sendControlledRoomAuthStatus(self, success, username: str, room: str) -> None:
        self._connector.sendControlledRoomAuthStatus(success, username, room)

    def sendChatMessage(self, message) -> None:
        if self._connector.meetsMinVersion(constants.CHAT_MIN_VERSION):
            self._connector.sendMessage({"Chat": message})

    def sendSetReady(self, username, isReady, manuallyInitiated: bool = True) -> None:
        self._connector.sendSetReady(username, isReady, manuallyInitiated)

    def setPlaylistIndex(self, username: str, index) -> None:
        self._connector.setPlaylistIndex(username, index)

    def setPlaylist(self, username: str, files) -> None:
        self._connector.setPlaylist(username, files)

    def __lt__(self, b) -> bool:
        if self.getPosition() is None or self._file is None:
            return False
        if b.getPosition() is None or b.getFile() is None:
            return True
        return self.getPosition() < b.getPosition()

    def _scheduleSendState(self) -> None:
        self._sendStateTimer = task.LoopingCall(self._askForStateUpdate)
        self._sendStateTimer.start(constants.SERVER_STATE_INTERVAL)

    def _askForStateUpdate(self, doSeek: bool = False, forcedUpdate: bool = False) -> None:
        self._server.sendState(self, doSeek, forcedUpdate)

    def _resetStateTimer(self) -> None:
        if self._sendStateTimer:
            if self._sendStateTimer.running:
                self._sendStateTimer.stop()
            self._sendStateTimer.start(constants.SERVER_STATE_INTERVAL)

    def _deactivateStateTimer(self) -> None:
        if self._sendStateTimer and self._sendStateTimer.running:
            self._sendStateTimer.stop()

    def sendState(self, position, paused, doSeek, setBy, forcedUpdate: bool) -> None:
        if self._connector.isLogged():
            self._connector.sendState(position, paused, doSeek, setBy, forcedUpdate)
        if time.time() - self._lastUpdatedOn > constants.PROTOCOL_TIMEOUT:
            self._server.removeWatcher(self)
            self._connector.drop()

    def __hasPauseChanged(self, paused) -> bool:
        if paused is None:
            return False
        return self._room.isPaused() and not paused or not self._room.isPaused() and paused

    def _updatePositionByAge(self, messageAge, paused, position):
        if not paused:
            position += messageAge
        return position

    def updateState(self, position, paused, doSeek, messageAge) -> None:
        pauseChanged = self.__hasPauseChanged(paused)
        self._lastUpdatedOn = time.time()
        if pauseChanged:
            self.room.setPaused(Room.STATE_PAUSED if paused else Room.STATE_PLAYING, self)
        if position is not None:
            position = self._updatePositionByAge(messageAge, paused, position)
            self.setPosition(position)
        if doSeek or pauseChanged:
            self._server.forcePositionUpdate(self, doSeek, paused)

    def isController(self) -> bool:
        return RoomPasswordProvider.isControlledRoom(self._room.name) \
            and self._room.canControl(self)

