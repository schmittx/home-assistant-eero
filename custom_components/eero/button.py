"""Support for Eero button entities."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.button import (
    ButtonDeviceClass,
    ButtonEntity,
    ButtonEntityDescription,
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
class EeroButtonEntityDescription(EeroEntityDescription, ButtonEntityDescription):
    """Class to describe an Eero button entity."""

    entity_category: str[EntityCategory] | None = EntityCategory.CONFIG


BUTTON_DESCRIPTIONS: list[EeroButtonEntityDescription] = [
    EeroButtonEntityDescription(
        key="reboot",
        name="Reboot",
        device_class=ButtonDeviceClass.RESTART,
        request_refresh=False,
    ),
    EeroButtonEntityDescription(
        key="run_internet_backup_test",
        name="Run Internet Backup Test",
        icon="mdi:web",
        premium_type=True,
        request_refresh=False,
    ),
    EeroButtonEntityDescription(
        key="run_speed_test",
        name="Run Speed Test",
        icon="mdi:speedometer",
        request_refresh=False,
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up an Eero button entity based on a config entry."""
    entry = hass.data[EERO_DOMAIN][config_entry.entry_id]
    coordinator = entry[DATA_COORDINATOR]
    entities: list[EeroButtonEntity] = []

    SUPPORTED_KEYS = {
        description.key: description for description in BUTTON_DESCRIPTIONS
    }

    for network in coordinator.data.networks:
        if network.id in entry[CONF_NETWORKS]:
            for key, description in SUPPORTED_KEYS.items():
                if description.premium_type and not network.premium_enabled:
                    continue
                if hasattr(network, key):
                    entities.append(
                        EeroButtonEntity(
                            coordinator,
                            network.id,
                            None,
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
                                EeroButtonEntity(
                                    coordinator,
                                    network.id,
                                    eero.id,
                                    description,
                                    entry[CONF_MISCELLANEOUS][network.id],
                                )
                            )

    async_add_entities(entities)


class EeroButtonEntity(EeroEntity, ButtonEntity):
    """Representation of an Eero button entity."""

    def press(self) -> None:
        """Press the button."""
        getattr(self.resource, self.entity_description.key)()

    async def async_press(self) -> None:
        """Press the button."""
        await super().async_press()
        if self.entity_description.request_refresh:
            await self.coordinator.async_request_refresh()
