"""Support for Eero update entities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.update import (
    UpdateDeviceClass,
    UpdateEntity,
    UpdateEntityDescription,
    UpdateEntityFeature,
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
    RELEASE_URL,
)


@dataclass
class EeroUpdateEntityDescription(EeroEntityDescription, UpdateEntityDescription):
    """Class to describe an Eero update entity."""

    entity_category: str[EntityCategory] | None = EntityCategory.CONFIG


UPDATE_DESCRIPTIONS: list[EeroUpdateEntityDescription] = [
    EeroUpdateEntityDescription(
        key="firmware",
        name="Firmware",
        device_class=UpdateDeviceClass.FIRMWARE,
        request_refresh=False,
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up an Eero update entity based on a config entry."""
    entry = hass.data[EERO_DOMAIN][config_entry.entry_id]
    coordinator = entry[DATA_COORDINATOR]
    entities: list[EeroUpdateEntity] = []

    SUPPORTED_KEYS = {
        description.key: description for description in UPDATE_DESCRIPTIONS
    }

    for network in coordinator.data.networks:
        if network.id in entry[CONF_NETWORKS]:
            for eero in network.eeros:
                if eero.id in entry[CONF_RESOURCES][network.id][CONF_EEROS]:
                    for description in SUPPORTED_KEYS.values():
                        if description.premium_type and not network.premium_enabled:
                            continue
                        entities.append(
                            EeroUpdateEntity(
                                coordinator,
                                network.id,
                                eero.id,
                                description,
                                entry[CONF_MISCELLANEOUS][network.id],
                            )
                        )

    async_add_entities(entities)


class EeroUpdateEntity(UpdateEntity, EeroEntity):
    """Representation of an Eero update entity."""

    @property
    def auto_update(self) -> bool:
        """Indicate if the device or service has auto update enabled."""
        return True

    @property
    def installed_version(self) -> str | None:
        """Version installed and in use."""
        if os_version := self.resource.current_firmware.os_version:
            return os_version
        return self.resource.os_version

    @property
    def latest_version(self) -> str | None:
        """Latest version available for install."""
        return self.resource.target_firmware.os_version

    @property
    def release_summary(self) -> str | None:
        """Summary of the release notes or changelog.

        This is not suitable for long changelogs, but merely suitable
        for a short excerpt update description of max 255 characters.
        """
        features = self.resource.target_firmware.features
        if features:
            return str("- " + "\n- ".join(features))
        return None

    def release_notes(self) -> str | None:
        """Return full release notes.

        This is suitable for a long changelog that does not fit in the release_summary property.
        The returned string can contain markdown.
        """
        return self.release_summary

    @property
    def release_url(self) -> str | None:
        """URL to the full release notes of the latest version available."""
        return RELEASE_URL

    @property
    def supported_features(self) -> int:
        """Flag supported features."""
        if self.resource.target_firmware.features:
            return UpdateEntityFeature.INSTALL | UpdateEntityFeature.RELEASE_NOTES
        return UpdateEntityFeature.INSTALL

    @property
    def title(self) -> str | None:
        """Title of the software.

        This helps to differentiate between the device or entity name
        versus the title of the software installed.
        """
        return self.resource.target_firmware.title

    def install(self, version: str | None, backup: bool, **kwargs: Any) -> None:
        """Install an update.

        Version can be specified to install a specific version. When `None`, the
        latest version needs to be installed.

        The backup parameter indicates a backup should be taken before
        installing the update.
        """
        self.network.update()
