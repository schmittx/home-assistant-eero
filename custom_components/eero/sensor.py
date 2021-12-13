"""Support for Eero sensor entities."""
from collections.abc import Mapping
import logging
from typing import Any, final

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.const import PERCENTAGE
from homeassistant.helpers.typing import StateType

from . import EeroEntity
from .const import (
    CONF_ACTIVITY,
    CONF_ACTIVITY_CLIENTS,
    CONF_ACTIVITY_EEROS,
    CONF_ACTIVITY_NETWORK,
    CONF_ACTIVITY_PROFILES,
    CONF_CLIENTS,
    CONF_EEROS,
    CONF_NETWORKS,
    CONF_PROFILES,
    DATA_COORDINATOR,
    DOMAIN as EERO_DOMAIN,
)
from .util import format_data_usage

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

PREMIUM_TYPES = {
    "ad_block_status": [
        "Ad Blocking Status",
        None,
        None,
    ],
}

PREMIUM_ACTIVITY_TYPES = {
    "adblock_day": [
        "Ad Blocks Day",
        None,
        "ads",
    ],
    "adblock_month": [
        "Ad Blocks Month",
        None,
        "ads",
    ],
    "adblock_week": [
        "Ad Blocks Week",
        None,
        "ads",
    ],
    "blocked_day": [
        "Threat Blocks Day",
        None,
        "threats",
    ],
    "blocked_month": [
        "Threat Blocks Month",
        None,
        "threats",
    ],
    "blocked_week": [
        "Threat Blocks Week",
        None,
        "threats",
    ],
    "data_usage_day": [
        "Data Usage Day",
        None,
        None,
    ],
    "data_usage_month": [
        "Data Usage Month",
        None,
        None,
    ],
    "data_usage_week": [
        "Data Usage Week",
        None,
        None,
    ],
    "inspected_day": [
        "Scans Day",
        None,
        "scans",
    ],
    "inspected_month": [
        "Scans Month",
        None,
        "scans",
    ],
    "inspected_week": [
        "Scans Week",
        None,
        "scans",
    ],
}

