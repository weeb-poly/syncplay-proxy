# coding:utf8

# You might want to change these
DEFAULT_PORT = 8999
RECENT_CLIENT_THRESHOLD = "1.6.5"  # This and higher considered 'recent' clients (no warnings)
WARN_OLD_CLIENTS = True  # Use MOTD to inform old clients to upgrade
FALLBACK_INITIAL_LANGUAGE = "en"

# Changing these might be ok
PROTOCOL_TIMEOUT = 12.5
SERVER_STATE_INTERVAL = 1
SERVER_STATS_SNAPSHOT_INTERVAL = 3600
PLAYLIST_MAX_CHARACTERS = 10000
PLAYLIST_MAX_ITEMS = 250

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
