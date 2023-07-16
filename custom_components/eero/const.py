"""Constants used by the Eero integration."""
from .api.const import (
    ACTIVITY_ADBLOCK_DAY,
    ACTIVITY_ADBLOCK_MONTH,
    ACTIVITY_ADBLOCK_WEEK,
    ACTIVITY_BLOCKED_DAY,
    ACTIVITY_BLOCKED_MONTH,
    ACTIVITY_BLOCKED_WEEK,
    ACTIVITY_DATA_USAGE_DAY,
    ACTIVITY_DATA_USAGE_MONTH,
    ACTIVITY_DATA_USAGE_WEEK,
    ACTIVITY_INSPECTED_DAY,
    ACTIVITY_INSPECTED_MONTH,
    ACTIVITY_INSPECTED_WEEK,
)


ACTIVITY_MAP_TO_EERO = {
    "Ad Blocks (Day)": ACTIVITY_ADBLOCK_DAY,
    "Ad Blocks (Week)": ACTIVITY_ADBLOCK_WEEK,
    "Ad Blocks (Month)": ACTIVITY_ADBLOCK_MONTH,
    "Data Usage (Day)": ACTIVITY_DATA_USAGE_DAY,
    "Data Usage (Week)": ACTIVITY_DATA_USAGE_WEEK,
    "Data Usage (Month)": ACTIVITY_DATA_USAGE_MONTH,
    "Scans (Day)": ACTIVITY_INSPECTED_DAY,
    "Scans (Week)": ACTIVITY_INSPECTED_WEEK,
    "Scans (Month)": ACTIVITY_INSPECTED_MONTH,
    "Threat Blocks (Day)": ACTIVITY_BLOCKED_DAY,
    "Threat Blocks (Week)": ACTIVITY_BLOCKED_WEEK,
    "Threat Blocks (Month)": ACTIVITY_BLOCKED_MONTH,
}
ACTIVITY_MAP_TO_HASS = {v: k for k, v in ACTIVITY_MAP_TO_EERO.items()}

ACTIVITIES_DEFAULT = [
    ACTIVITY_MAP_TO_HASS[ACTIVITY_DATA_USAGE_WEEK],
]
ACTIVITIES_PREMIUM = list(ACTIVITY_MAP_TO_EERO.keys())

ACTIVITIES_DATA_USAGE_DEFAULT = [
    ACTIVITY_MAP_TO_HASS[ACTIVITY_DATA_USAGE_WEEK],
]
ACTIVITIES_DATA_USAGE_PREMIUM = [
    ACTIVITY_MAP_TO_HASS[ACTIVITY_DATA_USAGE_DAY],
    ACTIVITY_MAP_TO_HASS[ACTIVITY_DATA_USAGE_WEEK],
    ACTIVITY_MAP_TO_HASS[ACTIVITY_DATA_USAGE_MONTH],
]

ATTR_BLOCKED_APPS = "blocked_apps"
ATTR_DNS_CACHING_ENABLED = "dns_caching_enabled"
ATTR_IPV6_ENABLED = "ipv6_enabled"
ATTR_TARGET_EERO = "target_eero"
ATTR_TARGET_NETWORK = "target_network"
ATTR_TARGET_PROFILE = "target_profile"
ATTR_THREAD_ENABLED = "thread_enabled"
ATTR_TIME_OFF = "time_off"
ATTR_TIME_ON = "time_on"

CONF_ACTIVITY = "activity"
CONF_ACTIVITY_CLIENTS = "clients"
CONF_ACTIVITY_EEROS = "eeros"
CONF_ACTIVITY_NETWORK = "network"
CONF_ACTIVITY_PROFILES = "profiles"
CONF_BACKUP_NETWORKS = "backup_networks"
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

DATA_API = "api"
DATA_COORDINATOR = "coordinator"
DATA_UPDATE_LISTENER = "update_listener"

DOMAIN = "eero"

ERROR_TIME_FORMAT = "Time {} should be format 'HH:MM'"

MANUFACTURER = "eero"

MODEL_BACKUP_NETWORK = "Backup Network"
MODEL_CLIENT = "Client"
MODEL_EERO = "eero"
MODEL_NETWORK = "Network"
MODEL_PROFILE = "Profile"

RELEASE_URL = "https://support.eero.com/hc/en-us/articles/209636523-eero-Software-Release-Notes"

SERVICE_ENABLE_DNS_CACHING = "enable_dns_caching"
SERVICE_ENABLE_IPV6 = "enable_ipv6"
SERVICE_ENABLE_THREAD = "enable_thread"
SERVICE_SET_BLOCKED_APPS = "set_blocked_apps"
SERVICE_SET_NIGHTLIGHT_MODE = "set_nightlight_mode"

SUPPORTED_APPS = [
    "activision_blizzard",
    "alibaba",
    "amazon",
    "amazon_video",
    "apple",
    "apple_itunes",
    "audible",
    "badoo",
    "blizzard",
    "bytedance",
    "cbs",
    "clash_of_clans",
    "clash_royale",
    "costco",
    "craigslist",
    "discord",
    "disney",
    "disney_plus",
    "disqus",
    "ebay",
    "electronic_arts",
    "epic_games",
    "etsy",
    "facebook",
    "facebook_messenger",
    "gmail",
    "google_hangouts",
    "google_voice",
    "hbo",
    "hulu",
    "iheartradio",
    "instagram",
    "kik",
    "last.fm",
    "linkedin",
    "microsoft_outlook",
    "microsoft_teams",
    "minecraft",
    "netflix",
    "nintendo",
    "okcupid",
    "pandora",
    "pinterest",
    "playstation",
    "plex",
    "reddit",
    "roblox",
    "signal",
    "skype",
    "slack",
    "snapchat",
    "soundcloud",
    "spotify",
    "steam",
    "stream",
    "target",
    "ticketmaster",
    "tiktok",
    "tinder",
    "tumblr",
    "twitch",
    "twitter",
    "ubisoft",
    "vimeo",
    "walmart",
    "wechat",
    "whatsapp",
    "xbox",
    "xbox_live",
    "yahoo_mail",
    "youtube",
    "zoom_video",
]

CONF_SAVE_RESPONSES = "save_responses"
CONF_SHOW_EERO_LOGO = "show_eero_logo"
CONF_TIMEOUT = "timeout"

VALUES_SCAN_INTERVAL = [30, 60, 120, 300, 600]
VALUES_TIMEOUT = [10, 15, 30, 45, 60]

DEFAULT_SAVE_LOCATION = f"/config/custom_components/{DOMAIN}/api/responses"
DEFAULT_SAVE_RESPONSES = False
DEFAULT_SCAN_INTERVAL = VALUES_SCAN_INTERVAL[2]
DEFAULT_SHOW_EERO_LOGO = False
DEFAULT_TIMEOUT = VALUES_TIMEOUT[0]
