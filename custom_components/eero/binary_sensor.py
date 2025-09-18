"""Support for Eero binary sensor entities."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import EeroEntity, EeroEntityDescription
from .const import (
    CONF_BACKUP_NETWORKS,
    CONF_EEROS,
    CONF_MISCELLANEOUS,
    CONF_NETWORKS,
    CONF_PROFILES,
    CONF_RESOURCES,
    DATA_COORDINATOR,
    DOMAIN as EERO_DOMAIN,
)
from .util import client_allowed


@dataclass
class EeroBinarySensorEntityDescription(
    EeroEntityDescription, BinarySensorEntityDescription
):
    """Class to describe an Eero binary sensor entity."""

    entity_category: str[EntityCategory] | None = EntityCategory.DIAGNOSTIC
    extra_attrs_wireless_only: dict[str, Callable] | None = None


BINARY_SENSOR_DESCRIPTIONS: list[EeroBinarySensorEntityDescription] = [
    EeroBinarySensorEntityDescription(
        key="block_apps_enabled",
        name="Block Apps",
        extra_attrs={
            "blocked_apps": lambda resource: sorted(resource.blocked_applications),
        },
    ),
    EeroBinarySensorEntityDescription(
        key="connected",
        name="Connected",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        extra_attrs_wireless_only={
            "bandwidth_receive": lambda resource: resource.channel_width_rx,
            "bandwidth_transmit": lambda resource: resource.channel_width_tx,
            "channel": lambda resource: resource.channel,
            "operating_band": lambda resource: f"{resource.interface_frequency[0]} {resource.interface_frequency[1]}",
        },
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up an Eero binary sensor entity based on a config entry."""
    entry = hass.data[EERO_DOMAIN][config_entry.entry_id]
    coordinator = entry[DATA_COORDINATOR]
    entities: list[EeroBinarySensorEntity] = []

    SUPPORTED_KEYS = {
        description.key: description for description in BINARY_SENSOR_DESCRIPTIONS
    }

    for network in coordinator.data.networks:
        if network.id in entry[CONF_NETWORKS]:
            for key, description in SUPPORTED_KEYS.items():
                if description.premium_type and not network.premium_enabled:
                    continue
                if hasattr(network, key):
                    entities.append(
                        EeroBinarySensorEntity(
                            coordinator,
                            network.id,
                            None,
                            description,
                            entry[CONF_MISCELLANEOUS][network.id],
                        )
                    )

            for backup_network in network.backup_networks:
                if (
                    backup_network.id
                    in entry[CONF_RESOURCES][network.id][CONF_BACKUP_NETWORKS]
                ):
                    for key, description in SUPPORTED_KEYS.items():
                        if hasattr(backup_network, key):
                            entities.append(
                                EeroBinarySensorEntity(
                                    coordinator,
                                    network.id,
                                    backup_network.id,
                                    description,
                                    entry[CONF_MISCELLANEOUS][network.id],
                                )
                            )

            for eero in network.eeros:
                if eero.id in entry[CONF_RESOURCES][network.id][CONF_EEROS]:
                    for key, description in SUPPORTED_KEYS.items():
                        if description.premium_type and not network.premium_enabled:
                            continue
                        if hasattr(eero, key):
                            entities.append(
                                EeroBinarySensorEntity(
                                    coordinator,
                                    network.id,
                                    eero.id,
                                    description,
                                    entry[CONF_MISCELLANEOUS][network.id],
                                )
                            )

            for profile in network.profiles:
                if profile.id in entry[CONF_RESOURCES][network.id][CONF_PROFILES]:
                    for key, description in SUPPORTED_KEYS.items():
                        if description.premium_type and not network.premium_enabled:
                            continue
                        if hasattr(profile, key):
                            entities.append(
                                EeroBinarySensorEntity(
                                    coordinator,
                                    network.id,
                                    profile.id,
                                    description,
                                    entry[CONF_MISCELLANEOUS][network.id],
                                )
                            )

            for client in network.clients:
                if client_allowed(client, entry[CONF_RESOURCES][network.id]):
                    for key, description in SUPPORTED_KEYS.items():
                        if description.premium_type and not network.premium_enabled:
                            continue
                        if hasattr(client, key):
                            entities.append(
                                EeroBinarySensorEntity(
                                    coordinator,
                                    network.id,
                                    client.id,
                                    description,
                                    entry[CONF_MISCELLANEOUS][network.id],
                                )
                            )

    async_add_entities(entities)


class EeroBinarySensorEntity(EeroEntity, BinarySensorEntity):
    """Representation of an Eero binary sensor entity."""

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        return getattr(self.resource, self.entity_description.key)

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        """Return entity specific state attributes.

        Implemented by platform classes. Convention for attribute names
        is lowercase snake_case.
        """
        attrs = {}
        if self.is_on:
            if self.entity_description.extra_attrs:
                for key, func in self.entity_description.extra_attrs.items():
                    attrs[key] = func(self.resource)
            if (
                self.entity_description.extra_attrs_wireless_only
                and self.resource.is_client
                and self.resource.wireless
            ):
                for (
                    key,
                    func,
                ) in self.entity_description.extra_attrs_wireless_only.items():
                    attrs[key] = func(self.resource)
        return attrs
