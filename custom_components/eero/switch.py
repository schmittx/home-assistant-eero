"""Support for Eero switch entities."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from homeassistant.components.switch import (
    SwitchDeviceClass,
    SwitchEntity,
    SwitchEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import EeroEntity, EeroEntityDescription
from .const import (
    CONF_BACKUP_NETWORKS,
    CONF_MISCELLANEOUS,
    CONF_NETWORKS,
    CONF_PROFILES,
    CONF_RESOURCES,
    DATA_COORDINATOR,
    DOMAIN as EERO_DOMAIN,
)
from .util import client_allowed


@dataclass
class EeroSwitchEntityDescription(EeroEntityDescription, SwitchEntityDescription):
    """Class to describe an Eero switch entity."""

    device_class: str[SwitchDeviceClass] | None = SwitchDeviceClass.SWITCH
    entity_category: str[EntityCategory] | None = EntityCategory.CONFIG


SWITCH_DESCRIPTIONS: list[EeroSwitchEntityDescription] = [
    EeroSwitchEntityDescription(
        key="ad_block",
        name="Ad Blocking",
        premium_type=True,
    ),
    EeroSwitchEntityDescription(
        key="auto_join_enabled",
        name="Auto-Join Enabled",
        premium_type=True,
    ),
    EeroSwitchEntityDescription(
        key="backup_internet_enabled",
        name="Backup Internet Enabled",
        premium_type=True,
    ),
    EeroSwitchEntityDescription(
        key="band_steering",
        name="Band Steering",
    ),
    EeroSwitchEntityDescription(
        key="block_gaming_content",
        name="Gaming Content Filter",
        premium_type=True,
    ),
    EeroSwitchEntityDescription(
        key="block_illegal_content",
        name="Illegal or Criminal Content Filter",
        premium_type=True,
    ),
    EeroSwitchEntityDescription(
        key="block_malware",
        name="Advanced Security",
        premium_type=True,
    ),
    EeroSwitchEntityDescription(
        key="block_messaging_content",
        name="Chat and Messaging Content Filter",
        premium_type=True,
    ),
    EeroSwitchEntityDescription(
        key="block_pornographic_content",
        name="Adult Content Filter",
        premium_type=True,
    ),
    EeroSwitchEntityDescription(
        key="block_shopping_content",
        name="Shopping Content Filter",
        premium_type=True,
    ),
    EeroSwitchEntityDescription(
        key="block_social_content",
        name="Social Media Content Filter",
        premium_type=True,
    ),
    EeroSwitchEntityDescription(
        key="block_streaming_content",
        name="Streaming Content Filter",
        premium_type=True,
    ),
    EeroSwitchEntityDescription(
        key="block_violent_content",
        name="Violent Content Filter",
        premium_type=True,
    ),
    EeroSwitchEntityDescription(
        key="ddns_enabled",
        name="Dynamic DNS",
        premium_type=True,
        extra_attrs={
            "domain": lambda resource: resource.ddns_subdomain,
        },
    ),
    EeroSwitchEntityDescription(
        key="dns_caching",
        name="Local DNS Caching",
        request_refresh=False,
    ),
    EeroSwitchEntityDescription(
        key="guest_network_enabled",
        name="Guest Network",
        extra_attrs={
            "guest_network_name": lambda resource: resource.guest_network_name,
            "guest_network_password": lambda resource: resource.guest_network_password,
            "connected_guest_clients": lambda resource: resource.connected_guest_clients_count,
        },
    ),
    EeroSwitchEntityDescription(
        key="ipv6_upstream",
        name="IPv6 Enabled",
        request_refresh=False,
    ),
    EeroSwitchEntityDescription(
        key="pause_5g_enabled",
        name="5 GHz Band Paused",
        extra_attrs={
            "expiration": lambda resource: resource.pause_5g_expiration,
        },
    ),
    EeroSwitchEntityDescription(
        key="paused",
        name="Paused",
    ),
    EeroSwitchEntityDescription(
        key="safe_search_enabled",
        name="SafeSearch Content Filter",
        premium_type=True,
    ),
    EeroSwitchEntityDescription(
        key="secondary_wan_deny_access",
        name="Allow Internet Backup",
        premium_type=True,
    ),
    EeroSwitchEntityDescription(
        key="sqm",
        name="Smart Queue Management",
    ),
    EeroSwitchEntityDescription(
        key="thread_enabled",
        name="Thread Enabled",
        extra_attrs={
            "thread_network_key": lambda resource: resource.thread_master_key,
            "thread_network_name": lambda resource: resource.thread_name,
            "channel": lambda resource: resource.thread_channel,
            "pan_id": lambda resource: resource.thread_pan_id,
            "extended_pan_id": lambda resource: resource.thread_xpan_id,
            "commissioning_credential": lambda resource: resource.thread_commissioning_credential,
            "active_operational_dataset": lambda resource: resource.thread_active_operational_dataset,
        },
    ),
    EeroSwitchEntityDescription(
        key="upnp",
        name="UPnP",
    ),
    EeroSwitchEntityDescription(
        key="wpa3",
        name="WPA3",
    ),
    EeroSwitchEntityDescription(
        key="youtube_restricted",
        name="YouTube Restricted Content Filter",
        premium_type=True,
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up an Eero switch entity based on a config entry."""
    entry = hass.data[EERO_DOMAIN][config_entry.entry_id]
    coordinator = entry[DATA_COORDINATOR]
    entities: list[EeroSwitchEntity] = []

    SUPPORTED_KEYS = {
        description.key: description for description in SWITCH_DESCRIPTIONS
    }

    for network in coordinator.data.networks:
        if network.id in entry[CONF_NETWORKS]:
            for key, description in SUPPORTED_KEYS.items():
                if description.premium_type and not network.premium_enabled:
                    continue
                if hasattr(network, key):
                    entities.append(
                        EeroSwitchEntity(
                            coordinator,
                            network.id,
                            None,
                            description,
                            entry[CONF_MISCELLANEOUS][network.id],
                        )
                    )

            for backup_network in network.backup_networks:
                if (
                    backup_network.id
                    in entry[CONF_RESOURCES][network.id][CONF_BACKUP_NETWORKS]
                ):
                    for key, description in SUPPORTED_KEYS.items():
                        if hasattr(backup_network, key):
                            entities.append(
                                EeroSwitchEntity(
                                    coordinator,
                                    network.id,
                                    backup_network.id,
                                    description,
                                    entry[CONF_MISCELLANEOUS][network.id],
                                )
                            )

            for profile in network.profiles:
                if profile.id in entry[CONF_RESOURCES][network.id][CONF_PROFILES]:
                    for key, description in SUPPORTED_KEYS.items():
                        if description.premium_type and not network.premium_enabled:
                            continue
                        if hasattr(profile, key):
                            entities.append(
                                EeroSwitchEntity(
                                    coordinator,
                                    network.id,
                                    profile.id,
                                    description,
                                    entry[CONF_MISCELLANEOUS][network.id],
                                )
                            )

            for client in network.clients:
                if client_allowed(client, entry[CONF_RESOURCES][network.id]):
                    for key, description in SUPPORTED_KEYS.items():
                        if description.premium_type and not network.premium_enabled:
                            continue
                        if hasattr(client, key):
                            entities.append(
                                EeroSwitchEntity(
                                    coordinator,
                                    network.id,
                                    client.id,
                                    description,
                                    entry[CONF_MISCELLANEOUS][network.id],
                                )
                            )

    async_add_entities(entities)


class EeroSwitchEntity(EeroEntity, SwitchEntity):
    """Representation of an Eero switch entity."""

    @property
    def is_on(self) -> bool | None:
        """Return True if entity is on."""
        return bool(getattr(self.resource, self.entity_description.key))

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        """Return entity specific state attributes.

        Implemented by platform classes. Convention for attribute names
        is lowercase snake_case.
        """
        attrs = {}
        if self.entity_description.extra_attrs and self.is_on:
            for key, func in self.entity_description.extra_attrs.items():
                attrs[key] = func(self.resource)
        return attrs

    def turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        setattr(self.resource, self.entity_description.key, True)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        await super().async_turn_on()
        if self.entity_description.request_refresh:
            await self.coordinator.async_request_refresh()

    def turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        setattr(self.resource, self.entity_description.key, False)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        await super().async_turn_off()
        if self.entity_description.request_refresh:
            await self.coordinator.async_request_refresh()
