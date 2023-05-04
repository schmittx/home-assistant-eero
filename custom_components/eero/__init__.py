"""The Eero integration."""
import async_timeout
from collections.abc import Mapping
from datetime import timedelta
import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_MODE, CONF_NAME, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import EeroAPI, EeroException
from .api.network import Network as EeroNetwork
from .api.resource import Resource as EeroResource
from .const import (
    ACTIVITY_MAP_TO_HASS,
    ATTR_BLOCKED_APPS,
    ATTR_DNS_CACHING_ENABLED,
    ATTR_IPV6_ENABLED,
    ATTR_TARGET_EERO,
    ATTR_TARGET_NETWORK,
    ATTR_TARGET_PROFILE,
    ATTR_THREAD_ENABLED,
    ATTR_TIME_OFF,
    ATTR_TIME_ON,
    ATTRIBUTION,
    CONF_ACTIVITY,
    CONF_ACTIVITY_CLIENTS,
    CONF_ACTIVITY_EEROS,
    CONF_ACTIVITY_NETWORK,
    CONF_ACTIVITY_PROFILES,
    CONF_CLIENTS,
    CONF_EEROS,
    CONF_NETWORKS,
    CONF_PROFILES,
    CONF_SAVE_RESPONSES,
    CONF_TIMEOUT,
    CONF_USER_TOKEN,
    CONF_WIRED_CLIENTS,
    CONF_WIRELESS_CLIENTS,
    DATA_COORDINATOR,
    DEFAULT_SAVE_LOCATION,
    DEFAULT_SAVE_RESPONSES,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TIMEOUT,
    DOMAIN,
    MANUFACTURER,
    MODEL_CLIENT,
    MODEL_NETWORK,
    MODEL_PROFILE,
    NIGHTLIGHT_MODE_AMBIENT,
    NIGHTLIGHT_MODE_DISABLED,
    NIGHTLIGHT_MODE_SCHEDULE,
    NIGHTLIGHT_MODES,
    SERVICE_ENABLE_DNS_CACHING,
    SERVICE_ENABLE_IPV6,
    SERVICE_ENABLE_THREAD,
    SERVICE_RESTART_EERO,
    SERVICE_RESTART_NETWORK,
    SERVICE_SET_BLOCKED_APPS,
    SERVICE_SET_NIGHTLIGHT_MODE,
    SUPPORTED_APPS,
    UNDO_UPDATE_LISTENER,
)
from .util import validate_time_format

ENABLE_DNS_CACHING_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_DNS_CACHING_ENABLED): cv.boolean,
        vol.Optional(ATTR_TARGET_NETWORK, default=[]): vol.All(cv.ensure_list, [vol.Any(cv.positive_int, cv.string)]),
    }
)

ENABLE_IPV6_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_IPV6_ENABLED): cv.boolean,
        vol.Optional(ATTR_TARGET_NETWORK, default=[]): vol.All(cv.ensure_list, [vol.Any(cv.positive_int, cv.string)]),
    }
)

ENABLE_THREAD_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_THREAD_ENABLED): cv.boolean,
        vol.Optional(ATTR_TARGET_NETWORK, default=[]): vol.All(cv.ensure_list, [vol.Any(cv.positive_int, cv.string)]),
    }
)

RESTART_EERO_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_TARGET_EERO, default=[]): vol.All(cv.ensure_list, [vol.Any(cv.positive_int, cv.string)]),
        vol.Optional(ATTR_TARGET_NETWORK, default=[]): vol.All(cv.ensure_list, [vol.Any(cv.positive_int, cv.string)]),
    }
)

RESTART_NETWORK_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_TARGET_NETWORK, default=[]): vol.All(cv.ensure_list, [vol.Any(cv.positive_int, cv.string)]),
    }
)

SET_BLOCKED_APPS_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_BLOCKED_APPS): vol.All(cv.ensure_list, [vol.In(SUPPORTED_APPS)]),
        vol.Optional(ATTR_TARGET_PROFILE, default=[]): vol.All(cv.ensure_list, [vol.Any(cv.positive_int, cv.string)]),
        vol.Optional(ATTR_TARGET_NETWORK, default=[]): vol.All(cv.ensure_list, [vol.Any(cv.positive_int, cv.string)]),
    }
)

SET_NIGHTLIGHT_MODE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_MODE): vol.In(NIGHTLIGHT_MODES),
        vol.Optional(ATTR_TIME_ON): validate_time_format,
        vol.Optional(ATTR_TIME_OFF): validate_time_format,
        vol.Optional(ATTR_TARGET_EERO, default=[]): vol.All(cv.ensure_list, [vol.Any(cv.positive_int, cv.string)]),
        vol.Optional(ATTR_TARGET_NETWORK, default=[]): vol.All(cv.ensure_list, [vol.Any(cv.positive_int, cv.string)]),
    }
)

