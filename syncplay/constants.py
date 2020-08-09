# coding:utf8
# code needed to get customized constants for different OS
import sys

# You might want to change these
DEFAULT_PORT = 8999
OSD_DURATION = 3.0
OSD_WARNING_MESSAGE_DURATION = 5.0
NO_ALERT_OSD_WARNING_DURATION = 13.0
UI_TIME_FORMAT = "[%X] "
RECENT_CLIENT_THRESHOLD = "1.6.5"  # This and higher considered 'recent' clients (no warnings)
MUSIC_FORMATS = [".mp3", ".m4a", ".m4p", ".wav", ".aiff", ".r", ".ogg", ".flac"] # ALL LOWER CASE!
WARN_OLD_CLIENTS = True  # Use MOTD to inform old clients to upgrade
LIST_RELATIVE_CONFIGS = True  # Print list of relative configs loaded
SHOW_CONTACT_INFO = True  # Displays dev contact details below list in GUI
SHOW_TOOLTIPS = True
WARN_ABOUT_MISSING_STRINGS = False  # (If debug mode is enabled)
FALLBACK_INITIAL_LANGUAGE = "en"
PLAYLIST_LOAD_NEXT_FILE_MINIMUM_LENGTH = 10  # Seconds
PLAYLIST_LOAD_NEXT_FILE_TIME_FROM_END_THRESHOLD = 5  # Seconds (only triggered if file is paused, e.g. due to EOF)
EXECUTABLE_COMBOBOX_MINIMUM_LENGTH = 30 # Minimum number of characters that the combobox will make visible

# Changing these might be ok
DELAYED_LOAD_WAIT_TIME = 2.5
AUTOMATIC_UPDATE_CHECK_FREQUENCY = 7 * 86400  # Days converted into seconds
DEFAULT_REWIND_THRESHOLD = 4
MINIMUM_REWIND_THRESHOLD = 3
DEFAULT_FASTFORWARD_THRESHOLD = 5
MINIMUM_FASTFORWARD_THRESHOLD = 4
FASTFORWARD_EXTRA_TIME = 0.25
FASTFORWARD_RESET_THRESHOLD = 3.0
FASTFORWARD_BEHIND_THRESHOLD = 1.75
SEEK_THRESHOLD = 1
SLOWDOWN_RATE = 0.95
DEFAULT_SLOWDOWN_KICKIN_THRESHOLD = 1.5
MINIMUM_SLOWDOWN_THRESHOLD = 1.3
SLOWDOWN_RESET_THRESHOLD = 0.1
DIFFERENT_DURATION_THRESHOLD = 2.5
PROTOCOL_TIMEOUT = 12.5
RECONNECT_RETRIES = 999
SERVER_STATE_INTERVAL = 1
SERVER_STATS_SNAPSHOT_INTERVAL = 3600
WARNING_OSD_MESSAGES_LOOP_INTERVAL = 1
AUTOPLAY_DELAY = 3.0
DO_NOT_RESET_POSITION_THRESHOLD = 1.0
SYNC_ON_PAUSE = True  # Client seek to global position - subtitles may disappear on some media players
PLAYLIST_MAX_CHARACTERS = 10000
PLAYLIST_MAX_ITEMS = 250
MAXIMUM_TAB_WIDTH = 350
TAB_PADDING = 30

# Max numbers are used by server (and client pre-connection). Once connected client gets values from server featureList (or uses 'fallback' versions for old servers)
MAX_CHAT_MESSAGE_LENGTH = 150  # Number of displayed characters
MAX_USERNAME_LENGTH = 150  # Number of displayed characters
MAX_ROOM_NAME_LENGTH = 35  # Number of displayed characters
MAX_FILENAME_LENGTH = 250  # Number of displayed characters

# Options for the File Switch feature:
FOLDER_SEARCH_FIRST_FILE_TIMEOUT = 25.0  # Secs - How long to wait to find the first file in folder search (to take account of HDD spin up)
FOLDER_SEARCH_TIMEOUT = 20.0  # Secs - How long to wait until searches in folder to update cache are aborted (after first file is found)
FOLDER_SEARCH_DOUBLE_CHECK_INTERVAL = 30.0  # Secs - Frequency of updating cache

