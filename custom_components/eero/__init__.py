"""The Eero integration."""
from __future__ import annotations

from asyncio import timeout
from collections.abc import Callable
from dataclasses import dataclass
from datetime import timedelta
import logging
import voluptuous as vol
from typing import Any

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
from .api.const import SUPPORTED_APPS
from .api.network import EeroNetwork
from .api.resource import EeroResource
from .config_flow import EeroConfigFlow
from .const import (
    ACTIVITIES_PREMIUM,
    ATTR_BLOCKED_APPS,
    ATTR_TARGET_NETWORK,
    ATTR_TARGET_PROFILE,
    CONF_ACTIVITY,
    CONF_ACTIVITY_CLIENTS,
    CONF_ACTIVITY_EEROS,
    CONF_ACTIVITY_NETWORK,
    CONF_ACTIVITY_PROFILES,
    CONF_BACKUP_NETWORKS,
    CONF_CONSIDER_HOME,
    CONF_EEROS,
    CONF_FILTER_EXCLUDE,
    CONF_FILTER_INCLUDE,
    CONF_MISCELLANEOUS,
    CONF_NETWORKS,
    CONF_PREFIX_NETWORK_NAME,
    CONF_PROFILES,
    CONF_RESOURCES,
    CONF_SAVE_RESPONSES,
    CONF_SHOW_EERO_LOGO,
    CONF_SUFFIX_CONNECTION_TYPE,
    CONF_TIMEOUT,
    CONF_USER_TOKEN,
    CONF_WIRED_CLIENTS,
    CONF_WIRED_CLIENTS_FILTER,
    CONF_WIRELESS_CLIENTS,
    CONF_WIRELESS_CLIENTS_FILTER,
    DATA_API,
    DATA_COORDINATOR,
    DATA_UPDATE_LISTENER,
    DEFAULT_CONSIDER_HOME,
    DEFAULT_PREFIX_NETWORK_NAME,
    DEFAULT_SAVE_LOCATION,
    DEFAULT_SAVE_RESPONSES,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SHOW_EERO_LOGO,
    DEFAULT_SUFFIX_CONNECTION_TYPE,
    DEFAULT_TIMEOUT,
    DEFAULT_WIRED_CLIENTS_FILTER,
    DEFAULT_WIRELESS_CLIENTS_FILTER,
    DOMAIN,
    MANUFACTURER,
    MODEL_BACKUP_NETWORK,
    MODEL_CLIENT_WIRED,
    MODEL_CLIENT_WIRELESS,
    MODEL_NETWORK,
    MODEL_PROFILE,
    SERVICE_SET_BLOCKED_APPS,
)

