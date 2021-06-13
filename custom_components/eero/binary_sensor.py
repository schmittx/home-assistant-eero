"""Support for Eero binary sensor entities."""
import logging

from homeassistant.components.binary_sensor import BinarySensorEntity

from . import EeroEntity
from .const import (
    CONF_CLIENTS,
    CONF_EEROS,
    CONF_NETWORKS,
    CONF_PROFILES,
    DATA_COORDINATOR,
    DOMAIN as EERO_DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

BASIC_TYPES = {
    "connected": [
        "Connected",
        None,
    ],
    "dns_caching": [
        "Local DNS Caching Enabled",
        None,
    ],
    "guest_connected": [
        "Guest Connected",
        None,
    ],
    "ipv6_upstream": [
        "IPv6 Enabled",
        None,
    ],
    "thread": [
        "Thread Enabled",
        None,
    ],
    "update_available": [
        "Update Available",
        None,
    ],
}

BINARY_SENSOR_TYPES = {**BASIC_TYPES}


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up an Eero binary sensor entity based on a config entry."""
    entry = hass.data[EERO_DOMAIN][entry.entry_id]
    conf_networks = entry[CONF_NETWORKS]
    conf_eeros = entry[CONF_EEROS]
    conf_profiles = entry[CONF_PROFILES]
    conf_clients = entry[CONF_CLIENTS]
    coordinator = entry[DATA_COORDINATOR]

    def get_entities():
        """Get the Eero binary sensor entities."""
        entities = []

        for network in coordinator.data.networks:
            if network.id in conf_networks:
                for variable in BINARY_SENSOR_TYPES:
                    if hasattr(network, variable):
                        entities.append(EeroBinarySensor(coordinator, network, None, variable))

                for eero in network.eeros:
                    if eero.id in conf_eeros:
                        for variable in BINARY_SENSOR_TYPES:
                            if hasattr(eero, variable):
                                entities.append(EeroBinarySensor(coordinator, network, eero, variable))

                for profile in network.profiles:
                    if profile.id in conf_profiles:
                        for variable in BINARY_SENSOR_TYPES:
                            if hasattr(profile, variable):
                                entities.append(EeroBinarySensor(coordinator, network, profile, variable))

                for client in network.clients:
                    if client.id in conf_clients:
                        for variable in BINARY_SENSOR_TYPES:
                            if hasattr(client, variable):
                                entities.append(EeroBinarySensor(coordinator, network, client, variable))

        return entities

    async_add_entities(await hass.async_add_job(get_entities), True)


class EeroBinarySensor(BinarySensorEntity, EeroEntity):
    """Representation of an Eero binary sensor entity."""

    @property
    def name(self):
        """Return the name of the entity."""
        sensor_type = BINARY_SENSOR_TYPES[self.variable][0]
        
        if self.resource.is_client:
            # Since eero is a WiFi router, only add the connection type annotation to the device name
            # for non-wireless devices.
            #
            # FIXME: add backwards compatiblity mode to keep wireless name suffixes
            include_wireless_in_names = False
            if not self.resource.wireless or include_wireless_in_names:
                return f"{self.network.name} {self.resource.name_connection_type} {sensor_type}"
            else:
                return f"{self.network.name} {self.resource.name} {sensor_type}"
        
        
        elif self.resource.is_eero or self.resource.is_profile:
            return f"{self.network.name} {self.resource.name} {sensor_type}"
        
        return f"{self.resource.name} {sensor_type}"

    @property
    def device_class(self):
        """Return the device class of the binary sensor."""
        return BINARY_SENSOR_TYPES[self.variable][1]

    @property
    def is_on(self):
        """Return true if the binary sensor is on."""
        return getattr(self.resource, self.variable)

    @property
    def device_state_attributes(self):
        attrs = super().device_state_attributes
        if self.variable == "update_available":
            if self.resource.is_eero:
                attrs["installed_version"] = self.resource.os_version
            if self.is_on:
                attrs["latest_version"] = self.network.target_firmware
        return attrs
