"""Support for Eero switch entities."""
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
)

_LOGGER = logging.getLogger(__name__)

BASIC_TYPES = {
    "band_steering": [
        "Band Steering",
    ],
    "guest_network_enabled": [
        "Guest Network",
    ],
    "led_on": [
        "LED Status Light",
    ],
    "paused": [
        "Paused",
    ],
    "sqm": [
        "Smart Queue Management",
    ],
    "upnp": [
        "UPnP",
    ],
    "wpa3": [
        "WPA3",
    ],
}

PREMIUM_TYPES = {
    "ad_block": [
        "Ad Blocking",
    ],
    "block_gaming_content": [
        "Gaming Content Filter",
    ],
    "block_illegal_content": [
        "Illegal or Criminal Content Filter",
    ],
    "block_malware": [
        "Advanced Security",
    ],
    "block_messaging_content": [
        "Chat and Messaging Content Filter",
    ],
    "block_pornographic_content": [
        "Adult Content Filter",
    ],
    "block_shopping_content": [
        "Shopping Content Filter",
    ],
    "block_social_content": [
        "Social Media Content Filter",
    ],
    "block_streaming_content": [
        "Streaming Content Filter",
    ],
    "block_violent_content": [
        "Violent Content Filter",
    ],
    "safe_search_enabled": [
        "SafeSearch Content Filter",
    ],
    "youtube_restricted": [
        "YouTube Restricted Content Filter",
    ],
}

SWITCH_TYPES = {**BASIC_TYPES, **PREMIUM_TYPES}

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up an Eero switch entity based on a config entry."""
    entry = hass.data[EERO_DOMAIN][entry.entry_id]
    conf_networks = entry[CONF_NETWORKS]
    conf_eeros = entry[CONF_EEROS]
    conf_profiles = entry[CONF_PROFILES]
    conf_clients = entry[CONF_CLIENTS]
    coordinator = entry[DATA_COORDINATOR]

    def get_entities():
        """Get the Eero switch entities."""
        entities = []

        for network in coordinator.data.networks:
            if network.id in conf_networks:
                for variable in SWITCH_TYPES:
                    if variable in PREMIUM_TYPES and not network.premium_status_active:
                        continue
                    elif hasattr(network, variable):
                        entities.append(EeroSwitch(coordinator, network, None, variable))

                for eero in network.eeros:
                    if eero.id in conf_eeros:
                        for variable in SWITCH_TYPES:
                            if variable in PREMIUM_TYPES and not network.premium_status_active:
                                continue
                            elif hasattr(eero, variable):
                                entities.append(EeroSwitch(coordinator, network, eero, variable))

                for profile in network.profiles:
                    if profile.id in conf_profiles:
                        for variable in SWITCH_TYPES:
                            if variable in PREMIUM_TYPES and not network.premium_status_active:
                                continue
                            elif hasattr(profile, variable):
                                entities.append(EeroSwitch(coordinator, network, profile, variable))

                for client in network.clients:
                    if client.id in conf_clients:
                        for variable in SWITCH_TYPES:
                            if variable in PREMIUM_TYPES and not network.premium_status_active:
                                continue
                            elif hasattr(client, variable):
                                entities.append(EeroSwitch(coordinator, network, client, variable))

        return entities

    async_add_entities(await hass.async_add_job(get_entities), True)


class EeroSwitch(SwitchEntity, EeroEntity):
    """Representation of an Eero switch entity."""

    @property
    def name(self):
        """Return the name of the entity."""
        switch_type = SWITCH_TYPES[self.variable][0]

        if self.resource.is_client:
            name = self.resource.name
            
            # Since eero is a WiFi router, only add the connection type annotation to the device name
            # for non-wireless devices.
            if not self.resource.wireless:
                name = self.resource.name_connection_type

            return f"{self.network.name} {name} {switch_type}"

        elif self.resource.is_eero or self.resource.is_profile:
            return f"{self.network.name} {self.resource.name} {switch_type}"

        return f"{self.resource.name} {switch_type}"

    @property
    def device_class(self):
        """Return the class of this device, from component DEVICE_CLASSES."""
        return DEVICE_CLASS_SWITCH

    @property
    def is_on(self):
        """Return true if the switch is on."""
        return bool(getattr(self.resource, self.variable))

    @property
    def device_state_attributes(self):
        attrs = super().device_state_attributes
        if self.variable == "guest_network_enabled" and self.is_on:
            attrs["guest_network_name"] = self.resource.guest_network_name
            attrs["connected_guest_clients"] = self.resource.connected_guest_clients_count
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
