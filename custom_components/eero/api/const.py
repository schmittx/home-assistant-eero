"""Eero API"""
ACTIVITY_ADBLOCK_DAY = "adblock_day"
ACTIVITY_ADBLOCK_WEEK = "adblock_week"
ACTIVITY_ADBLOCK_MONTH = "adblock_month"

ACTIVITY_BLOCKED_DAY = "blocked_day"
ACTIVITY_BLOCKED_WEEK = "blocked_week"
ACTIVITY_BLOCKED_MONTH = "blocked_month"

ACTIVITY_DATA_USAGE_DAY = "data_usage_day"
ACTIVITY_DATA_USAGE_WEEK = "data_usage_week"
ACTIVITY_DATA_USAGE_MONTH = "data_usage_month"

ACTIVITY_INSPECTED_DAY = "inspected_day"
ACTIVITY_INSPECTED_WEEK = "inspected_week"
ACTIVITY_INSPECTED_MONTH = "inspected_month"

API_ENDPOINT = "https://api-user.e2ro.com"

CADENCE_DAILY = "daily"
CADENCE_HOURLY = "hourly"

DEVICE_CATEGORY_COMPUTERS_PERSONAL = "computers_personal"
DEVICE_CATEGORY_ENTERTAINMENT = "entertainment"
DEVICE_CATEGORY_HOME = "home"
DEVICE_CATEGORY_OTHER = "other"

DEVICE_TYPE_AIR_CONDITIONER = "air_conditioner"
DEVICE_TYPE_AIR_PURIFIER = "air_purifier"
DEVICE_TYPE_ALARM_SYSTEM = "alarm_system"
DEVICE_TYPE_AUDIO = "audio"
DEVICE_TYPE_BED = "bed"
DEVICE_TYPE_CABLE_BOX = "cable_box",
DEVICE_TYPE_CAR = "car"
DEVICE_TYPE_COFFEE_MAKER = "coffee_maker"
DEVICE_TYPE_DESKTOP_COMPUTER = "desktop_computer"
DEVICE_TYPE_DIGITAL_ASSISTANT = "digital_assistant"
DEVICE_TYPE_DOOR_BELL = "door_bell"
DEVICE_TYPE_DOOR_LOCK = "door_lock"
DEVICE_TYPE_E_READER = "e_reader"
DEVICE_TYPE_EXERCISE_BIKE = "exercise_bike"
DEVICE_TYPE_FAN = "fan"
DEVICE_TYPE_GAME_CONSOLE = "game_console"
DEVICE_TYPE_GARAGE_DOOR = "garage_door"
DEVICE_TYPE_GENERIC = "generic"
DEVICE_TYPE_HARD_DRIVE = "hard_drive"
DEVICE_TYPE_HUB = "hub"
DEVICE_TYPE_LAPTOP_COMPUTER = "laptop_computer"
DEVICE_TYPE_LIGHT = "light"
DEVICE_TYPE_MEDIA_STREAMER = "media_streamer"
DEVICE_TYPE_NETWORK_EQUIPMENT = "network_equipment"
DEVICE_TYPE_OVEN = "oven"
DEVICE_TYPE_PET_DEVICE = "pet_device"
DEVICE_TYPE_PHONE = "phone"
DEVICE_TYPE_PLUG = "plug"
DEVICE_TYPE_PRINTER = "printer"
DEVICE_TYPE_REFRIGERATOR = "refrigerator"
DEVICE_TYPE_REMOTE = "remote",
DEVICE_TYPE_SCALE = "scale"
DEVICE_TYPE_SECURITY_CAMERA = "security_camera"
DEVICE_TYPE_SMOKE_DETECTOR = "smoke_detector"
DEVICE_TYPE_SPRINKLER = "sprinkler"
DEVICE_TYPE_TABLET = "tablet"
DEVICE_TYPE_TELEVISION = "television"
DEVICE_TYPE_THERMOSTAT = "thermostat"
DEVICE_TYPE_TOASTER = "toaster"
DEVICE_TYPE_VACUUM = "vacuum"
DEVICE_TYPE_WASHER_DRYER = "washer_dryer"
DEVICE_TYPE_WATCH = "watch"

