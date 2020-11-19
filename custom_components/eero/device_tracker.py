"""Support for Eero device trackers."""
import logging

from homeassistant.components.device_tracker.config_entry import ScannerEntity
from homeassistant.components.device_tracker.const import SOURCE_TYPE_ROUTER

from . import EeroEntity
from .const import (
    CONF_CLIENTS,
    CONF_NETWORKS,
    DATA_COORDINATOR,
    DOMAIN as EERO_DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up a Eero device tracker based on a config entry."""
    entry = hass.data[EERO_DOMAIN][entry.entry_id]
    conf_networks = entry[CONF_NETWORKS]
    conf_clients = entry[CONF_CLIENTS]
    coordinator = entry[DATA_COORDINATOR]

    def get_device_trackers():
        """Get the Eero device trackers."""
        device_trackers = []

        for network in coordinator.data.networks:
            if network.id in conf_networks:
                for client in network.clients:
                    if client.id in conf_clients:
                        device_trackers.append(EeroDeviceTracker(coordinator, network, client, "device_tracker"))

        return device_trackers

    async_add_entities(await hass.async_add_job(get_device_trackers), True)


class EeroDeviceTracker(ScannerEntity, EeroEntity):
    """Representation of a Eero device tracker."""

    @property
    def name(self):
        """Return the name of the entity."""
        return f"{self.network.name} {self.resource.name_connection_type}"

    @property
    def is_connected(self):
        """Return true if the device tracker is connected."""
        return self.resource.connected

    @property
    def source_type(self):
        """Return the source type, eg gps or router, of the device."""
        return SOURCE_TYPE_ROUTER

    @property
    def device_state_attributes(self):
        attrs = super().device_state_attributes
        if self.is_connected:
            attrs["connected_to"] = self.resource.source_location
            attrs["connection_type"] = self.resource.connection_type
            attrs["ip_address"] = self.resource.ip
        return attrs
