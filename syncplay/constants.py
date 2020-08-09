# coding:utf8

# You might want to change these
DEFAULT_PORT = 8999
RECENT_CLIENT_THRESHOLD = "1.6.5"  # This and higher considered 'recent' clients (no warnings)
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
PLAYLIST_MAX_CHARACTERS = 10000
PLAYLIST_MAX_ITEMS = 250
MAXIMUM_TAB_WIDTH = 350
TAB_PADDING = 30

# Max numbers are used by server (and client pre-connection).
# Once connected client gets values from server featureList (or uses 'fallback' versions for old servers)
MAX_CHAT_MESSAGE_LENGTH = 150  # Number of displayed characters
MAX_USERNAME_LENGTH = 150  # Number of displayed characters
MAX_ROOM_NAME_LENGTH = 35  # Number of displayed characters
MAX_FILENAME_LENGTH = 250  # Number of displayed characters

# Usually there's no need to adjust these
CONTROLLED_ROOMS_MIN_VERSION = "1.3.0"
USER_READY_MIN_VERSION = "1.3.0"
SHARED_PLAYLIST_MIN_VERSION = "1.4.0"
CHAT_MIN_VERSION = "1.5.0"
FEATURE_LIST_MIN_VERSION = "1.5.0"

# Changing these is usually not something you're looking for
PING_MOVING_AVERAGE_WEIGHT = 0.85

TLS_CERT_ROTATION_MAX_RETRIES = 10

# Note: Constants updated in client.py->checkForFeatureSupport
SERVER_MAX_TEMPLATE_LENGTH = 10000
