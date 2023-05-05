"""Support for Eero camera entities."""
from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
import io
import pyqrcode
from typing import Any, final

from homeassistant.components.camera import Camera, CameraEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from . import EeroEntity, EeroEntityDescription
from .api.const import STATE_DISABLED, STATE_ENABLED
from .const import (
    CONF_NETWORKS,
    DATA_COORDINATOR,
    DOMAIN as EERO_DOMAIN,
    EERO_LOGO_ICON,
)


@dataclass
class EeroCameraEntityDescription(EeroEntityDescription, CameraEntityDescription):
    """Class to describe an Eero camera entity."""

    entity_category: str[EntityCategory] | None = EntityCategory.DIAGNOSTIC
    ssid: str | None = None
    password: str | None = None
    state: Callable[[Any], bool] | None = None

CAMERA_DESCRIPTIONS: list[EeroCameraEntityDescription] = [
    EeroCameraEntityDescription(
        key="guest_network_qr_code",
        name="Guest Network QR Code",
        ssid="guest_network_name",
        password="guest_network_password",
        state=lambda resource: STATE_ENABLED if resource.guest_network_enabled else STATE_DISABLED
    ),
    EeroCameraEntityDescription(
        key="main_network_qr_code",
        name="QR Code",
        ssid="name",
        password="password",
        state=lambda resource: STATE_ENABLED,
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up an Eero camera entity based on a config entry."""
    entry = hass.data[EERO_DOMAIN][config_entry.entry_id]
    coordinator = entry[DATA_COORDINATOR]
    entities: list[EeroCameraEntity] = []

    SUPPORTED_KEYS = {
        description.key: description for description in CAMERA_DESCRIPTIONS
    }

    for network in coordinator.data.networks:
        if network.id in entry[CONF_NETWORKS]:
            for key, description in SUPPORTED_KEYS.items():
                if description.premium_type and not network.premium_status_active:
                    continue
                entities.append(
                    EeroCameraEntity(
                        coordinator,
                        network.id,
                        None,
                        description,
                    )
                )

    async_add_entities(entities, True)


class EeroCameraEntity(EeroEntity, Camera):
    """Representation of an Eero camera entity."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        network_id: str,
        resource_id: str,
        description: EeroCameraEntityDescription,
    ) -> None:
        """Initialize device."""
        super().__init__(coordinator, network_id, resource_id, description)
        Camera.__init__(self)

    @final
    @property
    def state(self) -> str | None:
        """Return the camera state."""
        return self.entity_description.state(self.resource)

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        """Return entity specific state attributes.

        Implemented by platform classes. Convention for attribute names
        is lowercase snake_case.
        """
        return {
            "ssid": getattr(self.resource, self.entity_description.ssid),
        }

    def camera_image(self, width: int, height: int) -> bytes:
        """Return bytes of camera image."""
        if self.state == STATE_ENABLED:
            return self.qr_code()
        return open(EERO_LOGO_ICON, "rb").read()

    def wifi_code(self) -> str:
        ssid = getattr(self.resource, self.entity_description.ssid)
        password = getattr(self.resource, self.entity_description.password)
        if password:
            return "WIFI:S:{ssid};H:{hidden};T:{auth_type};P:{password};;".format(
                ssid=ssid,
                hidden="false",
                auth_type="WPA/WPA2",
                password=password,
            )
        return "WIFI:S:{ssid};H:{hidden};T:{auth_type};;".format(
            ssid=ssid,
            hidden="false",
            auth_type="nopass",
        )

    def qr_code(self) -> bytes:
        buffer = io.BytesIO()
        qr_code = pyqrcode.create(self.wifi_code())
        qr_code.png(buffer, scale=5, module_color="#000", background="#FFF")
        return buffer.getvalue()
