"""The Eero integration."""

from __future__ import annotations

from .api.client import EeroClient
from .const import (
    CONF_FILTER_EXCLUDE,
    CONF_FILTER_INCLUDE,
    CONF_WIRED_CLIENTS,
    CONF_WIRED_CLIENTS_FILTER,
    CONF_WIRELESS_CLIENTS,
    CONF_WIRELESS_CLIENTS_FILTER,
)


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
