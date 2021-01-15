"""Support for Eero sensor entities."""
import logging

from homeassistant.const import PERCENTAGE

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
    "connected_clients_count": [
        "Connected Clients",
        None,
        "clients",
    ],
    "connected_guest_clients_count": [
        "Connected Guest Clients",
        None,
        "clients",
    ],
    "nightlight_brightness_percentage": [
        "Nightlight Brightness",
        None,
        PERCENTAGE,
    ],
    "ssid": [
        "SSID",
        None,
        None,
    ],
    "nightlight_status": [
        "Nightlight Status",
        None,
        None,
    ],
    "public_ip": [
        "Public IP",
        None,
        None,
    ],
    "speed_down": [
        "Download Speed",
        None,
        None,
    ],
    "speed_up": [
        "Upload Speed",
        None,
        None,
    ],
    "status": [
        "Status",
        None,
        None,
    ],
}

SENSOR_TYPES = {**BASIC_TYPES}


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up an Eero sensor entity based on a config entry."""
    entry = hass.data[EERO_DOMAIN][entry.entry_id]
    conf_networks = entry[CONF_NETWORKS]
    conf_eeros = entry[CONF_EEROS]
    conf_profiles = entry[CONF_PROFILES]
    conf_clients = entry[CONF_CLIENTS]
    coordinator = entry[DATA_COORDINATOR]

    def get_entities():
        """Get the Eero sensor entities."""
        entities = []

        for network in coordinator.data.networks:
            if network.id in conf_networks:
                for variable in SENSOR_TYPES:
                    if hasattr(network, variable):
                        entities.append(EeroSensor(coordinator, network, None, variable))

                for eero in network.eeros:
                    if eero.id in conf_eeros:
                        for variable in SENSOR_TYPES:
                            if hasattr(eero, variable):
                                entities.append(EeroSensor(coordinator, network, eero, variable))

                for profile in network.profiles:
                    if profile.id in conf_profiles:
                        for variable in SENSOR_TYPES:
                            if hasattr(profile, variable):
                                entities.append(EeroSensor(coordinator, network, profile, variable))

                for client in network.clients:
                    if client.id in conf_clients:
                        for variable in SENSOR_TYPES:
                            if hasattr(client, variable):
                                entities.append(EeroSensor(coordinator, network, client, variable))

        return entities

    async_add_entities(await hass.async_add_job(get_entities), True)


class EeroSensor(EeroEntity):
    """Representation of an Eero sensor entity."""

    @property
    def name(self):
        """Return the name of the entity."""
        if self.resource.is_client:
            return f"{self.network.name} {self.resource.name_connection_type} {SENSOR_TYPES[self.variable][0]}"
        elif self.resource.is_eero or self.resource.is_profile:
            return f"{self.network.name} {self.resource.name} {SENSOR_TYPES[self.variable][0]}"
        return f"{self.resource.name} {SENSOR_TYPES[self.variable][0]}"

    @property
    def device_class(self):
        """Return the device class of the sensor."""
        return SENSOR_TYPES[self.variable][1]

    @property
    def state(self):
        """Return the state of the sensor."""
        state = getattr(self.resource, self.variable)
        if self.variable in ["speed_down", "speed_up"]:
            return round(state)
        return state

    @property
    def unit_of_measurement(self):
        """Return the unit the value is expressed in."""
        if self.variable in ["speed_down", "speed_up"]:
            return getattr(self.resource, f"{self.variable}_units")
        return SENSOR_TYPES[self.variable][2]

    @property
    def device_state_attributes(self):
        attrs = super().device_state_attributes
        if self.variable == "nightlight_status":
            if self.resource.nightlight_schedule_enabled:
                schedule = self.resource.nightlight_schedule
                attrs["on"] = schedule[0]
                attrs["off"] = schedule[1]
        elif self.variable in ["speed_down", "speed_up"]:
            attrs["last_updated"] = self.resource.speed_date
        elif self.variable == "ssid":
            attrs["id"] = self.resource.id
            attrs["isp"] = self.resource.isp
            attrs["city"] = self.resource.city
            attrs["region"] = self.resource.region_name
            attrs["postal_code"] = self.resource.postal_code
            attrs["country"] = self.resource.country_name
        elif self.variable == "status" and self.resource.is_network:
            for attr in ["health_eero_network_status", "health_internet_isp_up", "health_internet_status"]:
                attrs[attr] = getattr(self.resource, attr)
        return attrs