DEVICE_CATEGORY_TYPE_MAP = {
    DEVICE_TYPE_DESKTOP_COMPUTER: DEVICE_CATEGORY_COMPUTERS_PERSONAL,
    DEVICE_TYPE_E_READER: DEVICE_CATEGORY_COMPUTERS_PERSONAL,
    DEVICE_TYPE_HARD_DRIVE: DEVICE_CATEGORY_COMPUTERS_PERSONAL,
    DEVICE_TYPE_LAPTOP_COMPUTER: DEVICE_CATEGORY_COMPUTERS_PERSONAL,
    DEVICE_TYPE_PHONE: DEVICE_CATEGORY_COMPUTERS_PERSONAL,
    DEVICE_TYPE_PRINTER: DEVICE_CATEGORY_COMPUTERS_PERSONAL,
    DEVICE_TYPE_TABLET: DEVICE_CATEGORY_COMPUTERS_PERSONAL,
    DEVICE_TYPE_WATCH: DEVICE_CATEGORY_COMPUTERS_PERSONAL,
    DEVICE_TYPE_AUDIO: DEVICE_CATEGORY_ENTERTAINMENT,
    DEVICE_TYPE_CABLE_BOX: DEVICE_CATEGORY_ENTERTAINMENT,
    DEVICE_TYPE_GAME_CONSOLE: DEVICE_CATEGORY_ENTERTAINMENT,
    DEVICE_TYPE_MEDIA_STREAMER: DEVICE_CATEGORY_ENTERTAINMENT,
    DEVICE_TYPE_REMOTE: DEVICE_CATEGORY_ENTERTAINMENT,
    DEVICE_TYPE_TELEVISION: DEVICE_CATEGORY_ENTERTAINMENT,
    DEVICE_TYPE_AIR_CONDITIONER: DEVICE_CATEGORY_HOME,
    DEVICE_TYPE_AIR_PURIFIER: DEVICE_CATEGORY_HOME,
    DEVICE_TYPE_ALARM_SYSTEM: DEVICE_CATEGORY_HOME,
    DEVICE_TYPE_BED: DEVICE_CATEGORY_HOME,
    DEVICE_TYPE_CAR: DEVICE_CATEGORY_HOME,
    DEVICE_TYPE_COFFEE_MAKER: DEVICE_CATEGORY_HOME,
    DEVICE_TYPE_DIGITAL_ASSISTANT: DEVICE_CATEGORY_HOME,
    DEVICE_TYPE_DOOR_BELL: DEVICE_CATEGORY_HOME,
    DEVICE_TYPE_DOOR_LOCK: DEVICE_CATEGORY_HOME,
    DEVICE_TYPE_EXERCISE_BIKE: DEVICE_CATEGORY_HOME,
    DEVICE_TYPE_FAN: DEVICE_CATEGORY_HOME,
    DEVICE_TYPE_GARAGE_DOOR: DEVICE_CATEGORY_HOME,
    DEVICE_TYPE_HUB: DEVICE_CATEGORY_HOME,
    DEVICE_TYPE_LIGHT: DEVICE_CATEGORY_HOME,
    DEVICE_TYPE_OVEN: DEVICE_CATEGORY_HOME,
    DEVICE_TYPE_PET_DEVICE: DEVICE_CATEGORY_HOME,
    DEVICE_TYPE_PLUG: DEVICE_CATEGORY_HOME,
    DEVICE_TYPE_REFRIGERATOR: DEVICE_CATEGORY_HOME,
    DEVICE_TYPE_SCALE: DEVICE_CATEGORY_HOME,
    DEVICE_TYPE_SECURITY_CAMERA: DEVICE_CATEGORY_HOME,
    DEVICE_TYPE_SMOKE_DETECTOR: DEVICE_CATEGORY_HOME,
    DEVICE_TYPE_SPRINKLER: DEVICE_CATEGORY_HOME,
    DEVICE_TYPE_THERMOSTAT: DEVICE_CATEGORY_HOME,
    DEVICE_TYPE_TOASTER: DEVICE_CATEGORY_HOME,
    DEVICE_TYPE_VACUUM: DEVICE_CATEGORY_HOME,
    DEVICE_TYPE_WASHER_DRYER: DEVICE_CATEGORY_HOME,
    DEVICE_TYPE_NETWORK_EQUIPMENT: DEVICE_CATEGORY_OTHER,
    DEVICE_TYPE_GENERIC: DEVICE_CATEGORY_OTHER,
}

