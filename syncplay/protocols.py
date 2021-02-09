import json
import time
from functools import wraps
import logging

from twisted.protocols.basic import LineReceiver
from twisted.internet.protocol import ClientFactory
from twisted.internet import reactor

from autobahn.twisted.websocket import WebSocketServerProtocol


class JSONCommandProtocol(LineReceiver):
    def lineReceived(self, line: bytes) -> None:
        try:
            line = line.decode('utf-8').strip()
        except UnicodeDecodeError:
            self.handleError("Not a utf-8 string")
            self.drop()
            return
        if not line:
            return
        try:
            messages = json.loads(line)
        except json.decoder.JSONDecodeError:
            self.handleError("Not a json encoded string {}".format(line))
            self.drop()
            return
        else:
            self.messageRecieved(messages)

    def sendMsg(self, dict_: dict) -> None:
        line = json.dumps(dict_)
        self.sendLine(line.encode('utf-8'))

    def drop(self) -> None:
        self.transport.loseConnection()

    def handleError(self, _error):
        raise NotImplementedError()


class SyncplayProxyProtocol(JSONCommandProtocol):
    def __hash__(self) -> int:
        return hash('|'.join((
            self.transport.getPeer().host,
            str(id(self)),
        )))

    def drop(self) -> None:
        self.transport.loseConnection()
        self.connectionLost(None)

    def handleError(self, error) -> None:
        logging.error("Drop: {} -- {}".format(self.transport.getPeer().host, error))
        self.sendMsg({"Error": {"message": error}})
        self.drop()


class SyncplayProxyClientProtocol(SyncplayProxyProtocol):
    def connectionMade(self):
        self.factory.server.client = self
        while self.factory.server.buffer:
            self.messageRecieved(self.factory.server.buffer.pop())

    def connectionLost(self, _):
        self.factory.server.client = None
        self.factory.server.drop()

    def messageRecieved(self, messages):
        self.factory.server.sendMsg(messages)


class WSJSONCommandProtocol(WebSocketServerProtocol):
    def onMessage(self, line: bytes, isBinary: bool) -> None:
        if isBinary:
            self.handleError("Not a utf-8 string")
            self.drop()
            return

        try:
            line = line.decode('utf-8').strip()
        except UnicodeDecodeError:
            self.handleError("Not a utf-8 string")
            self.drop()
            return

        if not line:
            return

        try:
            messages = json.loads(line)
        except json.decoder.JSONDecodeError:
            self.handleError("Not a json encoded string {}".format(line))
            self.drop()
            return
        else:
            self.messageRecieved(messages)

    def sendMsg(self, dict_: dict) -> None:
        line = json.dumps(dict_)
        self.sendMessage(line.encode('utf-8'), false)

    def drop(self) -> None:
        self.transport.loseConnection()

    def handleError(self, _error):
        raise NotImplementedError()


class SyncplayWSServerProtocol(WSJSONCommandProtocol):
    def __init__(self, factory):
        self._factory = factory
        self._features = None
        self._logged = False

    def connectionMade(self):
        self.buffer = []
        self.client = None

        cli_factory = ClientFactory()
        cli_factory.protocol = SyncplayProxyClientProtocol
        cli_factory.server = self

        host_name, host_port = self._factory.host_name, self._factory.host_port
        reactor.connectTCP(host_name, host_port, cli_factory)

    def connectionLost(self, _):
        tmpClient = self.client
        if tmpClient is not None:
            self.client = None
            tmpClient.drop()

    def messageRecieved(self, messages: dict) -> None:
        tlsMsg = messages.pop("TLS", None)
        if tlsMsg is not None:
            self.handleTLS(tlsMsg)

        if "Hello" in messages.keys():
            messages["Hello"]["user_ip"] = self.transport.getPeer().host

        if len(messages) != 0:
            self.proxyMessages(messages)

    def proxyMessages(self, messages) -> None:
        if self.client is not None:
            self.client.sendMsg(messages)
        else:
            self.buffer.append(messages)

    def sendTLS(self, message) -> None:
        self.sendMsg({"TLS": message})

    def handleTLS(self, message) -> None:
        inquiry = message.get("startTLS")
        if "send" in inquiry:
            self.sendTLS({"startTLS": "false"})


class SyncplayTCPServerProtocol(JSONCommandProtocol):
    def __init__(self, factory):
        self._factory = factory
        self._features = None
        self._logged = False

    def connectionMade(self):
        self.buffer = []
        self.client = None

        cli_factory = ClientFactory()
        cli_factory.protocol = SyncplayProxyClientProtocol
        cli_factory.server = self

        host_name, host_port = self._factory.host_name, self._factory.host_port
        reactor.connectTCP(host_name, host_port, cli_factory)

    def connectionLost(self, _):
        tmpClient = self.client
        if tmpClient is not None:
            self.client = None
            tmpClient.drop()

    def messageRecieved(self, messages: dict) -> None:
        tlsMsg = messages.pop("TLS", None)
        if tlsMsg is not None:
            self.handleTLS(tlsMsg)

        if "Hello" in messages.keys():
            messages["Hello"]["user_ip"] = self.transport.getPeer().host

        if len(messages) != 0:
            self.proxyMessages(messages)

    def proxyMessages(self, messages) -> None:
        if self.client is not None:
            self.client.sendMsg(messages)
        else:
            self.buffer.append(messages)

    def sendTLS(self, message) -> None:
        self.sendMsg({"TLS": message})

    def handleTLS(self, message) -> None:
        inquiry = message.get("startTLS")
        if "send" in inquiry:
            if self._factory.serverAcceptsTLS:
                lastEditCertTime = self._factory.checkLastEditCertTime()
                if lastEditCertTime is not None and lastEditCertTime != self._factory.lastEditCertTime:
                    self._factory.updateTLSContextFactory()
                if self._factory.options is not None:
                    self.sendTLS({"startTLS": "true"})
                    self.transport.startTLS(self._factory.options)
                else:
                    self.sendTLS({"startTLS": "false"})
            else:
                self.sendTLS({"startTLS": "false"})
