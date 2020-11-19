"""Support for Eero binary sensors."""
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
    TYPE_BEACON,
    TYPE_CLIENT,
    TYPE_EERO,
    TYPE_NETWORK,
    TYPE_PROFILE,
)

_LOGGER = logging.getLogger(__name__)

BASIC_TYPES = {
    "dns_caching": [[TYPE_NETWORK], "Local DNS Caching Enabled", None],
    "ipv6_upstream": [[TYPE_NETWORK], "IPv6 Enabled", None],
    "dns_caching": [[TYPE_NETWORK], "Local DNS Caching Enabled", None],
    "thread": [[TYPE_NETWORK], "Thread Enabled", None],
    "update_available": [[TYPE_EERO], "Update Available", None],
}

BINARY_SENSOR_TYPES = {**BASIC_TYPES}


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up a Eero sensor based on a config entry."""
    entry = hass.data[EERO_DOMAIN][entry.entry_id]
    conf_networks = entry[CONF_NETWORKS]
    conf_eeros = entry[CONF_EEROS]
    conf_profiles = entry[CONF_PROFILES]
    conf_clients = entry[CONF_CLIENTS]
    coordinator = entry[DATA_COORDINATOR]

    def get_binary_sensors():
        """Get the Eero binary sensors."""
        binary_sensors = []

        for network in coordinator.data.networks:
            if network.id in conf_networks:
                for variable in BINARY_SENSOR_TYPES:
                    if TYPE_NETWORK in BINARY_SENSOR_TYPES[variable][0]:
                        binary_sensors.append(EeroBinarySensor(coordinator, network, None, variable))

                for eero in network.eeros:
                    if eero.id in conf_eeros:
                        for variable in BINARY_SENSOR_TYPES:
                            if TYPE_EERO in BINARY_SENSOR_TYPES[variable][0]:
                                binary_sensors.append(EeroBinarySensor(coordinator, network, eero, variable))
                            if eero.is_beacon and TYPE_BEACON in BINARY_SENSOR_TYPES[variable][0]:
                                binary_sensors.append(EeroBinarySensor(coordinator, network, eero, variable))

                for profile in network.profiles:
                    if profile.id in conf_profiles:
                        for variable in BINARY_SENSOR_TYPES:
                            if TYPE_PROFILE in BINARY_SENSOR_TYPES[variable][0]:
                                binary_sensors.append(EeroBinarySensor(coordinator, network, profile, variable))

                for client in network.clients:
                    if client.id in conf_clients:
                        for variable in BINARY_SENSOR_TYPES:
                            if TYPE_CLIENT in BINARY_SENSOR_TYPES[variable][0]:
                                binary_sensors.append(EeroBinarySensor(coordinator, network, client, variable))

        return binary_sensors

    async_add_entities(await hass.async_add_job(get_binary_sensors), True)


class EeroBinarySensor(BinarySensorEntity, EeroEntity):
    """Representation of a Eero sensor."""

    @property
    def name(self):
        """Return the name of the entity."""
        if self.resource.is_client:
            return f"{self.network.name} {self.resource.name_connection_type} {BINARY_SENSOR_TYPES[self.variable][1]}"
        elif self.resource.is_eero or self.resource.is_profile:
            return f"{self.network.name} {self.resource.name} {BINARY_SENSOR_TYPES[self.variable][1]}"
        return f"{self.resource.name} {BINARY_SENSOR_TYPES[self.variable][1]}"

    @property
    def device_class(self):
        """Return the device class of the sensor."""
        return BINARY_SENSOR_TYPES[self.variable][2]

    @property
    def is_on(self):
        """Return true if the binary sensor is on."""
        return getattr(self.resource, self.variable)

    @property
    def device_state_attributes(self):
        attrs = super().device_state_attributes
        if self.variable == "update_available":
            attrs["installed_version"] = self.resource.os_version
            if self.is_on:
                attrs["latest_version"] = self.network.target_firmware
        return attrs
