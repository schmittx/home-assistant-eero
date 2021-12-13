"""Support for Eero binary sensor entities."""
from collections.abc import Mapping
import logging
from typing import Any

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity

from . import EeroEntity
from .const import (
    CONF_CLIENTS,
    CONF_EEROS,
    CONF_NETWORKS,
    CONF_PROFILES,
    DATA_COORDINATOR,
    DOMAIN as EERO_DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

BASIC_TYPES = {
    "connected": [
        "Connected",
        None,
    ],
    "dns_caching": [
        "Local DNS Caching Enabled",
        None,
    ],
    "guest_connected": [
        "Guest Connected",
        None,
    ],
    "ipv6_upstream": [
        "IPv6 Enabled",
        None,
    ],
    "thread": [
        "Thread Enabled",
        None,
    ],
    "update_available": [
        "Update Available",
        None,
    ],
}

PREMIUM_TYPES = {
    "block_apps_enabled": [
        "Block Apps",
        None,
    ],
}

BINARY_SENSOR_TYPES = {**BASIC_TYPES, **PREMIUM_TYPES}


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up an Eero binary sensor entity based on a config entry."""
    entry = hass.data[EERO_DOMAIN][entry.entry_id]
    conf_networks = entry[CONF_NETWORKS]
    conf_eeros = entry[CONF_EEROS]
    conf_profiles = entry[CONF_PROFILES]
    conf_clients = entry[CONF_CLIENTS]
    coordinator = entry[DATA_COORDINATOR]

    def get_entities():
        """Get the Eero binary sensor entities."""
        entities = []

        for network in coordinator.data.networks:
            if network.id in conf_networks:
                for variable in BINARY_SENSOR_TYPES:
                    if hasattr(network, variable):
                        entities.append(EeroBinarySensor(coordinator, network.id, None, variable))

                for eero in network.eeros:
                    if eero.id in conf_eeros:
                        for variable in BINARY_SENSOR_TYPES:
                            if hasattr(eero, variable):
                                entities.append(EeroBinarySensor(coordinator, network.id, eero.id, variable))

                for profile in network.profiles:
                    if profile.id in conf_profiles:
                        for variable in BINARY_SENSOR_TYPES:
                            if hasattr(profile, variable):
                                entities.append(EeroBinarySensor(coordinator, network.id, profile.id, variable))

                for client in network.clients:
                    if client.id in conf_clients:
                        for variable in BINARY_SENSOR_TYPES:
                            if hasattr(client, variable):
                                entities.append(EeroBinarySensor(coordinator, network.id, client.id, variable))

        return entities

    async_add_entities(await hass.async_add_job(get_entities), True)


class EeroBinarySensor(BinarySensorEntity, EeroEntity):
    """Representation of an Eero binary sensor entity."""

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        if self.resource.is_client:
            return f"{self.network.name} {self.resource.name_connection_type} {BINARY_SENSOR_TYPES[self.variable][0]}"
        elif self.resource.is_eero or self.resource.is_profile:
            return f"{self.network.name} {self.resource.name} {BINARY_SENSOR_TYPES[self.variable][0]}"
        return f"{self.resource.name} {BINARY_SENSOR_TYPES[self.variable][0]}"

    @property
    def device_class(self) -> BinarySensorDeviceClass:
        """Return the class of this entity."""
        return BINARY_SENSOR_TYPES[self.variable][1]

    @property
    def is_on(self) -> bool:
        """Return true if the binary sensor is on."""
        return getattr(self.resource, self.variable)

    @property
    def extra_state_attributes(self) -> Mapping[str, Any]:
        """Return entity specific state attributes.

        Implemented by platform classes. Convention for attribute names
        is lowercase snake_case.
        """
        attrs = super().extra_state_attributes
        if self.variable == "block_apps_enabled" and self.is_on:
                attrs["blocked_apps"] = sorted(self.resource.blocked_applications)
        elif self.variable == "update_available":
            if self.resource.is_eero:
                attrs["installed_version"] = self.resource.os_version
            if self.is_on:
                attrs["latest_version"] = self.network.target_firmware
        return attrs
