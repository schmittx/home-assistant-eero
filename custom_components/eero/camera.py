"""Support for Eero camera entities."""
import io
import logging
import png
import pyqrcode

from homeassistant.components.camera import Camera

from . import EeroEntity
from .const import (
    CONF_NETWORKS,
    DATA_COORDINATOR,
    DOMAIN as EERO_DOMAIN,
    EERO_LOGO_ICON,
)

_LOGGER = logging.getLogger(__name__)


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
                entities.append(EeroCamera(coordinator, network, None, None))

        return entities

    async_add_entities(await hass.async_add_job(get_entities), True)


class EeroCamera(EeroEntity, Camera):
    """Representation of an Eero camera entity."""

    def __init__(self, coordinator, network, resource, variable):
        """Initialize device."""
        super().__init__(coordinator, network, resource, variable)
        Camera.__init__(self)

    @property
    def name(self):
        """Return the name of the entity."""
        return f"{self.resource.name} Guest Network"

    @property
    def state(self):
        """Return the camera state."""
        if self.guest_network_enabled:
            return "Enabled"
        return "Disabled"

    @property
    def device_state_attributes(self):
        attrs = super().device_state_attributes
        if self.guest_network_enabled:
            attrs["guest_network_name"] = self.resource.guest_network_name
        return attrs

    def camera_image(self):
        """Process the image."""
        if self.guest_network_enabled:
            return self.qr_code()
        return open(EERO_LOGO_ICON, "rb").read()

    @property
    def guest_network_enabled(self):
        return getattr(self.resource, "guest_network_enabled")

    def wifi_code(self):
        password = self.resource.guest_network_password
        if password:
            return "WIFI:S:{ssid};H:{hidden};T:{auth_type};P:{password};;".format(
                ssid=self.resource.guest_network_name,
                hidden="false",
                auth_type="WPA/WPA2",
                password=password,
            )
        return "WIFI:S:{ssid};H:{hidden};T:{auth_type};;".format(
            ssid=self.resource.guest_network_name,
            hidden="false",
            auth_type="nopass",
        )

    def qr_code(self):
        buffer = io.BytesIO()
        qr_code = pyqrcode.create(self.wifi_code())
        qr_code.png(buffer, scale=5, module_color="#000", background="#FFF")
        return buffer.getvalue()
