"""Support for Eero image entities."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.components.image import ImageEntity, ImageEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from . import EeroEntity, EeroEntityDescription
from .const import (
    CONF_BACKUP_NETWORKS,
    CONF_MISCELLANEOUS,
    CONF_NETWORKS,
    CONF_RESOURCES,
    DATA_COORDINATOR,
    DOMAIN as EERO_DOMAIN,
)


@dataclass
class EeroImageEntityDescription(EeroEntityDescription, ImageEntityDescription):
    """Class to describe an Eero image entity."""

    entity_category: str[EntityCategory] | None = EntityCategory.DIAGNOSTIC
    ssid: str | None = None
    password: str | None = None
    state: Callable[[Any], bool] | None = None


IMAGE_DESCRIPTIONS: list[EeroImageEntityDescription] = [
    EeroImageEntityDescription(
        key="guest_network_qr_code",
        name="Guest Network QR Code",
    ),
    EeroImageEntityDescription(
        key="qr_code",
        name="QR Code",
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up an Eero image entity based on a config entry."""
    entry = hass.data[EERO_DOMAIN][config_entry.entry_id]
    coordinator = entry[DATA_COORDINATOR]
    entities: list[EeroImageEntity] = []

    SUPPORTED_KEYS = {
        description.key: description for description in IMAGE_DESCRIPTIONS
    }

    for network in coordinator.data.networks:
        if network.id in entry[CONF_NETWORKS]:
            for key, description in SUPPORTED_KEYS.items():
                if hasattr(network, key):
                    entities.append(
                        EeroImageEntity(
                            coordinator,
                            network.id,
                            None,
                            description,
                            entry[CONF_MISCELLANEOUS][network.id],
                            hass,
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
                                EeroImageEntity(
                                    coordinator,
                                    network.id,
                                    backup_network.id,
                                    description,
                                    entry[CONF_MISCELLANEOUS][network.id],
                                    hass,
                                )
                            )

    async_add_entities(entities)


class EeroImageEntity(EeroEntity, ImageEntity):
    """Representation of an Eero image entity."""

    _attr_content_type = "image/png"

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        network_id: str,
        resource_id: str,
        description: EeroImageEntityDescription,
        miscellaneous: dict[str, Any],
        hass: HomeAssistant,
    ) -> None:
        """Initialize device."""
        super().__init__(
            coordinator,
            network_id,
            resource_id,
            description,
            miscellaneous,
        )
        ImageEntity.__init__(self, hass)
        self._current_image: bytes | None = None

    @property
    def image_last_updated(self) -> datetime | None:
        """The time when the image was last updated."""
        if self._current_image != getattr(self.resource, self.entity_description.key):
            self._attr_image_last_updated = dt_util.utcnow()
        return self._attr_image_last_updated

    async def async_added_to_hass(self) -> None:
        """Fetch and set initial data and state."""
        await super().async_added_to_hass()
        await self.resource.api.generate_default_qr_code()
        self._current_image = getattr(self.resource, self.entity_description.key)
        self._attr_image_last_updated = dt_util.utcnow()

    def image(self) -> bytes | None:
        """Return bytes of image."""
        self._current_image = getattr(self.resource, self.entity_description.key)
        return self._current_image
