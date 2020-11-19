"""Support for Eero sensors."""
import logging

from homeassistant.components.switch import DEVICE_CLASS_SWITCH, SwitchEntity

from . import EeroEntity
from .const import (
    CONF_CLIENTS,
    CONF_EEROS,
    CONF_NETWORKS,
    CONF_PROFILES,
    DATA_COORDINATOR,
    DOMAIN as EERO_DOMAIN,
    TYPE_CLIENT,
    TYPE_EERO,
    TYPE_NETWORK,
    TYPE_PROFILE,
)

_LOGGER = logging.getLogger(__name__)

BASIC_TYPES = {
    "band_steering": [[TYPE_NETWORK], "Band Steering"],
    "guest_network_enabled": [[TYPE_NETWORK], "Guest Network"],
    "led_on": [[TYPE_EERO], "LED Status Light"],
    "paused": [[TYPE_CLIENT, TYPE_PROFILE], "Paused"],
    "sqm": [[TYPE_NETWORK], "Smart Queue Management"],
    "upnp": [[TYPE_NETWORK], "UPnP"],
    "wpa3": [[TYPE_NETWORK], "WPA3"],
}

PREMIUM_TYPES = {
    "ad_block": [[TYPE_NETWORK], "Ad Blocking"],
    "block_illegal_content": [[TYPE_PROFILE], "Illegal Content Filter"],
    "block_malware": [[TYPE_NETWORK], "Advanced Security"],
    "block_pornographic_content": [[TYPE_PROFILE], "Adult Content Filter"],
    "block_violent_content": [[TYPE_PROFILE], "Violent Content Filter"],
    "safe_search_enabled": [[TYPE_PROFILE], "SafeSearch Content Filter"],
}

SWITCH_TYPES = {**BASIC_TYPES, **PREMIUM_TYPES}

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up a Eero sensor based on a config entry."""
    entry = hass.data[EERO_DOMAIN][entry.entry_id]
    conf_networks = entry[CONF_NETWORKS]
    conf_eeros = entry[CONF_EEROS]
    conf_profiles = entry[CONF_PROFILES]
    conf_clients = entry[CONF_CLIENTS]
    coordinator = entry[DATA_COORDINATOR]

    def get_switches():
        """Get the Eero switches."""
        switches = []

        for network in coordinator.data.networks:
            if network.id in conf_networks:
                for variable in SWITCH_TYPES:
                    if variable in PREMIUM_TYPES and not network.premium_status_active:
                        continue
                    elif TYPE_NETWORK in SWITCH_TYPES[variable][0]:
                        switches.append(EeroSwitch(coordinator, network, None, variable))

                for eero in network.eeros:
                    if eero.id in conf_eeros:
                        for variable in SWITCH_TYPES:
                            if variable in PREMIUM_TYPES and not network.premium_status_active:
                                continue
                            elif TYPE_EERO in SWITCH_TYPES[variable][0]:
                                switches.append(EeroSwitch(coordinator, network, eero, variable))

                for profile in network.profiles:
                    if profile.id in conf_profiles:
                        for variable in SWITCH_TYPES:
                            if variable in PREMIUM_TYPES and not network.premium_status_active:
                                continue
                            elif TYPE_PROFILE in SWITCH_TYPES[variable][0]:
                                switches.append(EeroSwitch(coordinator, network, profile, variable))

                for client in network.clients:
                    if client.id in conf_clients:
                        for variable in SWITCH_TYPES:
                            if variable in PREMIUM_TYPES and not network.premium_status_active:
                                continue
                            elif TYPE_CLIENT in SWITCH_TYPES[variable][0]:
                                switches.append(EeroSwitch(coordinator, network, client, variable))

        return switches

    async_add_entities(await hass.async_add_job(get_switches), True)


class EeroSwitch(SwitchEntity, EeroEntity):
    """Representation of a Eero sensor."""

    @property
    def name(self):
        """Return the name of the entity."""
        if self.resource.is_client:
            return f"{self.network.name} {self.resource.name_connection_type} {SWITCH_TYPES[self.variable][1]}"
        elif self.resource.is_eero or self.resource.is_profile:
            return f"{self.network.name} {self.resource.name} {SWITCH_TYPES[self.variable][1]}"
        return f"{self.resource.name} {SWITCH_TYPES[self.variable][1]}"

    @property
    def device_class(self):
        """Return the class of this device, from component DEVICE_CLASSES."""
        return DEVICE_CLASS_SWITCH

    @property
    def is_on(self):
        """Return true if the binary sensor is on."""
        return bool(getattr(self.resource, self.variable))

    @property
    def device_state_attributes(self):
        attrs = super().device_state_attributes
        if self.variable == "guest_network_enabled" and self.is_on:
            attrs["guest_network_name"] = self.resource.guest_network_name
        return attrs

    def turn_on(self, **kwargs):
        """Turn the device on."""
        setattr(self.resource, self.variable, True)

    async def async_turn_on(self, **kwargs):
        await super().async_turn_on()
        await self.coordinator.async_request_refresh()

    def turn_off(self, **kwargs):
        """Turn the device off."""
        setattr(self.resource, self.variable, False)

    async def async_turn_off(self, **kwargs):
        await super().async_turn_off()
        await self.coordinator.async_request_refresh()