SENSOR_TYPES = {**BASIC_TYPES, **PREMIUM_TYPES, **PREMIUM_ACTIVITY_TYPES}


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up an Eero sensor entity based on a config entry."""
    entry = hass.data[EERO_DOMAIN][entry.entry_id]
    conf_networks = entry[CONF_NETWORKS]
    conf_eeros = entry[CONF_EEROS]
    conf_profiles = entry[CONF_PROFILES]
    conf_clients = entry[CONF_CLIENTS]
    conf_activity = entry[CONF_ACTIVITY]
    coordinator = entry[DATA_COORDINATOR]

    def get_entities():
        """Get the Eero sensor entities."""
        entities = []

        for network in coordinator.data.networks:
            if network.id in conf_networks:
                activity = conf_activity.get(network.id, {})
                for variable in SENSOR_TYPES:
                    if variable in PREMIUM_TYPES and not network.premium_status_active:
                        continue
                    elif variable in PREMIUM_ACTIVITY_TYPES and not network.premium_status_active:
                        continue
                    elif variable in PREMIUM_ACTIVITY_TYPES and variable not in activity.get(CONF_ACTIVITY_NETWORK, []):
                        continue
                    elif hasattr(network, variable):
                        entities.append(EeroSensor(coordinator, network.id, None, variable))

                for eero in network.eeros:
                    if eero.id in conf_eeros:
                        for variable in SENSOR_TYPES:
                            if variable in PREMIUM_TYPES and not network.premium_status_active:
                                continue
                            elif variable in PREMIUM_ACTIVITY_TYPES and not network.premium_status_active:
                                continue
                            elif variable in PREMIUM_ACTIVITY_TYPES and variable not in activity.get(CONF_ACTIVITY_EEROS, []):
                                continue
                            elif hasattr(eero, variable):
                                entities.append(EeroSensor(coordinator, network.id, eero.id, variable))

                for profile in network.profiles:
                    if profile.id in conf_profiles:
                        for variable in SENSOR_TYPES:
                            if variable in PREMIUM_TYPES and not network.premium_status_active:
                                continue
                            elif variable in PREMIUM_ACTIVITY_TYPES and not network.premium_status_active:
                                continue
                            elif variable in PREMIUM_ACTIVITY_TYPES and variable not in activity.get(CONF_ACTIVITY_PROFILES, []):
                                continue
                            elif hasattr(profile, variable):
                                entities.append(EeroSensor(coordinator, network.id, profile.id, variable))

                for client in network.clients:
                    if client.id in conf_clients:
                        for variable in SENSOR_TYPES:
                            if variable in PREMIUM_TYPES and not network.premium_status_active:
                                continue
                            elif variable in PREMIUM_ACTIVITY_TYPES and not network.premium_status_active:
                                continue
                            elif variable in PREMIUM_ACTIVITY_TYPES and variable not in activity.get(CONF_ACTIVITY_CLIENTS, []):
                                continue
                            elif hasattr(client, variable):
                                entities.append(EeroSensor(coordinator, network.id, client.id, variable))

        return entities

    async_add_entities(await hass.async_add_job(get_entities), True)


class EeroSensor(SensorEntity, EeroEntity):
    """Representation of an Eero sensor entity."""

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        if self.resource.is_client:
            return f"{self.network.name} {self.resource.name_connection_type} {SENSOR_TYPES[self.variable][0]}"
        elif self.resource.is_eero or self.resource.is_profile:
            return f"{self.network.name} {self.resource.name} {SENSOR_TYPES[self.variable][0]}"
        return f"{self.resource.name} {SENSOR_TYPES[self.variable][0]}"

    @property
    def device_class(self) -> SensorDeviceClass:
        """Return the class of this entity."""
        return SENSOR_TYPES[self.variable][1]

    @property
    def state(self) -> StateType:
        """Return the state of the entity."""
        if self.variable in ["blocked_day", "blocked_month", "blocked_week"] and self.resource.is_network:
            return getattr(self.resource, self.variable)["blocked"]
        elif self.variable in ["data_usage_day", "data_usage_month", "data_usage_week"]:
            down, up = getattr(self.resource, self.variable)
            return format_data_usage(down + up)[0]
        elif self.variable in ["speed_down", "speed_up"]:
            return round(getattr(self.resource, self.variable)[0])
        return getattr(self.resource, self.variable)

    @final
    @property
    def unit_of_measurement(self) -> str:
        """Return the unit of measurement of the entity, after unit conversion."""
        if self.variable in ["data_usage_day", "data_usage_month", "data_usage_week"]:
            down, up = getattr(self.resource, self.variable)
            return format_data_usage(down + up)[1]
        elif self.variable in ["speed_down", "speed_up"]:
            return getattr(self.resource, self.variable)[1]
        return SENSOR_TYPES[self.variable][2]

    @property
    def extra_state_attributes(self) -> Mapping[str, Any]:
        """Return entity specific state attributes.

        Implemented by platform classes. Convention for attribute names
        is lowercase snake_case.
        """
        attrs = super().extra_state_attributes
        if self.variable in ["blocked_day", "blocked_month", "blocked_week"] and self.resource.is_network:
            data = getattr(self.resource, self.variable)
            for key, value in data.items():
                if key != "blocked":
                    attrs[key] = value
        elif self.variable in ["data_usage_day", "data_usage_month", "data_usage_week"]:
            down, up = getattr(self.resource, self.variable)
            attrs["download"], attrs["download_units"] = format_data_usage(down)
            attrs["upload"], attrs["upload_units"] = format_data_usage(up)
        elif self.variable == "nightlight_status" and self.resource.nightlight_schedule_enabled:
            attrs["on"], attrs["off"] = self.resource.nightlight_schedule
        elif self.variable in ["speed_down", "speed_up"]:
            attrs["last_updated"] = self.resource.speed_date
        elif self.variable == "status" and self.resource.is_network:
            for attr in [
                "ssid",
                "id",
                "isp",
                "city",
                "region_name",
                "postal_code",
                "country_name",
                "health_eero_network_status",
                "health_internet_isp_up",
                "health_internet_status",
            ]:
                attrs[attr] = getattr(self.resource, attr)
        return attrs
