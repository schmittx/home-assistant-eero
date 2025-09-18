"""Support for Eero number entities."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.number import NumberEntity, NumberEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
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
class EeroNumberEntityDescription(EeroEntityDescription, NumberEntityDescription):
    """Class to describe an Eero number entity."""

    entity_category: str[EntityCategory] | None = EntityCategory.CONFIG


NUMBER_DESCRIPTIONS: list[EeroNumberEntityDescription] = [
    EeroNumberEntityDescription(
        key="nightlight_brightness_percentage",
        name="Nightlight Brightness",
        native_unit_of_measurement=PERCENTAGE,
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up an Eero number entity based on a config entry."""
    entry = hass.data[EERO_DOMAIN][config_entry.entry_id]
    coordinator = entry[DATA_COORDINATOR]
    entities: list[EeroNumberEntity] = []

    SUPPORTED_KEYS = {
        description.key: description for description in NUMBER_DESCRIPTIONS
    }

    for network in coordinator.data.networks:
        if network.id in entry[CONF_NETWORKS]:
            for eero in network.eeros:
                if eero.id in entry[CONF_RESOURCES][network.id][CONF_EEROS]:
                    for key, description in SUPPORTED_KEYS.items():
                        if description.premium_type and not network.premium_enabled:
                            continue
                        if hasattr(eero, key):
                            entities.append(
                                EeroNumberEntity(
                                    coordinator,
                                    network.id,
                                    eero.id,
                                    description,
                                    entry[CONF_MISCELLANEOUS][network.id],
                                )
                            )

    async_add_entities(entities)


class EeroNumberEntity(NumberEntity, EeroEntity):
    """Representation of an Eero number entity."""

    entity_description: EeroNumberEntityDescription

    @property
    def native_value(self) -> float | None:
        """Return the value reported by the number."""
        return getattr(self.resource, self.entity_description.key)

    def set_native_value(self, value: float) -> None:
        """Set new value."""
        setattr(self.resource, self.entity_description.key, value)

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        await super().async_set_native_value(value)
        if self.entity_description.request_refresh:
            await self.coordinator.async_request_refresh()
