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

INSIGHT_TYPE_ADBLOCK = "adblock"
INSIGHT_TYPE_BLOCKED = "blocked"
INSIGHT_TYPE_INSPECTED = "inspected"

MODEL_BEACON = "eero Beacon"

PERIOD_DAY = "day"
PERIOD_MONTH = "month"
PERIOD_WEEK = "week"

RESOURCE_MAP = dict(clients="devices")

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
