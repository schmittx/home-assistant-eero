"""Constants used by the Eero integration."""
ATTR_DNS_CACHING_ENABLED = "dns_caching_enabled"
ATTR_IPV6_ENABLED = "ipv6_enabled"
ATTR_THREAD_ENABLED = "thread_enabled"
ATTR_EERO_NAME = "eero_name"
ATTR_NETWORK_NAME = "network_name"
ATTR_TIME_OFF = "time_off"
ATTR_TIME_ON = "time_on"

ATTRIBUTION = "Data provided by Eero"

CONF_CLIENTS = "clients"
CONF_CODE = "code"
CONF_EEROS = "eeros"
CONF_LOGIN = "login"
CONF_NAME = "name"
CONF_NETWORKS = "networks"
CONF_PROFILES = "profiles"
CONF_USER_TOKEN = "user_token"
CONF_WIRED_CLIENTS = "wired_clients"
CONF_WIRELESS_CLIENTS = "wireless_clients"

DATA_COORDINATOR = "coordinator"

DOMAIN = "eero"

ERROR_TIME_FORMAT = "Time {} should be format 'HH:MM'"

MANUFACTURER = "eero"

MODEL_CLIENT = "Client"
MODEL_EERO = "eero"
MODEL_NETWORK = "Network"
MODEL_PROFILE = "Profile"

NIGHTLIGHT_MODE_DISABLED= "disabled"
NIGHTLIGHT_MODE_AMBIENT = "ambient"
NIGHTLIGHT_MODE_SCHEDULE = "schedule"
NIGHTLIGHT_MODES = [
    NIGHTLIGHT_MODE_DISABLED,
    NIGHTLIGHT_MODE_AMBIENT,
    NIGHTLIGHT_MODE_SCHEDULE,
]

SERVICE_ENABLE_DNS_CACHING = "enable_dns_caching"
SERVICE_ENABLE_IPV6 = "enable_ipv6"
SERVICE_ENABLE_THREAD = "enable_thread"
SERVICE_RESTART_EERO = "restart_eero"
SERVICE_RESTART_NETWORK = "restart_network"
SERVICE_SET_NIGHTLIGHT_MODE = "set_nightlight_mode"

TYPE_BEACON = "beacon"
TYPE_CLIENT = "client"
TYPE_EERO = "eero"
TYPE_NETWORK = "network"
TYPE_PROFILE = "profile"

UNDO_UPDATE_LISTENER = "undo_update_listener"

CONF_SAVE_RESPONSES = "save_responses"
CONF_TIMEOUT = "timeout"

VALUES_SCAN_INTERVAL = [30, 60, 120, 300, 600]
VALUES_TIMEOUT = [10, 15, 30, 45, 60]

DEFAULT_SAVE_LOCATION = "/config/custom_components/eero/api/responses"
DEFAULT_SAVE_RESPONSES = False
DEFAULT_SCAN_INTERVAL = VALUES_SCAN_INTERVAL[2]
DEFAULT_TIMEOUT = VALUES_TIMEOUT[0]
