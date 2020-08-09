import ast
import datetime
import hashlib
import itertools
import random
import os
import platform
import re
import string
import subprocess
import sys
import time
import traceback
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

from syncplay import constants
from syncplay.messages import getMessage

folderSearchEnabled = True


def retry(ExceptionToCheck, tries=4, delay=3, backoff=2, logger=None):
    """Retry calling the decorated function using an exponential backoff.

    http://www.saltycrane.com/blog/2009/11/trying-out-retry-decorator-python/
    original from: http://wiki.python.org/moin/PythonDecoratorLibrary#Retry

    :param ExceptionToCheck: the exception to check. may be a tuple of
        excpetions to check
    :type ExceptionToCheck: Exception or tuple
    :param tries: number of times to try (not retry) before giving up
    :type tries: int
    :param delay: initial delay between retries in seconds
    :type delay: int
    :param backoff: backoff multiplier e.g. value of 2 will double the delay
        each retry
    :type backoff: int
    :param logger: logger to use. If None, print
    :type logger: logging.Logger instance
    """
    def deco_retry(f):
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            try_one_last_time = True
            while mtries > 1:
                try:
                    # try_one_last_time = False
                    return f(*args, **kwargs)
                    break
                except ExceptionToCheck as e:
                    if logger:
                        msg = getMessage("retrying-notification").format(str(e), mdelay)
                        logger.warning(msg)
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            if try_one_last_time:
                return f(*args, **kwargs)
            return
        return f_retry  # true decorator
    return deco_retry


def formatSize(numOfBytes, precise=False) -> str:
    if numOfBytes == 0:  # E.g. when file size privacy is enabled
        return "???"
    try:
        megabytes = int(numOfBytes) / 1048576.0  # Technically this is a mebibyte, but whatever
        if precise:
            megabytes = round(megabytes, 1)
        else:
            megabytes = int(megabytes)
        return str(megabytes) + getMessage("megabyte-suffix")
    except:  # E.g. when filesize is hashed
        return "???"


def isASCII(s) -> bool:
    return all(ord(c) < 128 for c in s)


def limitedPowerset(s, minLength):
    return itertools.chain.from_iterable(itertools.combinations(s, r) for r in range(len(s), minLength, -1))


def truncateText(unicodeText, maxLength) -> str:
    try:
        unicodeText = unicodeText.decode('utf-8')
    except:
        pass
    try:
        return str(unicodeText.encode("utf-8"), "utf-8", errors="ignore")[:maxLength]
    except:
        pass
    return ""


def stripfilename(filename, stripURL) -> str:
    if filename:
        try:
            filename = filename
        except UnicodeDecodeError:
            pass
        filename = urllib.parse.unquote(filename)
        if stripURL:
            try:
                filename = urllib.parse.unquote(filename.split("/")[-1])
            except UnicodeDecodeError:
                filename = urllib.parse.unquote(filename.split("/")[-1])
        return re.sub(constants.FILENAME_STRIP_REGEX, "", filename)
    else:
        return ""


def stripRoomName(RoomName) -> str:
    if RoomName:
        try:
            return re.sub(constants.ROOM_NAME_STRIP_REGEX, "\g<roomnamebase>", RoomName)
        except IndexError:
            return RoomName
    else:
        return ""


def hashFilename(filename, stripURL=False) -> str:
    if isURL(filename):
        stripURL = True
    strippedFilename = stripfilename(filename, stripURL)
    try:
        strippedFilename = strippedFilename.encode('utf-8')
    except UnicodeDecodeError:
        pass
    filenameHash = hashlib.sha256(strippedFilename).hexdigest()[:12]
    return filenameHash


def hashFilesize(size):
    return hashlib.sha256(str(size).encode('utf-8')).hexdigest()[:12]


def sameHashed(string1raw, string1hashed, string2raw, string2hashed) -> bool:
    try:
        if string1raw.lower() == string2raw.lower():
            return True
    except AttributeError:
        pass
    if string1raw == string2raw:
        return True
    elif string1raw == string2hashed:
        return True
    elif string1hashed == string2raw:
        return True
    elif string1hashed == string2hashed:
        return True


def sameFilename(filename1, filename2) -> bool:
    try:
        filename1 = filename1
    except UnicodeDecodeError:
        pass
    try:
        filename2 = filename2
    except UnicodeDecodeError:
        pass
    stripURL = True if isURL(filename1) ^ isURL(filename2) else False
    if filename1 == constants.PRIVACY_HIDDENFILENAME or filename2 == constants.PRIVACY_HIDDENFILENAME:
        return True
    elif sameHashed(stripfilename(filename1, stripURL), hashFilename(filename1, stripURL), stripfilename(filename2, stripURL), hashFilename(filename2, stripURL)):
        return True
    else:
        return False


def meetsMinVersion(version, minVersion) -> bool:
    def versiontotuple(ver):
        return tuple(map(int, ver.split(".")))
    return versiontotuple(version) >= versiontotuple(minVersion)


def isURL(path) -> bool:
    if path is None:
        return False
    elif "://" in path:
        return True
    else:
        return False


def playlistIsValid(files) -> bool:
    if len(files) > constants.PLAYLIST_MAX_ITEMS:
        return False
    elif sum(map(len, files)) > constants.PLAYLIST_MAX_CHARACTERS:
        return False
    return True


class RoomPasswordProvider(object):
    CONTROLLED_ROOM_REGEX = re.compile("^\+(.*):(\w{12})$")
    PASSWORD_REGEX = re.compile("[A-Z]{2}-\d{3}-\d{3}")

    @staticmethod
    def isControlledRoom(roomName) -> bool:
        return bool(re.match(RoomPasswordProvider.CONTROLLED_ROOM_REGEX, roomName))

    @staticmethod
    def check(roomName, password, salt) -> bool:
        if not password or not re.match(RoomPasswordProvider.PASSWORD_REGEX, password):
            raise ValueError()

        if not roomName:
            raise NotControlledRoom()
        match = re.match(RoomPasswordProvider.CONTROLLED_ROOM_REGEX, roomName)
        if not match:
            raise NotControlledRoom()
        roomHash = match.group(2)
        computedHash = RoomPasswordProvider._computeRoomHash(match.group(1), password, salt)
        return roomHash == computedHash

    @staticmethod
    def getControlledRoomName(roomName, password, salt):
        return "+" + roomName + ":" + RoomPasswordProvider._computeRoomHash(roomName, password, salt)

    @staticmethod
    def _computeRoomHash(roomName, password, salt):
        roomName = roomName.encode('utf8')
        salt = salt.encode('utf8')
        password = password.encode('utf8')
        salt = hashlib.sha256(salt).hexdigest().encode('utf8')
        provisionalHash = hashlib.sha256(roomName + salt).hexdigest().encode('utf8')
        return hashlib.sha1(provisionalHash + salt + password).hexdigest()[:12].upper()


class RandomStringGenerator(object):
    @staticmethod
    def generate_room_password():
        parts = (
            RandomStringGenerator._get_random_letters(2),
            RandomStringGenerator._get_random_numbers(3),
            RandomStringGenerator._get_random_numbers(3)
        )
        return "{}-{}-{}".format(*parts)

    @staticmethod
    def generate_server_salt():
        parts = (
            RandomStringGenerator._get_random_letters(10),
        )
        return "{}".format(*parts)

    @staticmethod
    def _get_random_letters(quantity):
        return ''.join(random.choices(string.ascii_uppercase, k=quantity))

    @staticmethod
    def _get_random_numbers(quantity):
        return ''.join(random.choice(string.digits, k=quantity))


class NotControlledRoom(Exception):
    pass
