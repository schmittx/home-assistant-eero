"""Support for Eero time entities."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import time

from homeassistant.components.time import TimeEntity, TimeEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import EeroEntity, EeroEntityDescription
from .const import (
    CONF_EEROS,
    CONF_MISCELLANEOUS,
    CONF_NETWORKS,
    CONF_RESOURCES,
    DATA_COORDINATOR,
    DOMAIN as EERO_DOMAIN,
)


@dataclass
class EeroTimeEntityDescription(EeroEntityDescription, TimeEntityDescription):
    """Class to describe an Eero time entity."""

    entity_category: str[EntityCategory] | None = EntityCategory.CONFIG


TIME_DESCRIPTIONS: list[EeroTimeEntityDescription] = [
    EeroTimeEntityDescription(
        key="nightlight_schedule_on",
        name="Nightlight On",
    ),
    EeroTimeEntityDescription(
        key="nightlight_schedule_off",
        name="Nightlight Off",
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up an Eero time entity based on a config entry."""
    entry = hass.data[EERO_DOMAIN][config_entry.entry_id]
    coordinator = entry[DATA_COORDINATOR]
    entities: list[EeroTimeEntity] = []

    SUPPORTED_KEYS = {description.key: description for description in TIME_DESCRIPTIONS}

    for network in coordinator.data.networks:
        if network.id in entry[CONF_NETWORKS]:
            for eero in network.eeros:
                if eero.id in entry[CONF_RESOURCES][network.id][CONF_EEROS]:
                    for key, description in SUPPORTED_KEYS.items():
                        if description.premium_type and not network.premium_enabled:
                            continue
                        if hasattr(eero, key):
                            entities.append(
                                EeroTimeEntity(
                                    coordinator,
                                    network.id,
                                    eero.id,
                                    description,
                                    entry[CONF_MISCELLANEOUS][network.id],
                                )
                            )

    async_add_entities(entities)


class EeroTimeEntity(TimeEntity, EeroEntity):
    """Representation of an Eero time entity."""

    entity_description: EeroTimeEntityDescription

    @property
    def native_value(self) -> time | None:
        """Return the value reported by the time."""
        return getattr(self.resource, self.entity_description.key)

    def set_value(self, value: time) -> None:
        """Change the time."""
        setattr(self.resource, self.entity_description.key, value)

    async def async_set_value(self, value: time) -> None:
        """Change the time."""
        await super().async_set_value(value)
        if self.entity_description.request_refresh:
            await self.coordinator.async_request_refresh()