# Usually there's no need to adjust these
DOUBLE_CHECK_REWIND = False
LAST_PAUSED_DIFF_THRESHOLD = 2
FILENAME_STRIP_REGEX = "[-~_\.\[\](): ]"
CONTROL_PASSWORD_STRIP_REGEX = "[^a-zA-Z0-9\-]"
ROOM_NAME_STRIP_REGEX = "^(\+)(?P<roomnamebase>.*)(:)(\w{12})$"
COMMANDS_UNDO = ["u", "undo", "revert"]
COMMANDS_CHAT = ["ch", "chat"]
COMMANDS_LIST = ["l", "list", "users"]
COMMANDS_PAUSE = ["p", "play", "pause"]
COMMANDS_ROOM = ["r", "room"]
COMMANDS_HELP = ['help', 'h', '?', '/?', r'\?']
COMMANDS_CREATE = ['c', 'create']
COMMANDS_AUTH = ['a', 'auth']
COMMANDS_TOGGLE = ['t', 'toggle']
CONTROLLED_ROOMS_MIN_VERSION = "1.3.0"
USER_READY_MIN_VERSION = "1.3.0"
SHARED_PLAYLIST_MIN_VERSION = "1.4.0"
CHAT_MIN_VERSION = "1.5.0"
FEATURE_LIST_MIN_VERSION = "1.5.0"

# Changing these is usually not something you're looking for
PLAYER_ASK_DELAY = 0.1
PING_MOVING_AVERAGE_WEIGHT = 0.85
STREAM_ADDITIONAL_IGNORE_TIME = 10

TLS_CERT_ROTATION_MAX_RETRIES = 10

USERLIST_GUI_USERNAME_COLUMN = 0
USERLIST_GUI_FILENAME_COLUMN = 3

# Note: Constants updated in client.py->checkForFeatureSupport
UI_COMMAND_REGEX = r"^(?P<command>[^\ ]+)(?:\ (?P<parameter>.+))?"
UI_OFFSET_REGEX = r"^(?:o|offset)\ ?(?P<sign>[/+-])?(?P<time>\d{1,9}(?:[^\d\.](?:\d{1,9})){0,2}(?:\.(?:\d{1,3}))?)$"
UI_SEEK_REGEX = r"^(?:s|seek)?\ ?(?P<sign>[+-])?(?P<time>\d{1,4}(?:[^\d\.](?:\d{1,6})){0,2}(?:\.(?:\d{1,3}))?)$"
PARSE_TIME_REGEX = r'(:?(?:(?P<hours>\d+?)[^\d\.])?(?:(?P<minutes>\d+?))?[^\d\.])?(?P<seconds>\d+?)(?:\.(?P<miliseconds>\d+?))?$'
MESSAGE_WITH_USERNAME_REGEX = "^(<(?P<username>[^<>]+)>)(?P<message>.*)"
SERVER_MAX_TEMPLATE_LENGTH = 10000
PRIVACY_SENDRAW_MODE = "SendRaw"
PRIVACY_SENDHASHED_MODE = "SendHashed"
PRIVACY_DONTSEND_MODE = "DoNotSend"
UNPAUSE_IFALREADYREADY_MODE = "IfAlreadyReady"
UNPAUSE_IFOTHERSREADY_MODE = "IfOthersReady"
UNPAUSE_IFMINUSERSREADY_MODE = "IfMinUsersReady"
UNPAUSE_ALWAYS_MODE = "Always"
INPUT_POSITION_TOP = "Top"
INPUT_POSITION_MIDDLE = "Middle"
INPUT_POSITION_BOTTOM = "Bottom"

PRIVACY_HIDDENFILENAME = "**Hidden filename**"
INVERTED_STATE_MARKER = "*"
ERROR_MESSAGE_MARKER = "*"
LOAD_SAVE_MANUALLY_MARKER = "!"
CONFIG_NAME_MARKER = ":"
CONFIG_VALUE_MARKER = "="
USERITEM_CONTROLLER_ROLE = 0
USERITEM_READY_ROLE = 1
FILEITEM_SWITCH_ROLE = 1
FILEITEM_SWITCH_NO_SWITCH = 0
FILEITEM_SWITCH_FILE_SWITCH = 1
FILEITEM_SWITCH_STREAM_SWITCH = 2
PLAYLISTITEM_CURRENTLYPLAYING_ROLE = 3

MESSAGE_NEUTRAL = "neutral"
MESSAGE_BADNEWS = "bad"
MESSAGE_GOODNEWS = "good"

OSD_NOTIFICATION = "notification"  # Also known as PrimaryOSD
OSD_ALERT = "alert"  # Also known as SecondaryOSD
OSD_CHAT = "chat"

CHATROOM_MODE = "Chatroom"
SCROLLING_MODE = "Scrolling"
