"""Support for Eero camera entities."""
from collections.abc import Mapping
import io
import logging
import pyqrcode
from typing import Any, final

from homeassistant.components.camera import Camera

from . import EeroEntity
from .const import (
    CONF_NETWORKS,
    DATA_COORDINATOR,
    DOMAIN as EERO_DOMAIN,
    EERO_LOGO_ICON,
)

_LOGGER = logging.getLogger(__name__)

CAMERA_TYPES = {
    "guest_network_qr_code": [
        "guest_network_name",
        "guest_network_password",
    ],
    "main_network_qr_code": [
        "name",
        "password",
    ],
}

STATE_DISABLED = "Disabled"
STATE_ENABLED = "Enabled"


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up an Eero camera entity based on a config entry."""
    entry = hass.data[EERO_DOMAIN][entry.entry_id]
    conf_networks = entry[CONF_NETWORKS]
    coordinator = entry[DATA_COORDINATOR]

    def get_entities():
        """Get the Eero camera entities."""
        entities = []

        for network in coordinator.data.networks:
            if network.id in conf_networks:
                for variable in CAMERA_TYPES:
                    entities.append(EeroCamera(coordinator, network.id, None, variable))

        return entities

    async_add_entities(await hass.async_add_job(get_entities), True)


class EeroCamera(EeroEntity, Camera):
    """Representation of an Eero camera entity."""

    def __init__(self, coordinator, network, resource, variable):
        """Initialize device."""
        super().__init__(coordinator, network, resource, variable)
        Camera.__init__(self)

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return getattr(self.resource, CAMERA_TYPES[self.variable][0])

    @final
    @property
    def state(self) -> str:
        """Return the camera state."""
        if all(
            [
                self.variable == "guest_network_qr_code",
                not self.resource.guest_network_enabled,
            ]
        ):
            return STATE_DISABLED
        return STATE_ENABLED

    @property
    def extra_state_attributes(self) -> Mapping[str, Any]:
        """Return entity specific state attributes.

        Implemented by platform classes. Convention for attribute names
        is lowercase snake_case.
        """
        attrs = super().extra_state_attributes
        attrs["ssid"] = getattr(self.resource, CAMERA_TYPES[self.variable][0])
        return attrs

    def camera_image(self, width: int, height: int) -> bytes:
        """Return bytes of camera image."""
        if self.state == STATE_ENABLED:
            return self.qr_code()
        return open(EERO_LOGO_ICON, "rb").read()

    def wifi_code(self):
        ssid = getattr(self.resource, CAMERA_TYPES[self.variable][0])
        password = getattr(self.resource, CAMERA_TYPES[self.variable][1])
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

    def qr_code(self):
        buffer = io.BytesIO()
        qr_code = pyqrcode.create(self.wifi_code())
        qr_code.png(buffer, scale=5, module_color="#000", background="#FFF")
        return buffer.getvalue()
