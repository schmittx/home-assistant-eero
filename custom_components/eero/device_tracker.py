"""Support for Eero device tracker entities."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, final

from homeassistant.components.device_tracker import (
    ATTR_HOST_NAME,
    ATTR_IP,
    ATTR_MAC,
    ATTR_SOURCE_TYPE,
    SourceType,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_MANUFACTURER,
    STATE_HOME,
    STATE_NOT_HOME,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from . import EeroEntity, EeroEntityDescription
from .const import (
    CONF_CLIENTS,
    CONF_NETWORKS,
    CONF_PROFILES,
    DATA_COORDINATOR,
    DOMAIN as EERO_DOMAIN,
)

@dataclass
class EeroDeviceTrackerEntityDescription(EeroEntityDescription):
    """Class to describe an Eero device tracker entity."""

    entity_category: str[EntityCategory] | None = EntityCategory.DIAGNOSTIC
    source_type: str[SourceType] = SourceType.ROUTER

DEVICE_TRACKER_DESCRIPTIONS: list[EeroDeviceTrackerEntityDescription] = [
    EeroDeviceTrackerEntityDescription(
        key="device_tracker",
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up an Eero device tracker entity based on a config entry."""
    entry = hass.data[EERO_DOMAIN][config_entry.entry_id]
    coordinator = entry[DATA_COORDINATOR]
    entities: list[EeroDeviceTrackerEntity] = []

    SUPPORTED_KEYS = {
        description.key: description for description in DEVICE_TRACKER_DESCRIPTIONS
    }

    for network in coordinator.data.networks:
        if network.id in entry[CONF_NETWORKS]:
            for profile in network.profiles:
                if profile.id in entry[CONF_PROFILES]:
                    for key, description in SUPPORTED_KEYS.items():
                        if description.premium_type and not network.premium_enabled:
                            continue
                        entities.append(
                            EeroDeviceTrackerEntity(
                                coordinator,
                                network.id,
                                profile.id,
                                description,
                            )
                        )

            for client in network.clients:
                if client.id in entry[CONF_CLIENTS]:
                    for key, description in SUPPORTED_KEYS.items():
                        if description.premium_type and not network.premium_enabled:
                            continue
                        entities.append(
                            EeroDeviceTrackerEntity(
                                coordinator,
                                network.id,
                                client.id,
                                description,
                            )
                        )

    async_add_entities(entities)


class EeroDeviceTrackerEntity(EeroEntity):
    """Representation of an Eero device tracker entity."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def name(self) -> str | None:
        """Return the name of the entity."""
        if self.resource.is_client:
            return f"{self.network.name} {self.resource.name_connection_type}"
        return f"{self.network.name} {self.resource.name}"

    @property
    def is_connected(self) -> bool | None:
        """Return true if the device is connected to the network."""
        return self.resource.connected

    @property
    def source_type(self) -> SourceType | str:
        """Return the source type, eg gps or router, of the device."""
        return self.entity_description.source_type

    @property
    def ip_address(self) -> str | None:
        """Return the primary ip address of the device."""
        if self.resource.is_client:
            return self.resource.ip
        return None

    @property
    def mac_address(self) -> str | None:
        """Return the mac address of the device."""
        if self.resource.is_client:
            return self.resource.mac
        return None

    @property
    def hostname(self) -> str | None:
        """Return hostname of the device."""
        if self.resource.is_client:
            return self.resource.hostname
        return None

    @property
    def state(self) -> str:
        """Return the state of the device."""
        if self.is_connected:
            return STATE_HOME
        return STATE_NOT_HOME

    @final
    @property
    def state_attributes(self) -> dict[str, StateType]:
        """Return the device state attributes."""
        attr: dict[str, StateType] = {ATTR_SOURCE_TYPE: self.source_type}
        if ip_address := self.ip_address:
            attr[ATTR_IP] = ip_address
        if mac_address := self.mac_address:
            attr[ATTR_MAC] = mac_address
        if hostname := self.hostname:
            attr[ATTR_HOST_NAME] = hostname
        return attr

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        """Return entity specific state attributes.

        Implemented by platform classes. Convention for attribute names
        is lowercase snake_case.
        """
        attrs = {}
        if self.is_connected and self.resource.is_client:
            attrs["connected_to"] = self.resource.source_location
            attrs["connection_type"] = self.resource.connection_type
            if manufacturer := self.resource.manufacturer:
                attrs[ATTR_MANUFACTURER] = manufacturer
            attrs["network_name"] = self.network.name
        return attrs