PLATFORMS = ["binary_sensor", "camera", "device_tracker", "sensor", "switch"]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up a config entry."""
    data = entry.data
    options = entry.options

    conf_networks = options.get(CONF_NETWORKS, data[CONF_NETWORKS])
    conf_eeros = options.get(CONF_EEROS, data.get(CONF_EEROS, []))
    conf_profiles = options.get(CONF_PROFILES, data.get(CONF_PROFILES, []))
    conf_wired_clients = options.get(CONF_WIRED_CLIENTS, data.get(CONF_WIRED_CLIENTS, []))
    conf_wireless_clients = options.get(CONF_WIRELESS_CLIENTS, data.get(CONF_WIRELESS_CLIENTS, []))
    conf_clients = conf_wired_clients + conf_wireless_clients
    conf_activity = options.get(CONF_ACTIVITY, data.get(CONF_ACTIVITY, {}))
    if not conf_networks:
        conf_eeros, conf_profiles, conf_clients = [], [], []
    conf_identifiers = [(DOMAIN, resource_id) for resource_id in conf_networks + conf_eeros + conf_profiles + conf_clients]

    device_registry = hass.helpers.device_registry.async_get(hass)
    entity_registry = hass.helpers.entity_registry.async_get(hass)
    for device_entry in hass.helpers.device_registry.async_entries_for_config_entry(device_registry, entry.entry_id):
        if all([bool(resource_id not in conf_identifiers) for resource_id in device_entry.identifiers]):
            device_registry.async_remove_device(device_entry.id)
        else:
            for entity_entry in hass.helpers.entity_registry.async_entries_for_device(entity_registry, device_entry.id):
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

    conf_save_responses = options.get(CONF_SAVE_RESPONSES, DEFAULT_SAVE_RESPONSES)
    conf_scan_interval = options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    conf_timeout = options.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)

    conf_save_location = DEFAULT_SAVE_LOCATION if conf_save_responses else None

    api = EeroAPI(activity=conf_activity, save_location=conf_save_location, user_token=data[CONF_USER_TOKEN])

    async def async_update_data():
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        try:
            async with async_timeout.timeout(conf_timeout):
                return await hass.async_add_executor_job(api.update)
        except EeroException as exception:
            raise UpdateFailed(f"Error communicating with API: {exception.error_message}")

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"Eero ({data[CONF_NAME]})",
        update_method=async_update_data,
        update_interval=timedelta(seconds=conf_scan_interval),
    )
    await coordinator.async_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        CONF_NETWORKS: conf_networks,
        CONF_EEROS: conf_eeros,
        CONF_PROFILES: conf_profiles,
        CONF_CLIENTS: conf_clients,
        CONF_ACTIVITY: conf_activity,
        DATA_COORDINATOR: coordinator,
        UNDO_UPDATE_LISTENER: entry.add_update_listener(async_update_listener),
    }

    def enable_dns_caching(service):
        _enable_network_attribute(
            target_network=service.data[ATTR_TARGET_NETWORK],
            attribute="dns_caching",
            enabled=service.data[ATTR_DNS_CACHING_ENABLED],
        )

    def enable_ipv6(service):
        _enable_network_attribute(
            target_network=service.data[ATTR_TARGET_NETWORK],
            attribute="ipv6",
            enabled=service.data[ATTR_IPV6_ENABLED],
        )

    def enable_thread(service):
        _enable_network_attribute(
            target_network=service.data[ATTR_TARGET_NETWORK],
            attribute="thread",
            enabled=service.data[ATTR_THREAD_ENABLED],
        )

    def restart_eero(service):
        for eero in _validate_eero(
            target_eero=service.data[ATTR_TARGET_EERO],
            target_network=service.data[ATTR_TARGET_NETWORK],
        ):
            eero.reboot()

    def restart_network(service):
        for network in _validate_network(target_network=service.data[ATTR_TARGET_NETWORK]):
            network.reboot()

    async def async_set_blocked_apps(service):
        blocked_apps = service.data[ATTR_BLOCKED_APPS]
        for profile in _validate_profile(
            target_profile=service.data[ATTR_TARGET_PROFILE],
            target_network=service.data[ATTR_TARGET_NETWORK],
        ):
            await hass.async_add_executor_job(profile.set_blocked_applications, blocked_apps)
        await coordinator.async_request_refresh()

    async def async_set_nightlight_mode(service):
        mode = service.data[ATTR_MODE]
        for eero in _validate_eero(
            target_eero=service.data[ATTR_TARGET_EERO],
            target_network=service.data[ATTR_TARGET_NETWORK],
        ):
            if eero.is_eero_beacon:
                if mode == NIGHTLIGHT_MODE_DISABLED:
                    await hass.async_add_executor_job(eero.set_nightlight_disabled)
                elif mode == NIGHTLIGHT_MODE_AMBIENT:
                    await hass.async_add_executor_job(eero.set_nightlight_ambient)
                elif mode == NIGHTLIGHT_MODE_SCHEDULE:
                    on = service.data.get(ATTR_TIME_ON, eero.nightlight_schedule[0])
                    off = service.data.get(ATTR_TIME_OFF, eero.nightlight_schedule[1])
                    if on == off:
                        return
                    await hass.async_add_executor_job(eero.set_nightlight_schedule, on, off)
        await coordinator.async_request_refresh()

    def _enable_network_attribute(attribute, enabled, target_network):
        for network in _validate_network(target_network=target_network):
            setattr(network, attribute, enabled)

    def _validate_eero(target_eero, target_network):
        validated_eero = []
        for network in _validate_network(target_network=target_network):
            for eero in network.eeros:
                if any([not target_eero, eero.id in target_eero, eero.name in target_eero]):
                    validated_eero.append(eero)
        return validated_eero

    def _validate_network(target_network):
        validated_network = []
        for network in coordinator.data.networks:
            if any([not target_network, network.id in target_network, network.name in target_network]):
                validated_network.append(network)
        return validated_network

    def _validate_profile(target_profile, target_network):
        validated_profile = []
        for network in _validate_network(target_network=target_network):
            for profile in network.profiles:
                if any([not target_profile, profile.id in target_profile, profile.name in target_profile]):
                    validated_profile.append(profile)
        return validated_profile

    if conf_networks:
        hass.services.async_register(
            DOMAIN,
            SERVICE_ENABLE_DNS_CACHING,
            enable_dns_caching,
            schema=ENABLE_DNS_CACHING_SCHEMA,
        )

        hass.services.async_register(
            DOMAIN,
            SERVICE_ENABLE_IPV6,
            enable_ipv6,
            schema=ENABLE_IPV6_SCHEMA,
        )

        hass.services.async_register(
            DOMAIN,
            SERVICE_ENABLE_THREAD,
            enable_thread,
            schema=ENABLE_THREAD_SCHEMA,
        )

        hass.services.async_register(
            DOMAIN,
            SERVICE_RESTART_NETWORK,
            restart_network,
            schema=RESTART_NETWORK_SCHEMA,
        )

    if conf_eeros:
        hass.services.async_register(
            DOMAIN,
            SERVICE_RESTART_EERO,
            restart_eero,
            schema=RESTART_EERO_SCHEMA,
        )

        if any([eero.is_eero_beacon for network in coordinator.data.networks for eero in network.eeros]):
            hass.services.async_register(
                DOMAIN,
                SERVICE_SET_NIGHTLIGHT_MODE,
                async_set_nightlight_mode,
                schema=SET_NIGHTLIGHT_MODE_SCHEMA,
            )

    if conf_profiles:
        hass.services.async_register(
            DOMAIN,
            SERVICE_SET_BLOCKED_APPS,
            async_set_blocked_apps,
            schema=SET_BLOCKED_APPS_SCHEMA,
        )

    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, PLATFORMS
    )
    if unload_ok:
        hass.data[DOMAIN][entry.entry_id][UNDO_UPDATE_LISTENER]()
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_update_listener(hass: HomeAssistant, entry: ConfigEntry):
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


class EeroEntity(CoordinatorEntity):
    """Representation of an Eero entity."""
    def __init__(self, coordinator, network_id, resource_id, variable):
        """Initialize device."""
        super().__init__(coordinator)
        self.network_id = network_id
        self.resource_id = resource_id
        self.variable = variable

    @property
    def network(self) -> EeroNetwork:
        """Return the state attributes."""
        for network in self.coordinator.data.networks:
            if network.id == self.network_id:
                return network

    @property
    def resource(self) -> EeroResource:
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
            return f"{self.network.id}-{self.variable}"
        return f"{self.network.id}-{self.resource.id}-{self.variable}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device specific attributes.

        Implemented by platform classes.
        """
        name = self.resource.name
        if self.resource.is_network:
            model = MODEL_NETWORK
        elif self.resource.is_eero:
            model = self.resource.model
        elif self.resource.is_profile:
            model = MODEL_PROFILE
        elif self.resource.is_client:
            model = MODEL_CLIENT
            name = self.resource.name_connection_type

        sw_version, via_device = None, None
        if self.resource.is_eero:
            sw_version = self.resource.os_version
        if any(
            [
                self.resource.is_eero,
                self.resource.is_profile,
                self.resource.is_client,
            ]
        ):
            via_device = (DOMAIN, self.network.id)

        return DeviceInfo(
            identifiers={(DOMAIN, self.resource.id)},
            manufacturer=MANUFACTURER,
            model=model,
            name=name,
            sw_version=sw_version,
            via_device=via_device,
        )

    @property
    def extra_state_attributes(self) -> Mapping[str, Any]:
        """Return entity specific state attributes.

        Implemented by platform classes. Convention for attribute names
        is lowercase snake_case.
        """
        attrs = {}
        return attrs

    @property
    def attribution(self) -> str:
        """Return the attribution."""
        return ATTRIBUTION