SET_BLOCKED_APPS_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_BLOCKED_APPS): vol.All(cv.ensure_list, [vol.In(SUPPORTED_APPS.keys())]),
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


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate old entry."""
    if config_entry.version > EeroConfigFlow.VERSION:
        return False

    _LOGGER.info(f"Migrating configuration from version: {config_entry.version}.{config_entry.minor_version}")

    if config_entry.version < EeroConfigFlow.VERSION:

        data = dict(config_entry.data)
        _LOGGER.debug(f"Initial data:\n{data}")

        options = dict(config_entry.options)
        _LOGGER.debug(f"Initial options:\n{options}")

        if config_entry.version <= 1:

            resources = {}
            for network_id in options.get(CONF_NETWORKS, data.get(CONF_NETWORKS, [])):
                _LOGGER.info(f"Migrating resources for network: {network_id}")
                resources[network_id] = {
                    CONF_BACKUP_NETWORKS: [],
                    CONF_EEROS: [],
                    CONF_PROFILES: [],
                    CONF_WIRED_CLIENTS: [],
                    CONF_WIRED_CLIENTS_FILTER: DEFAULT_WIRED_CLIENTS_FILTER,
                    CONF_WIRELESS_CLIENTS: [],
                    CONF_WIRELESS_CLIENTS_FILTER: DEFAULT_WIRELESS_CLIENTS_FILTER,
                }

            device_registry = dr.async_get(hass)
            for conf in [CONF_BACKUP_NETWORKS, CONF_EEROS, CONF_PROFILES, CONF_WIRED_CLIENTS, CONF_WIRELESS_CLIENTS]:
                for device_entry in dr.async_entries_for_config_entry(device_registry, config_entry.entry_id):
                    if network_device_id := device_entry.via_device_id:
                        network_id = list(device_registry.async_get(network_device_id).identifiers)[0][1]
                        network_name = device_registry.async_get(network_device_id).name
                        resource_id = list(device_entry.identifiers)[0][1]
                        if any(
                            [
                                resource_id in options.get(conf, data.get(conf, [])),
                                resource_id in data.get(CONF_RESOURCES, {}).get(network_id, {}).get(conf, []),
                                resource_id in options.get(CONF_RESOURCES, {}).get(network_id, {}).get(conf, []),
                            ]
                        ):
                            _LOGGER.info(f"Migrating resource: {resource_id} in network: {network_id}\n- Name: {device_entry.name}\n- Type: {device_entry.model}\n- Network: {network_name}")
                            resources[network_id][conf].append(resource_id)

            data[CONF_RESOURCES] = resources
            options[CONF_RESOURCES] = resources

        if config_entry.version <= 2:

            miscellaneous = {}
            for network_id in options.get(CONF_NETWORKS, data.get(CONF_NETWORKS, [])):
                _LOGGER.info(f"Migrating miscellaneous options for network: {network_id}")
                miscellaneous[network_id] = {
                    CONF_CONSIDER_HOME: options.get(CONF_CONSIDER_HOME, data.get(CONF_CONSIDER_HOME, DEFAULT_CONSIDER_HOME)),
                    CONF_PREFIX_NETWORK_NAME: options.get(CONF_PREFIX_NETWORK_NAME, data.get(CONF_PREFIX_NETWORK_NAME, DEFAULT_PREFIX_NETWORK_NAME)),
                    CONF_SUFFIX_CONNECTION_TYPE: options.get(CONF_SUFFIX_CONNECTION_TYPE, data.get(CONF_SUFFIX_CONNECTION_TYPE, DEFAULT_SUFFIX_CONNECTION_TYPE)),
                    CONF_SHOW_EERO_LOGO: options.get(CONF_SHOW_EERO_LOGO, data.get(CONF_SHOW_EERO_LOGO, DEFAULT_SHOW_EERO_LOGO)),
                }

            data[CONF_MISCELLANEOUS] = miscellaneous
            options[CONF_MISCELLANEOUS] = miscellaneous

        _LOGGER.debug(f"Migrated data:\n{data}")
        _LOGGER.debug(f"Migrated options:\n{options}")

        hass.config_entries.async_update_entry(
            entry=config_entry,
            data=data,
            options=options,
            version=EeroConfigFlow.VERSION,
            minor_version=EeroConfigFlow.MINOR_VERSION,
        )

    _LOGGER.info(f"Successfully migrated configuration to version: {config_entry.version}.{config_entry.minor_version}")

    return True


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up a config entry."""
    data = config_entry.data
    options = config_entry.options

    conf_networks = options.get(CONF_NETWORKS, data.get(CONF_NETWORKS, []))
    conf_resources = options.get(CONF_RESOURCES, data.get(CONF_RESOURCES, {}))
    conf_activity = options.get(CONF_ACTIVITY, data.get(CONF_ACTIVITY, {}))
    conf_miscellaneous = options.get(CONF_MISCELLANEOUS, data.get(CONF_MISCELLANEOUS, {}))
    conf_save_responses = options.get(CONF_SAVE_RESPONSES, data.get(CONF_SAVE_RESPONSES, DEFAULT_SAVE_RESPONSES))
    conf_scan_interval = options.get(CONF_SCAN_INTERVAL, data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))
    conf_timeout = options.get(CONF_TIMEOUT, data.get(CONF_TIMEOUT, DEFAULT_TIMEOUT))

    device_registry = dr.async_get(hass)
    entity_registry = er.async_get(hass)

    for device_entry in dr.async_entries_for_config_entry(device_registry, config_entry.entry_id):
        _LOGGER.debug(f"Checking entries for device: {device_entry.name} - {device_entry.model}")
        for network_id, resources in conf_resources.items():
            conf_identifiers = [(DOMAIN, resource_id) for resource_id in [network_id] + resources[CONF_BACKUP_NETWORKS] + resources[CONF_EEROS] + resources[CONF_PROFILES]]
            conf_wired_client_identifiers = [(DOMAIN, resource_id) for resource_id in resources[CONF_WIRED_CLIENTS]]
            conf_wireless_client_identifiers = [(DOMAIN, resource_id) for resource_id in resources[CONF_WIRELESS_CLIENTS]]

            if any(
                [
                    all(
                        [
                            device_entry.model not in [MODEL_CLIENT_WIRED, MODEL_CLIENT_WIRELESS],
                            all([bool(identifier not in conf_identifiers) for identifier in device_entry.identifiers]),
                        ]
                    ),
                    all(
                        [
                            device_entry.model == MODEL_CLIENT_WIRED,
                            all([bool(identifier in conf_wired_client_identifiers) for identifier in device_entry.identifiers]),
                            resources[CONF_WIRED_CLIENTS_FILTER] == CONF_FILTER_EXCLUDE,
                        ]
                    ),
                    all(
                        [
                            device_entry.model == MODEL_CLIENT_WIRED,
                            all([bool(identifier not in conf_wired_client_identifiers) for identifier in device_entry.identifiers]),
                            resources[CONF_WIRED_CLIENTS_FILTER] == CONF_FILTER_INCLUDE,
                        ]
                    ),
                    all(
                        [
                            device_entry.model == MODEL_CLIENT_WIRELESS,
                            all([bool(identifier in conf_wireless_client_identifiers) for identifier in device_entry.identifiers]),
                            resources[CONF_WIRELESS_CLIENTS_FILTER] == CONF_FILTER_EXCLUDE,
                        ]
                    ),
                    all(
                        [
                            device_entry.model == MODEL_CLIENT_WIRELESS,
                            all([bool(identifier not in conf_wireless_client_identifiers) for identifier in device_entry.identifiers]),
                            resources[CONF_WIRELESS_CLIENTS_FILTER] == CONF_FILTER_INCLUDE,
                        ]
                    ),
                ]
            ):
                _LOGGER.debug(f"Removing device entry: {device_entry.name} - {device_entry.model}")
                device_registry.async_remove_device(device_entry.id)
            else:
                for entity_entry in er.async_entries_for_device(entity_registry, device_entry.id):
                    unique_id = entity_entry.unique_id.split("-")
                    activity = conf_activity.get(unique_id[0], {})
                    if all(
                        [
                            unique_id[-1] in ACTIVITIES_PREMIUM,
                            any(
                                [
                                    device_entry.model == MODEL_NETWORK and unique_id[-1] not in activity.get(CONF_ACTIVITY_NETWORK, []),
                                    MANUFACTURER in device_entry.model and unique_id[-1] not in activity.get(CONF_ACTIVITY_EEROS, []),
                                    device_entry.model == MODEL_PROFILE and unique_id[-1] not in activity.get(CONF_ACTIVITY_PROFILES, []),
                                    device_entry.model in [MODEL_CLIENT_WIRED, MODEL_CLIENT_WIRELESS] and unique_id[-1] not in activity.get(CONF_ACTIVITY_CLIENTS, []),
                                ]
                            ),
                        ]
                    ):
                            _LOGGER.debug(f"Removing entity: {entity_entry.name} from device entry: {device_entry.name} - {device_entry.model}")
                            entity_registry.async_remove(entity_entry.entity_id)

    api = EeroAPI(
        activity=conf_activity,
        save_location=DEFAULT_SAVE_LOCATION if conf_save_responses else None,
        show_eero_logo={network_id: miscellaneous[CONF_SHOW_EERO_LOGO] for network_id, miscellaneous in conf_miscellaneous.items()},
        user_token=data[CONF_USER_TOKEN],
    )

    async def async_update_data():
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        try:
            async with timeout(conf_timeout):
                return await hass.async_add_executor_job(api.update, conf_networks)
        except EeroException:
            raise UpdateFailed("Error communicating with API")

    coordinator = DataUpdateCoordinator(
        hass=hass,
        logger=_LOGGER,
        name=f"Eero ({data[CONF_NAME]})",
        update_method=async_update_data,
        update_interval=timedelta(seconds=conf_scan_interval),
    )
    await coordinator.async_refresh()

    for network in coordinator.data.networks:
        if conf_miscellaneous_network := conf_miscellaneous.get(network.id):
            conf_consider_home = conf_miscellaneous_network[CONF_CONSIDER_HOME]
            if conf_consider_home and timedelta(minutes=conf_consider_home) <= timedelta(seconds=conf_scan_interval):
                _LOGGER.info(f"For network: {network.name_unique} - Consider home interval, {int(conf_consider_home)} minute(s), should be set larger than polling interval, {int(conf_scan_interval)} seconds, otherwise it has no functionality.")

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][config_entry.entry_id] = {
        CONF_ACTIVITY: conf_activity,
        CONF_MISCELLANEOUS: conf_miscellaneous,
        CONF_NETWORKS: conf_networks,
        CONF_RESOURCES: conf_resources,
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

    if [profile for resources in conf_resources.values() for profile in resources[CONF_PROFILES]]:
        hass.services.async_register(
            DOMAIN,
            SERVICE_SET_BLOCKED_APPS,
            async_set_blocked_apps,
            schema=SET_BLOCKED_APPS_SCHEMA,
        )

    for network in coordinator.data.networks:
        if network.id in conf_networks:
            device_registry.async_get_or_create(
                config_entry_id=config_entry.entry_id,
                identifiers={(DOMAIN, network.id)},
                manufacturer=MANUFACTURER,
                name=network.name,
                model=MODEL_NETWORK,
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
        miscellaneous: dict[str, Any],
    ) -> None:
        """Initialize device."""
        super().__init__(coordinator)
        self.network_id = network_id
        self.resource_id = resource_id
        self.entity_description = description
        self.prefix_network_name = miscellaneous[CONF_PREFIX_NETWORK_NAME]
        self.suffix_connection_type =  miscellaneous[CONF_SUFFIX_CONNECTION_TYPE]

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
            model = MODEL_CLIENT_WIRELESS if self.resource.wireless else MODEL_CLIENT_WIRED
            if self.suffix_connection_type:
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
            name = self.resource.name
            if self.suffix_connection_type:
                name = self.resource.name_connection_type
            if self.prefix_network_name:
                name = f"{self.network.name} {name}"
            return f"{name} {self.entity_description.name}"
        elif self.resource.is_backup_network or self.resource.is_eero or self.resource.is_profile:
            name = f"{self.resource.name} {self.entity_description.name}"
            if self.prefix_network_name:
                name = f"{self.network.name} {name}"
            return name
        return f"{self.resource.name} {self.entity_description.name}"


@dataclass
class EeroEntityDescription(EntityDescription):
    """A class that describes Eero entities."""

    extra_attrs: dict[str, Callable] | None = None
    premium_type: bool = False
    request_refresh: bool = True
    translation_key: str | None = "all"
