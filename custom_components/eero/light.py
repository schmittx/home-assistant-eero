"""Support for Eero light entities."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ColorMode,
    LightEntity,
    LightEntityDescription,
)
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
class EeroLightEntityDescription(EeroEntityDescription, LightEntityDescription):
    """Class to describe an Eero light entity."""

    entity_category: str[EntityCategory] | None = EntityCategory.CONFIG
    color_mode: str[ColorMode] = ColorMode.BRIGHTNESS
    supported_color_modes: set[ColorMode] = field(
        default_factory=lambda: {ColorMode.BRIGHTNESS}
    )


LIGHT_DESCRIPTIONS: list[EeroLightEntityDescription] = [
    EeroLightEntityDescription(
        key="status_light_enabled",
        name="Status Light",
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up an Eero light entity based on a config entry."""
    entry = hass.data[EERO_DOMAIN][config_entry.entry_id]
    coordinator = entry[DATA_COORDINATOR]
    entities: list[EeroLightEntity] = []

    SUPPORTED_KEYS = {
        description.key: description for description in LIGHT_DESCRIPTIONS
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
                                EeroLightEntity(
                                    coordinator,
                                    network.id,
                                    eero.id,
                                    description,
                                    entry[CONF_MISCELLANEOUS][network.id],
                                )
                            )

    async_add_entities(entities)


class EeroLightEntity(EeroEntity, LightEntity):
    """Representation of an Eero light entity."""

    @property
    def is_on(self) -> bool:
        """Return True if entity is on."""
        return bool(getattr(self.resource, self.entity_description.key))

    @property
    def brightness(self) -> int:
        """Return the brightness of this light between 0..255."""
        return int(self.resource.status_light_brightness * 255 / 100)

    @property
    def color_mode(self) -> str:
        """Return the color mode of the light."""
        return self.entity_description.color_mode

    @property
    def supported_color_modes(self) -> set[str]:
        """Flag supported color modes."""
        return self.entity_description.supported_color_modes

    def turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        if ATTR_BRIGHTNESS in kwargs:
            brightness = int(kwargs[ATTR_BRIGHTNESS] * 100 / 255)
            self.resource.set_status_light_brightness(value=brightness)
        else:
            self.resource.set_status_light_on()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        await super().async_turn_on(**kwargs)
        if self.entity_description.request_refresh:
            await self.coordinator.async_request_refresh()

    def turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        self.resource.set_status_light_off()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        await super().async_turn_off(**kwargs)
        if self.entity_description.request_refresh:
            await self.coordinator.async_request_refresh()