INSIGHT_TYPE_ADBLOCK = "adblock"
INSIGHT_TYPE_BLOCKED = "blocked"
INSIGHT_TYPE_INSPECTED = "inspected"

MODEL_BEACON = "eero Beacon"

PERIOD_DAY = "day"
PERIOD_MONTH = "month"
PERIOD_WEEK = "week"

RESOURCE_MAP = dict(clients="devices")

STATE_ACTIVE = "active"
STATE_AMBIENT = "ambient"
STATE_DISABLED = "disabled"
STATE_ENABLED = "enabled"
STATE_NETWORK = "network"
STATE_PROFILE = "profile"
STATE_SCHEDULE = "schedule"

URL_ACCOUNT = "/2.2/account"


ACTIVITY_MAP = {
    ACTIVITY_ADBLOCK_DAY: [
        "{}/insights",
        INSIGHT_TYPE_ADBLOCK,
        PERIOD_DAY,
    ],
    ACTIVITY_ADBLOCK_MONTH: [
        "{}/insights",
        INSIGHT_TYPE_ADBLOCK,
        PERIOD_MONTH,
    ],
    ACTIVITY_ADBLOCK_WEEK: [
        "{}/insights",
        INSIGHT_TYPE_ADBLOCK,
        PERIOD_WEEK,
    ],
    ACTIVITY_BLOCKED_DAY: [
        "{}/insights",
        INSIGHT_TYPE_BLOCKED,
        PERIOD_DAY,
    ],
    ACTIVITY_BLOCKED_MONTH: [
        "{}/insights",
        INSIGHT_TYPE_BLOCKED,
        PERIOD_MONTH,
    ],
    ACTIVITY_BLOCKED_WEEK: [
        "{}/insights",
        INSIGHT_TYPE_BLOCKED,
        PERIOD_WEEK,
    ],
    ACTIVITY_DATA_USAGE_DAY: [
        "{}/data_usage",
        None,
        PERIOD_DAY,
    ],
    ACTIVITY_DATA_USAGE_MONTH: [
        "{}/data_usage",
        None,
        PERIOD_MONTH,
    ],
    ACTIVITY_DATA_USAGE_WEEK: [
        "{}/data_usage",
        None,
        PERIOD_WEEK,
    ],
    ACTIVITY_INSPECTED_DAY: [
        "{}/insights",
        INSIGHT_TYPE_INSPECTED,
        PERIOD_DAY,
    ],
    ACTIVITY_INSPECTED_MONTH: [
        "{}/insights",
        INSIGHT_TYPE_INSPECTED,
        PERIOD_MONTH,
    ],
    ACTIVITY_INSPECTED_WEEK: [
        "{}/insights",
        INSIGHT_TYPE_INSPECTED,
        PERIOD_WEEK,
    ],
}

PREFERRED_UPDATE_HOUR_MAP = {
    "12am_1am": 0,
    "1am_2am": 1,
    "2am_3am": 2,
    "3am_4am": 3,
    "4am_5am": 4,
    "5am_6am": 5,
    "6am_7am": 6,
    "7am_8am": 7,
    "8am_9am": 8,
    "9am_10am": 9,
    "10am_11am": 10,
    "11am_12pm": 11,
    "12pm_1pm": 12,
    "1pm_2pm": 13,
    "2pm_3pm": 14,
    "3pm_4pm": 15,
    "4pm_5pm": 16,
    "5pm_6pm": 17,
    "6pm_7pm": 18,
    "7pm_8pm": 19,
    "8pm_9pm": 20,
    "9pm_10pm": 21,
    "10pm_11pm": 22,
    "11pm_12am": 23,
}
