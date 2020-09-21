import hashlib
import random
import re
import string
import time
from typing import Union

from syncplay import constants
from syncplay.messages import getMessage


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


def truncateText(unicodeText: Union[bytes, str], maxLength: int) -> str:
    try:
        unicodeText = unicodeText.decode('utf-8')
    except:
        pass
    try:
        return str(unicodeText.encode("utf-8"), "utf-8", errors="ignore")[:maxLength]
    except:
        pass
    return ""


def meetsMinVersion(version: str, minVersion: str) -> bool:
    def versiontotuple(ver: str) -> tuple:
        return tuple(map(int, ver.split(".")))
    return versiontotuple(version) >= versiontotuple(minVersion)


def playlistIsValid(files: list) -> bool:
    if len(files) > constants.PLAYLIST_MAX_ITEMS:
        return False
    elif sum(map(len, files)) > constants.PLAYLIST_MAX_CHARACTERS:
        return False
    return True


class RoomPasswordProvider:
    CONTROLLED_ROOM_REGEX = re.compile("^\+(.*):(\w{12})$")
    PASSWORD_REGEX = re.compile("[A-Z]{2}-\d{3}-\d{3}")

    @staticmethod
    def isControlledRoom(roomName: str) -> bool:
        return bool(re.match(RoomPasswordProvider.CONTROLLED_ROOM_REGEX, roomName))

    @staticmethod
    def check(roomName: str, password: str, salt: str) -> bool:
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
    def getControlledRoomName(roomName: str, password: str, salt: str) -> str:
        return f"+{roomName}:" + RoomPasswordProvider._computeRoomHash(roomName, password, salt)

    @staticmethod
    def _computeRoomHash(roomName: str, password: str, salt: str) -> str:
        roomName = roomName.encode('utf8')
        salt = salt.encode('utf8')
        password = password.encode('utf8')
        salt = hashlib.sha256(salt).hexdigest().encode('utf8')
        provisionalHash = hashlib.sha256(roomName + salt).hexdigest().encode('utf8')
        return hashlib.sha1(provisionalHash + salt + password).hexdigest()[:12].upper()


class RandomStringGenerator:
    @staticmethod
    def generate_room_password() -> str:
        parts = (
            RandomStringGenerator._get_random_letters(2),
            RandomStringGenerator._get_random_numbers(3),
            RandomStringGenerator._get_random_numbers(3)
        )
        return "{}-{}-{}".format(*parts)

    @staticmethod
    def generate_server_salt() -> str:
        return RandomStringGenerator._get_random_letters(10)

    @staticmethod
    def _get_random_letters(quantity: int) -> str:
        return ''.join(random.choices(string.ascii_uppercase, k=quantity))

    @staticmethod
    def _get_random_numbers(quantity: int) -> str:
        return ''.join(random.choice(string.digits, k=quantity))


class NotControlledRoom(Exception):
    pass
