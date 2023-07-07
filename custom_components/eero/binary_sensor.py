"""Support for Eero binary sensor entities."""
from __future__ import annotations

from collections.abc import Mapping
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
    CONF_CLIENTS,
    CONF_EEROS,
    CONF_NETWORKS,
    CONF_PROFILES,
    DATA_COORDINATOR,
    DOMAIN as EERO_DOMAIN,
)

@dataclass
class EeroBinarySensorEntityDescription(EeroEntityDescription, BinarySensorEntityDescription):
    """Class to describe an Eero binary sensor entity."""

    entity_category: str[EntityCategory] | None = EntityCategory.DIAGNOSTIC

BINARY_SENSOR_DESCRIPTIONS: list[EeroBinarySensorEntityDescription] = [
    EeroBinarySensorEntityDescription(
        key="block_apps_enabled",
        name="Block Apps",
        extra_attrs={
            "blocked_apps": lambda resource: sorted(getattr(resource, "blocked_applications")),
        },
    ),
    EeroBinarySensorEntityDescription(
        key="connected",
        name="Connected",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
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
                if description.premium_type and not network.premium_status_active:
                    continue
                elif hasattr(network, key):
                    entities.append(
                        EeroBinarySensorEntity(
                            coordinator,
                            network.id,
                            None,
                            description,
                        )
                    )

            for backup_network in network.backup_networks:
                if backup_network.id in entry[CONF_BACKUP_NETWORKS]:
                    for key, description in SUPPORTED_KEYS.items():
                        if hasattr(backup_network, key):
                            entities.append(
                                EeroBinarySensorEntity(
                                    coordinator,
                                    network.id,
                                    backup_network.id,
                                    description,
                                )
                            )

            for eero in network.eeros:
                if eero.id in entry[CONF_EEROS]:
                    for key, description in SUPPORTED_KEYS.items():
                        if description.premium_type and not network.premium_status_active:
                            continue
                        elif hasattr(eero, key):
                            entities.append(
                                EeroBinarySensorEntity(
                                    coordinator,
                                    network.id,
                                    eero.id,
                                    description,
                                )
                            )

            for profile in network.profiles:
                if profile.id in entry[CONF_PROFILES]:
                    for key, description in SUPPORTED_KEYS.items():
                        if description.premium_type and not network.premium_status_active:
                            continue
                        elif hasattr(profile, key):
                            entities.append(
                                EeroBinarySensorEntity(
                                    coordinator,
                                    network.id,
                                    profile.id,
                                    description,
                                )
                            )

            for client in network.clients:
                if client.id in entry[CONF_CLIENTS]:
                    for key, description in SUPPORTED_KEYS.items():
                        if description.premium_type and not network.premium_status_active:
                            continue
                        elif hasattr(client, key):
                            entities.append(
                                EeroBinarySensorEntity(
                                    coordinator,
                                    network.id,
                                    client.id,
                                    description,
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
        if self.entity_description.extra_attrs and self.is_on:
            for key, func in self.entity_description.extra_attrs.items():
                attrs[key] = func(self.resource)
        return attrs
