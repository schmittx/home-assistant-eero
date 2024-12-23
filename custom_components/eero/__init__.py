"""The Eero integration."""
from __future__ import annotations

import async_timeout
from collections.abc import Callable
from dataclasses import dataclass
from datetime import timedelta
import logging
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform, CONF_NAME, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.helpers import (
    config_validation as cv,
    device_registry as dr,
    entity_registry as er,
)
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import EeroAPI, EeroException
from .api.network import EeroNetwork
from .api.resource import EeroResource
from .const import (
    ACTIVITY_MAP_TO_HASS,
    ATTR_BLOCKED_APPS,
    ATTR_TARGET_NETWORK,
    ATTR_TARGET_PROFILE,
    CONF_ACTIVITY,
    CONF_ACTIVITY_CLIENTS,
    CONF_ACTIVITY_EEROS,
    CONF_ACTIVITY_NETWORK,
    CONF_ACTIVITY_PROFILES,
    CONF_BACKUP_NETWORKS,
    CONF_CLIENTS,
    CONF_EEROS,
    CONF_NETWORKS,
    CONF_PREFIX_NETWORK_NAME,
    CONF_PROFILES,
    CONF_SAVE_RESPONSES,
    CONF_SHOW_EERO_LOGO,
    CONF_TIMEOUT,
    CONF_USER_TOKEN,
    CONF_WIRED_CLIENTS,
    CONF_WIRELESS_CLIENTS,
    DATA_API,
    DATA_COORDINATOR,
    DATA_UPDATE_LISTENER,
    DEFAULT_PREFIX_NETWORK_NAME,
    DEFAULT_SAVE_LOCATION,
    DEFAULT_SAVE_RESPONSES,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SHOW_EERO_LOGO,
    DEFAULT_TIMEOUT,
    DOMAIN,
    MANUFACTURER,
    MODEL_BACKUP_NETWORK,
    MODEL_CLIENT,
    MODEL_NETWORK,
    MODEL_PROFILE,
    SERVICE_SET_BLOCKED_APPS,
    SUPPORTED_APPS,
)

SET_BLOCKED_APPS_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_BLOCKED_APPS): vol.All(cv.ensure_list, [vol.In(SUPPORTED_APPS)]),
        vol.Optional(ATTR_TARGET_PROFILE, default=[]): vol.All(cv.ensure_list, [vol.Any(cv.positive_int, cv.string)]),
        vol.Optional(ATTR_TARGET_NETWORK, default=[]): vol.All(cv.ensure_list, [vol.Any(cv.positive_int, cv.string)]),
    }
)

