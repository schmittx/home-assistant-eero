"""The Eero integration."""
from __future__ import annotations

import voluptuous as vol

from .api.client import EeroClient
from .const import (
    CONF_FILTER_EXCLUDE,
    CONF_FILTER_INCLUDE,
    CONF_WIRED_CLIENTS,
    CONF_WIRED_CLIENTS_FILTER,
    CONF_WIRELESS_CLIENTS,
    CONF_WIRELESS_CLIENTS_FILTER,
    ERROR_TIME_FORMAT,
)


def validate_time_format(value) -> str:
    """Validate time format."""
    if isinstance(value, int):
        raise vol.Invalid("Ensure time value is wrapped in quotes.")

    if not isinstance(value, str):
        raise vol.Invalid(ERROR_TIME_FORMAT.format(value))

    if value.startswith("-") or value.startswith("+"):
        raise vol.Invalid(ERROR_TIME_FORMAT.format(value))

    parsed = value.split(":")
    if len(parsed) != 2:
        raise vol.Invalid(ERROR_TIME_FORMAT.format(value))

    try:
        hour, minute = int(parsed[0]), int(parsed[1])
    except ValueError as err:
        raise vol.Invalid(ERROR_TIME_FORMAT.format(value)) from err

    if hour > 23 or minute > 59:
        raise vol.Invalid(ERROR_TIME_FORMAT.format(value))

    if hour < 10:
        hour = f"0{hour}"

    if minute < 10:
        minute = f"0{minute}"

    return f"{hour}:{minute}"


def client_allowed(client: EeroClient, resources: dict) -> bool:
    """Validate client against configuration."""
    return any(
        [
            all(
                [
                    not client.wireless,
                    client.id in resources[CONF_WIRED_CLIENTS],
                    resources[CONF_WIRED_CLIENTS_FILTER] == CONF_FILTER_INCLUDE,
                ]
            ),
            all(
                [
                    not client.wireless,
                    client.id not in resources[CONF_WIRED_CLIENTS],
                    resources[CONF_WIRED_CLIENTS_FILTER] == CONF_FILTER_EXCLUDE,
                ]
            ),
            all(
                [
                    client.wireless,
                    client.id in resources[CONF_WIRELESS_CLIENTS],
                    resources[CONF_WIRELESS_CLIENTS_FILTER] == CONF_FILTER_INCLUDE,
                ]
            ),
            all(
                [
                    client.wireless,
                    client.id not in resources[CONF_WIRELESS_CLIENTS],
                    resources[CONF_WIRELESS_CLIENTS_FILTER] == CONF_FILTER_EXCLUDE,
                ]
            ),
        ]
    )