PLATFORMS = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.DEVICE_TRACKER,
    Platform.IMAGE,
    Platform.LIGHT,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.TIME,
    Platform.UPDATE,
]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up a config entry."""
    data = config_entry.data
    options = config_entry.options

    conf_networks = options.get(CONF_NETWORKS, data.get(CONF_NETWORKS, []))
    conf_backup_networks = options.get(CONF_BACKUP_NETWORKS, data.get(CONF_BACKUP_NETWORKS, []))
    conf_eeros = options.get(CONF_EEROS, data.get(CONF_EEROS, []))
    conf_profiles = options.get(CONF_PROFILES, data.get(CONF_PROFILES, []))
    conf_wired_clients = options.get(CONF_WIRED_CLIENTS, data.get(CONF_WIRED_CLIENTS, []))
    conf_wireless_clients = options.get(CONF_WIRELESS_CLIENTS, data.get(CONF_WIRELESS_CLIENTS, []))
    conf_clients = conf_wired_clients + conf_wireless_clients
    conf_activity = options.get(CONF_ACTIVITY, data.get(CONF_ACTIVITY, {}))
    if not conf_networks:
        conf_backup_networks, conf_eeros, conf_profiles, conf_clients = [], [], [], []
    conf_identifiers = [(DOMAIN, resource_id) for resource_id in conf_networks + conf_backup_networks + conf_eeros + conf_profiles + conf_clients]

    device_registry = dr.async_get(hass)
    entity_registry = er.async_get(hass)
    for device_entry in dr.async_entries_for_config_entry(device_registry, config_entry.entry_id):
        if all([bool(resource_id not in conf_identifiers) for resource_id in device_entry.identifiers]):
            device_registry.async_remove_device(device_entry.id)
        else:
            for entity_entry in er.async_entries_for_device(entity_registry, device_entry.id):
                unique_id = entity_entry.unique_id.split("-")
                activity = conf_activity.get(unique_id[0], {})
                if unique_id[-1] in list(ACTIVITY_MAP_TO_HASS.keys()):
                    if any(
                        [
                            device_entry.model == MODEL_NETWORK and unique_id[-1] not in activity.get(CONF_ACTIVITY_NETWORK, []),
                            MANUFACTURER in device_entry.model and unique_id[-1] not in activity.get(CONF_ACTIVITY_EEROS, []),
                            device_entry.model == MODEL_PROFILE and unique_id[-1] not in activity.get(CONF_ACTIVITY_PROFILES, []),
                            device_entry.model == MODEL_CLIENT and unique_id[-1] not in activity.get(CONF_ACTIVITY_CLIENTS, []),
                        ]
                    ):
                        entity_registry.async_remove(entity_entry.entity_id)

    conf_prefix_network_name = options.get(CONF_PREFIX_NETWORK_NAME, data.get(CONF_PREFIX_NETWORK_NAME, DEFAULT_PREFIX_NETWORK_NAME))
    conf_save_responses = options.get(CONF_SAVE_RESPONSES, data.get(CONF_SAVE_RESPONSES, DEFAULT_SAVE_RESPONSES))
    conf_scan_interval = options.get(CONF_SCAN_INTERVAL, data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))
    conf_show_eero_logo = options.get(CONF_SHOW_EERO_LOGO, data.get(CONF_SHOW_EERO_LOGO, DEFAULT_SHOW_EERO_LOGO))
    conf_timeout = options.get(CONF_TIMEOUT, data.get(CONF_TIMEOUT, DEFAULT_TIMEOUT))

    conf_save_location = DEFAULT_SAVE_LOCATION if conf_save_responses else None

    api = EeroAPI(
        activity=conf_activity,
        save_location=conf_save_location,
        show_eero_logo=conf_show_eero_logo,
        user_token=data[CONF_USER_TOKEN],
    )

    async def async_update_data():
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        try:
            async with async_timeout.timeout(conf_timeout):
                return await hass.async_add_executor_job(api.update, conf_networks)
        except EeroException as exception:
            raise UpdateFailed(f"Error communicating with API: {exception.error}")

    coordinator = DataUpdateCoordinator(
        hass=hass,
        logger=_LOGGER,
        name=f"Eero ({data[CONF_NAME]})",
        update_method=async_update_data,
        update_interval=timedelta(seconds=conf_scan_interval),
    )
    await coordinator.async_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][config_entry.entry_id] = {
        CONF_ACTIVITY: conf_activity,
        CONF_BACKUP_NETWORKS: conf_backup_networks,
        CONF_CLIENTS: conf_clients,
        CONF_EEROS: conf_eeros,
        CONF_NETWORKS: conf_networks,
        CONF_PREFIX_NETWORK_NAME: conf_prefix_network_name,
        CONF_PROFILES: conf_profiles,
        DATA_API: api,
        DATA_COORDINATOR: coordinator,
        DATA_UPDATE_LISTENER: config_entry.add_update_listener(async_update_listener),
    }

    async def async_set_blocked_apps(service):
        blocked_apps = service.data[ATTR_BLOCKED_APPS]
        for profile in _validate_profile(
            target_profile=service.data[ATTR_TARGET_PROFILE],
            target_network=service.data[ATTR_TARGET_NETWORK],
        ):
            await hass.async_add_executor_job(profile.set_blocked_applications, blocked_apps)
        await coordinator.async_request_refresh()

    def _validate_network(target_network: str):
        validated_network = []
        for network in coordinator.data.networks:
            if any([not target_network, network.id in target_network, network.name in target_network]):
                validated_network.append(network)
        return validated_network

    def _validate_profile(target_profile: str, target_network: str):
        validated_profile = []
        for network in _validate_network(target_network=target_network):
            for profile in network.profiles:
                if any([not target_profile, profile.id in target_profile, profile.name in target_profile]):
                    validated_profile.append(profile)
        return validated_profile

    if conf_profiles:
        hass.services.async_register(
            DOMAIN,
            SERVICE_SET_BLOCKED_APPS,
            async_set_blocked_apps,
            schema=SET_BLOCKED_APPS_SCHEMA,
        )

    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        config_entry, PLATFORMS
    )
    if unload_ok:
        hass.data[DOMAIN][config_entry.entry_id][DATA_UPDATE_LISTENER]()
        hass.data[DOMAIN].pop(config_entry.entry_id)

    return unload_ok


async def async_update_listener(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(config_entry.entry_id)


class EeroEntity(CoordinatorEntity):
    """Representation of an Eero entity."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        network_id: str,
        resource_id: str,
        description: EeroEntityDescription,
        prefix_network_name: bool = DEFAULT_PREFIX_NETWORK_NAME,
    ) -> None:
        """Initialize device."""
        super().__init__(coordinator)
        self.network_id = network_id
        self.resource_id = resource_id
        self.entity_description = description
        self.prefix_network_name = prefix_network_name

    @property
    def network(self) -> EeroNetwork | None:
        """Return the state attributes."""
        for network in self.coordinator.data.networks:
            if network.id == self.network_id:
                return network

    @property
    def resource(self) -> EeroResource | None:
        """Return the state attributes."""
        if self.resource_id:
            for resource in self.network.resources:
                if resource.id == self.resource_id:
                    return resource
        return self.network

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        if self.resource.is_network:
            return f"{self.network.id}-{self.entity_description.key}"
        return f"{self.network.id}-{self.resource.id}-{self.entity_description.key}"

    @property
    def device_info(self) -> dr.DeviceInfo:
        """Return device specific attributes.

        Implemented by platform classes.
        """
        name = self.resource.name
        if self.resource.is_network:
            model = MODEL_NETWORK
        elif self.resource.is_backup_network:
            model = MODEL_BACKUP_NETWORK
        elif self.resource.is_eero:
            model = self.resource.model
        elif self.resource.is_profile:
            model = MODEL_PROFILE
        elif self.resource.is_client:
            model = MODEL_CLIENT
            name = self.resource.name_connection_type

        entry_type, suggested_area, sw_version, hw_version, via_device = None, None, None, None, None
        if any(
            [
                self.resource.is_backup_network,
                self.resource.is_network,
                self.resource.is_profile,
            ]
        ):
            entry_type = dr.DeviceEntryType.SERVICE
        if self.resource.is_eero:
            suggested_area = self.resource.location
            sw_version = self.resource.os_version
            hw_version = self.resource.model_number
        if any(
            [
                self.resource.is_backup_network,
                self.resource.is_eero,
                self.resource.is_profile,
                self.resource.is_client,
            ]
        ):
            via_device = (DOMAIN, self.network.id)

        return dr.DeviceInfo(
            entry_type=entry_type,
            hw_version=hw_version,
            identifiers={(DOMAIN, self.resource.id)},
            manufacturer=MANUFACTURER,
            model=model,
            name=name,
            suggested_area=suggested_area,
            sw_version=sw_version,
            via_device=via_device,
        )

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        if self.resource.is_client:
            name = f"{self.resource.name_connection_type} {self.entity_description.name}"
            if self.prefix_network_name:
                return f"{self.network.name} {name}"
            return name
        elif self.resource.is_backup_network or self.resource.is_eero or self.resource.is_profile:
            name = f"{self.resource.name} {self.entity_description.name}"
            if self.prefix_network_name:
                return f"{self.network.name} {name}"
            return name
        return f"{self.resource.name} {self.entity_description.name}"


@dataclass
class EeroEntityDescription(EntityDescription):
    """A class that describes Eero entities."""

    extra_attrs: dict[str, Callable] | None = None
    premium_type: bool = False
    request_refresh: bool = True
    translation_key: str | None = "all"
