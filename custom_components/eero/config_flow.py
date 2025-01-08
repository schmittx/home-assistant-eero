"""Adds config flow for Eero integration."""

import logging
import voluptuous as vol
from typing import Any

from homeassistant import config_entries
from homeassistant.const import UnitOfTime, CONF_NAME, CONF_SCAN_INTERVAL
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.selector import BooleanSelector, NumberSelector, NumberSelectorConfig, SelectSelector, SelectSelectorConfig, SelectSelectorMode

from .api import EeroAPI, EeroException
from .const import (
    ACTIVITIES_DEFAULT,
    ACTIVITIES_DATA_USAGE_DEFAULT,
    ACTIVITIES_DATA_USAGE_PREMIUM,
    ACTIVITIES_PREMIUM,
    CONF_ACTIVITY,
    CONF_ACTIVITY_EEROS,
    CONF_ACTIVITY_CLIENTS,
    CONF_ACTIVITY_NETWORK,
    CONF_ACTIVITY_PROFILES,
    CONF_BACKUP_NETWORKS,
    CONF_CODE,
    CONF_EEROS,
    CONF_LOGIN,
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
    DEFAULT_PREFIX_NETWORK_NAME,
    DEFAULT_SAVE_RESPONSES,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SHOW_EERO_LOGO,
    DEFAULT_SUFFIX_CONNECTION_TYPE,
    DEFAULT_TIMEOUT,
    DEFAULT_WIRED_CLIENTS_FILTER,
    DEFAULT_WIRELESS_CLIENTS_FILTER,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MAX_TIMEOUT,
    MIN_SCAN_INTERVAL,
    MIN_TIMEOUT,
    STEP_SCAN_INTERVAL,
    STEP_TIMEOUT,
    VALUES_CLIENTS_FILTER,
)

_LOGGER = logging.getLogger(__name__)


class EeroConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Eero integration."""

    VERSION = 2
    MINOR_VERSION = 0
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialize."""
        self.api = None
        self.index = 0
        self.response = None
        self.user_input = {}

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            self.user_input[CONF_LOGIN] = user_input[CONF_LOGIN]
            self.api = EeroAPI()

            try:
                self.response = await self.hass.async_add_executor_job(
                    self.api.login, user_input[CONF_LOGIN],
                )
            except EeroException as exception:
                _LOGGER.error(f"Status: {exception.code}, Error Message: {exception.error}")
                errors["base"] = "invalid_login"

            self.user_input[CONF_USER_TOKEN] = self.response["user_token"]

            return await self.async_step_verify()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_LOGIN): cv.string}),
            errors=errors,
        )

    async def async_step_verify(self, user_input=None):
        errors = {}

        if user_input is not None:

            try:
                self.response = await self.hass.async_add_executor_job(
                    self.api.login_verify, user_input[CONF_CODE],
                )
            except EeroException as exception:
                _LOGGER.error(f"Status: {exception.code}, Error Message: {exception.error}")
                errors["base"] = "invalid_code"

            await self.async_set_unique_id(self.response["log_id"].lower())
            self._abort_if_unique_id_configured()
            self.user_input[CONF_NAME] = self.response["name"]
            self.response = await self.hass.async_add_executor_job(self.api.update)
            return await self.async_step_networks()

        return self.async_show_form(
            step_id="verify",
            data_schema=vol.Schema({vol.Required(CONF_CODE): cv.string}),
            description_placeholders={"login": self.user_input[CONF_LOGIN]},
            errors=errors,
        )

    async def async_step_networks(self, user_input=None):
        if user_input is not None:
            self.user_input[CONF_NETWORKS] = [network.id for network in self.response.networks if network.name_unique in user_input[CONF_NETWORKS]]
            return await self.async_step_resources()

        network_names = [network.name_unique for network in self.response.networks]

        return self.async_show_form(
            step_id="networks",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NETWORKS, default=network_names): SelectSelector(
                        SelectSelectorConfig(
                            options=network_names,
                            multiple=True,
                            mode=SelectSelectorMode.DROPDOWN,
                            sort=True,
                        )
                    ),
                }
            ),
        )

    async def async_step_resources(self, user_input=None):
        if user_input is not None:
            target_network = self.user_input[CONF_NETWORKS][self.index]
            for network in self.response.networks:
                if network.id == target_network:
                    self.user_input[CONF_RESOURCES][network.id] = {
                        CONF_BACKUP_NETWORKS: [backup_network.id for backup_network in network.backup_networks if backup_network.name in user_input.get(CONF_BACKUP_NETWORKS, [])],
                        CONF_EEROS: [eero.id for eero in network.eeros if eero.name in user_input[CONF_EEROS]],
                        CONF_PROFILES: [profile.id for profile in network.profiles if profile.name in user_input[CONF_PROFILES]],
                        CONF_WIRED_CLIENTS: [client.id for client in network.clients if client.name_mac in user_input[CONF_WIRED_CLIENTS]],
                        CONF_WIRED_CLIENTS_FILTER: user_input[CONF_WIRED_CLIENTS_FILTER],
                        CONF_WIRELESS_CLIENTS: [client.id for client in network.clients if client.name_mac in user_input[CONF_WIRELESS_CLIENTS]],
                        CONF_WIRELESS_CLIENTS_FILTER: user_input[CONF_WIRELESS_CLIENTS_FILTER],
                    }
                    self.index += 1

        if self.index == len(self.user_input[CONF_NETWORKS]):
            self.index = 0
            return await self.async_step_activity()
        elif self.index == 0:
            self.user_input[CONF_RESOURCES] = {}

        target_network = self.user_input[CONF_NETWORKS][self.index]
        for network in self.response.networks:
            if network.id == target_network:
                eero_names = [eero.name for eero in network.eeros]
                profile_names = [profile.name for profile in network.profiles]
                wired_client_names = [client.name_mac for client in network.clients if not client.wireless]
                wireless_client_names = [client.name_mac for client in network.clients if client.wireless]
                schema = {
                    vol.Required(CONF_EEROS, default=eero_names): SelectSelector(
                        SelectSelectorConfig(
                            options=eero_names,
                            multiple=True,
                            mode=SelectSelectorMode.DROPDOWN,
                            sort=True,
                        )
                    ),
                    vol.Required(CONF_PROFILES, default=profile_names): SelectSelector(
                        SelectSelectorConfig(
                            options=profile_names,
                            multiple=True,
                            mode=SelectSelectorMode.DROPDOWN,
                            sort=True,
                        )
                    ),
                    vol.Required(CONF_WIRED_CLIENTS, default=[]): SelectSelector(
                        SelectSelectorConfig(
                            options=wired_client_names,
                            multiple=True,
                            mode=SelectSelectorMode.DROPDOWN,
                            sort=True,
                        )
                    ),
                    vol.Required(CONF_WIRED_CLIENTS_FILTER, default=DEFAULT_WIRED_CLIENTS_FILTER): SelectSelector(
                        SelectSelectorConfig(
                            options=VALUES_CLIENTS_FILTER,
                            translation_key="all",
                        )
                    ),
                    vol.Required(CONF_WIRELESS_CLIENTS, default=[]): SelectSelector(
                        SelectSelectorConfig(
                            options=wireless_client_names,
                            multiple=True,
                            mode=SelectSelectorMode.DROPDOWN,
                            sort=True,
                        )
                    ),
                    vol.Required(CONF_WIRELESS_CLIENTS_FILTER, default=DEFAULT_WIRELESS_CLIENTS_FILTER): SelectSelector(
                        SelectSelectorConfig(
                            options=VALUES_CLIENTS_FILTER,
                            translation_key="all",
                        )
                    ),
                }
                if network.premium_enabled:
                    backup_network_names = [backup_network.name for backup_network in network.backup_networks]
                    schema[vol.Required(CONF_BACKUP_NETWORKS, default=backup_network_names)] = SelectSelector(
                        SelectSelectorConfig(
                            options=backup_network_names,
                            multiple=True,
                            mode=SelectSelectorMode.DROPDOWN,
                            sort=True,
                        )
                    )

                return self.async_show_form(
                    step_id="resources",
                    data_schema=vol.Schema(schema),
                    description_placeholders={"network": network.name_unique},
                )

    async def async_step_activity(self, user_input=None):
        if user_input is not None:
            target_network = self.user_input[CONF_NETWORKS][self.index]
            for network in self.response.networks:
                if network.id == target_network:
                    self.user_input[CONF_ACTIVITY][network.id] = {
                            CONF_ACTIVITY_NETWORK: user_input[CONF_ACTIVITY_NETWORK],
                            CONF_ACTIVITY_EEROS: user_input.get(CONF_ACTIVITY_EEROS, []),
                            CONF_ACTIVITY_PROFILES: user_input.get(CONF_ACTIVITY_PROFILES, []),
                            CONF_ACTIVITY_CLIENTS: user_input.get(CONF_ACTIVITY_CLIENTS, []),
                    }
                    self.index += 1

        if self.index == len(self.user_input[CONF_NETWORKS]):
            self.index = 0
            if self.show_advanced_options:
                return await self.async_step_advanced()
            return self.async_create_entry(title=self.user_input[CONF_NAME], data=self.user_input)
        elif self.index == 0:
            self.user_input[CONF_ACTIVITY] = {}

        target_network = self.user_input[CONF_NETWORKS][self.index]
        for network in self.response.networks:
            if network.id == target_network:
                activity_options = ACTIVITIES_DEFAULT
                data_usage_options = ACTIVITIES_DATA_USAGE_DEFAULT
                if network.premium_enabled:
                    activity_options = ACTIVITIES_PREMIUM
                    data_usage_options = ACTIVITIES_DATA_USAGE_PREMIUM

                data_schema = {
                        vol.Required(CONF_ACTIVITY_NETWORK, default=[]): SelectSelector(
                            SelectSelectorConfig(
                                options=activity_options,
                                multiple=True,
                                mode=SelectSelectorMode.DROPDOWN,
                                translation_key="all",
                            )
                        ),
                }

                if self.user_input[CONF_RESOURCES][network.id][CONF_EEROS]:
                    data_schema[vol.Required(CONF_ACTIVITY_EEROS, default=[])] = SelectSelector(
                        SelectSelectorConfig(
                            options=data_usage_options,
                            multiple=True,
                            mode=SelectSelectorMode.DROPDOWN,
                            translation_key="all",
                        )
                    )

                if self.user_input[CONF_RESOURCES][network.id][CONF_PROFILES]:
                    data_schema[vol.Required(CONF_ACTIVITY_PROFILES, default=[])] = SelectSelector(
                        SelectSelectorConfig(
                            options=activity_options,
                            multiple=True,
                            mode=SelectSelectorMode.DROPDOWN,
                            translation_key="all",
                        )
                    )

                if any(
                    [
                        self.user_input[CONF_RESOURCES][network.id][CONF_WIRED_CLIENTS],
                        self.user_input[CONF_RESOURCES][network.id][CONF_WIRELESS_CLIENTS],
                    ]
                ):
                    data_schema[vol.Required(CONF_ACTIVITY_CLIENTS, default=[])] = SelectSelector(
                        SelectSelectorConfig(
                            options=activity_options,
                            multiple=True,
                            mode=SelectSelectorMode.DROPDOWN,
                            translation_key="all",
                        )
                    )

                return self.async_show_form(
                    step_id="activity",
                    data_schema=vol.Schema(data_schema),
                    description_placeholders={"network": network.name_unique},
                )

    async def async_step_advanced(self, user_input=None):
        """Handle a flow initialized by the user."""
        if user_input is not None:
            self.user_input[CONF_PREFIX_NETWORK_NAME] = user_input[CONF_PREFIX_NETWORK_NAME]
            self.user_input[CONF_SUFFIX_CONNECTION_TYPE] = user_input[CONF_SUFFIX_CONNECTION_TYPE]
            self.user_input[CONF_SAVE_RESPONSES] = user_input[CONF_SAVE_RESPONSES]
            self.user_input[CONF_SHOW_EERO_LOGO] = user_input[CONF_SHOW_EERO_LOGO]
            self.user_input[CONF_SCAN_INTERVAL] = user_input[CONF_SCAN_INTERVAL]
            self.user_input[CONF_TIMEOUT] = user_input[CONF_TIMEOUT]
            return self.async_create_entry(title=f"{self.user_input[CONF_NAME]} ({self.user_input[CONF_LOGIN]})", data=self.user_input)

        return self.async_show_form(
            step_id="advanced",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_PREFIX_NETWORK_NAME, default=DEFAULT_PREFIX_NETWORK_NAME): BooleanSelector(),
                    vol.Required(CONF_SUFFIX_CONNECTION_TYPE, default=DEFAULT_SUFFIX_CONNECTION_TYPE): BooleanSelector(),
                    vol.Required(CONF_SAVE_RESPONSES, default=DEFAULT_SAVE_RESPONSES): BooleanSelector(),
                    vol.Required(CONF_SHOW_EERO_LOGO, default=DEFAULT_SHOW_EERO_LOGO): BooleanSelector(),
                    vol.Required(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): NumberSelector(
                        NumberSelectorConfig(
                            min=MIN_SCAN_INTERVAL,
                            max=MAX_SCAN_INTERVAL,
                            step=STEP_SCAN_INTERVAL,
                            unit_of_measurement=UnitOfTime.SECONDS,
                        )
                    ),
                    vol.Required(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): NumberSelector(
                        NumberSelectorConfig(
                            min=MIN_TIMEOUT,
                            max=MAX_TIMEOUT,
                            step=STEP_TIMEOUT,
                            unit_of_measurement=UnitOfTime.SECONDS,
                        )
                    ),
                }
            ),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Eero options callback."""
        return EeroOptionsFlowHandler()


class EeroOptionsFlowHandler(config_entries.OptionsFlow):
    """Config flow options for Eero."""

    def __init__(self):
        """Initialize Eero options flow."""
        self.api = None
        self.index = 0
        self.response = None
        self.user_input = {}

    @property
    def data(self) -> dict[str, Any]:
        """Return the data from a config entry."""
        return self.config_entry.data

    @property
    def options(self) -> dict[str, Any]:
        """Return the options from a config entry."""
        return self.config_entry.options

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        self.api = self.hass.data[DOMAIN][self.config_entry.entry_id][DATA_API]
        self.response = await self.hass.async_add_executor_job(self.api.update)
        return await self.async_step_networks()

    async def async_step_networks(self, user_input=None):
        """Handle a flow initialized by the user."""
        if user_input is not None:
            self.user_input[CONF_NETWORKS] = [network.id for network in self.response.networks if network.name_unique in user_input[CONF_NETWORKS]]
            return await self.async_step_resources()

        conf_networks = [network.name_unique for network in self.response.networks if network.id in self.options.get(CONF_NETWORKS, self.data[CONF_NETWORKS])]
        network_names = [network.name_unique for network in self.response.networks]

        return self.async_show_form(
            step_id="networks",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NETWORKS, default=conf_networks): SelectSelector(
                        SelectSelectorConfig(
                            options=network_names,
                            multiple=True,
                            mode=SelectSelectorMode.DROPDOWN,
                            sort=True,
                        )
                    ),
                }
            ),
        )

    async def async_step_resources(self, user_input=None):
        """Handle a flow initialized by the user."""
        if user_input is not None:
            target_network = self.user_input[CONF_NETWORKS][self.index]
            for network in self.response.networks:
                if network.id == target_network:
                    self.user_input[CONF_RESOURCES][network.id] = {
                        CONF_BACKUP_NETWORKS: [backup_network.id for backup_network in network.backup_networks if backup_network.name in user_input.get(CONF_BACKUP_NETWORKS, [])],
                        CONF_EEROS: [eero.id for eero in network.eeros if eero.name in user_input[CONF_EEROS]],
                        CONF_PROFILES: [profile.id for profile in network.profiles if profile.name in user_input[CONF_PROFILES]],
                        CONF_WIRED_CLIENTS: [client.id for client in network.clients if client.name_mac in user_input[CONF_WIRED_CLIENTS]],
                        CONF_WIRED_CLIENTS_FILTER: user_input[CONF_WIRED_CLIENTS_FILTER],
                        CONF_WIRELESS_CLIENTS: [client.id for client in network.clients if client.name_mac in user_input[CONF_WIRELESS_CLIENTS]],
                        CONF_WIRELESS_CLIENTS_FILTER: user_input[CONF_WIRELESS_CLIENTS_FILTER],
                    }
                    self.index += 1

        if self.index == len(self.user_input[CONF_NETWORKS]):
            self.index = 0
            return await self.async_step_activity()
        elif self.index == 0:
            self.user_input[CONF_RESOURCES] = {}

        target_network = self.user_input[CONF_NETWORKS][self.index]
        for network in self.response.networks:
            if network.id == target_network:
                conf_resources = self.options.get(CONF_RESOURCES, self.data.get(CONF_RESOURCES, {})).get(network.id, {})

                conf_eeros = [eero.name for eero in network.eeros if eero.id in conf_resources.get(CONF_EEROS, [])]
                eero_names = [eero.name for eero in network.eeros]

                conf_profiles = [profile.name for profile in network.profiles if profile.id in conf_resources.get(CONF_PROFILES, [])]
                profile_names = [profile.name for profile in network.profiles]

                conf_wired_clients = [client.name_mac for client in network.clients if client.id in conf_resources.get(CONF_WIRED_CLIENTS, [])]
                wired_client_names = [client.name_mac for client in network.clients if not client.wireless]

                conf_wired_clients_filter = conf_resources.get(CONF_WIRED_CLIENTS_FILTER, DEFAULT_WIRED_CLIENTS_FILTER)

                conf_wireless_clients = [client.name_mac for client in network.clients if client.id in conf_resources.get(CONF_WIRELESS_CLIENTS, [])]
                wireless_client_names = [client.name_mac for client in network.clients if client.wireless]

                conf_wireless_clients_filter = conf_resources.get(CONF_WIRELESS_CLIENTS_FILTER, DEFAULT_WIRELESS_CLIENTS_FILTER)

                schema = {
                    vol.Required(CONF_EEROS, default=conf_eeros): SelectSelector(
                        SelectSelectorConfig(
                            options=eero_names,
                            multiple=True,
                            mode=SelectSelectorMode.DROPDOWN,
                            sort=True,
                        )
                    ),
                    vol.Required(CONF_PROFILES, default=conf_profiles): SelectSelector(
                        SelectSelectorConfig(
                            options=profile_names,
                            multiple=True,
                            mode=SelectSelectorMode.DROPDOWN,
                            sort=True,
                        )
                    ),
                    vol.Required(CONF_WIRED_CLIENTS, default=conf_wired_clients): SelectSelector(
                        SelectSelectorConfig(
                            options=wired_client_names,
                            multiple=True,
                            mode=SelectSelectorMode.DROPDOWN,
                            sort=True,
                        )
                    ),
                    vol.Required(CONF_WIRED_CLIENTS_FILTER, default=conf_wired_clients_filter): SelectSelector(
                        SelectSelectorConfig(
                            options=VALUES_CLIENTS_FILTER,
                            translation_key="all",
                        )
                    ),
                    vol.Required(CONF_WIRELESS_CLIENTS, default=conf_wireless_clients): SelectSelector(
                        SelectSelectorConfig(
                            options=wireless_client_names,
                            multiple=True,
                            mode=SelectSelectorMode.DROPDOWN,
                            sort=True,
                        )
                    ),
                    vol.Required(CONF_WIRELESS_CLIENTS_FILTER, default=conf_wireless_clients_filter): SelectSelector(
                        SelectSelectorConfig(
                            options=VALUES_CLIENTS_FILTER,
                            translation_key="all",
                        )
                    ),
                }
                if network.premium_enabled:
                    conf_backup_networks = [backup_network.name for backup_network in network.backup_networks if backup_network.id in conf_resources.get(CONF_BACKUP_NETWORKS, [])]
                    backup_network_names = [backup_network.name for backup_network in network.backup_networks]
                    schema[vol.Required(CONF_BACKUP_NETWORKS, default=conf_backup_networks)] = SelectSelector(
                        SelectSelectorConfig(
                            options=backup_network_names,
                            multiple=True,
                            mode=SelectSelectorMode.DROPDOWN,
                            sort=True,
                        )
                    )

                return self.async_show_form(
                    step_id="resources",
                    data_schema=vol.Schema(schema),
                    description_placeholders={"network": network.name_unique},
                )

    async def async_step_activity(self, user_input=None):
        if user_input is not None:
            target_network = self.user_input[CONF_NETWORKS][self.index]
            for network in self.response.networks:
                if network.id == target_network:
                    self.user_input[CONF_ACTIVITY][network.id] = {
                            CONF_ACTIVITY_NETWORK: user_input[CONF_ACTIVITY_NETWORK],
                            CONF_ACTIVITY_EEROS: user_input.get(CONF_ACTIVITY_EEROS, []),
                            CONF_ACTIVITY_PROFILES: user_input.get(CONF_ACTIVITY_PROFILES, []),
                            CONF_ACTIVITY_CLIENTS: user_input.get(CONF_ACTIVITY_CLIENTS, []),
                    }
                    self.index += 1

        if self.index == len(self.user_input[CONF_NETWORKS]):
            self.index = 0
            if self.show_advanced_options:
                return await self.async_step_advanced()
            return self.async_create_entry(title="", data=self.user_input)
        elif self.index == 0:
            self.user_input[CONF_ACTIVITY] = {}

        target_network = self.user_input[CONF_NETWORKS][self.index]
        for network in self.response.networks:
            if network.id == target_network:
                activity_options = ACTIVITIES_DEFAULT
                data_usage_options = ACTIVITIES_DATA_USAGE_DEFAULT
                if network.premium_enabled:
                    activity_options = ACTIVITIES_PREMIUM
                    data_usage_options = ACTIVITIES_DATA_USAGE_PREMIUM

                conf_activity = self.options.get(CONF_ACTIVITY, self.data.get(CONF_ACTIVITY, {})).get(network.id, {})

                conf_activity_network = conf_activity.get(CONF_ACTIVITY_NETWORK, [])
                conf_activity_eero = conf_activity.get(CONF_ACTIVITY_EEROS, [])
                conf_activity_profile = conf_activity.get(CONF_ACTIVITY_PROFILES, [])
                conf_activity_client = conf_activity.get(CONF_ACTIVITY_CLIENTS, [])

                data_schema = {
                        vol.Required(CONF_ACTIVITY_NETWORK, default=conf_activity_network): SelectSelector(
                            SelectSelectorConfig(
                                options=activity_options,
                                multiple=True,
                                mode=SelectSelectorMode.DROPDOWN,
                                translation_key="all",
                            )
                        ),
                }

                if self.user_input[CONF_RESOURCES][network.id][CONF_EEROS]:
                    data_schema[vol.Required(CONF_ACTIVITY_EEROS, default=conf_activity_eero)] = SelectSelector(
                        SelectSelectorConfig(
                            options=data_usage_options,
                            multiple=True,
                            mode=SelectSelectorMode.DROPDOWN,
                            translation_key="all",
                        )
                    )

                if self.user_input[CONF_RESOURCES][network.id][CONF_PROFILES]:
                    data_schema[vol.Required(CONF_ACTIVITY_PROFILES, default=conf_activity_profile)] = SelectSelector(
                        SelectSelectorConfig(
                            options=activity_options,
                            multiple=True,
                            mode=SelectSelectorMode.DROPDOWN,
                            translation_key="all",
                        )
                    )

                if any(
                    [
                        self.user_input[CONF_RESOURCES][network.id][CONF_WIRED_CLIENTS],
                        self.user_input[CONF_RESOURCES][network.id][CONF_WIRELESS_CLIENTS],
                    ]
                ):
                    data_schema[vol.Required(CONF_ACTIVITY_CLIENTS, default=conf_activity_client)] = SelectSelector(
                        SelectSelectorConfig(
                            options=activity_options,
                            multiple=True,
                            mode=SelectSelectorMode.DROPDOWN,
                            translation_key="all",
                        )
                    )

                return self.async_show_form(
                    step_id="activity",
                    data_schema=vol.Schema(data_schema),
                    description_placeholders={"network": network.name_unique},
                )

    async def async_step_advanced(self, user_input=None):
        """Handle a flow initialized by the user."""
        if user_input is not None:
            self.user_input[CONF_PREFIX_NETWORK_NAME] = user_input[CONF_PREFIX_NETWORK_NAME]
            self.user_input[CONF_SUFFIX_CONNECTION_TYPE] = user_input[CONF_SUFFIX_CONNECTION_TYPE]
            self.user_input[CONF_SAVE_RESPONSES] = user_input[CONF_SAVE_RESPONSES]
            self.user_input[CONF_SHOW_EERO_LOGO] = user_input[CONF_SHOW_EERO_LOGO]
            self.user_input[CONF_SCAN_INTERVAL] = user_input[CONF_SCAN_INTERVAL]
            self.user_input[CONF_TIMEOUT] = user_input[CONF_TIMEOUT]
            return self.async_create_entry(title="", data=self.user_input)

        conf_prefix_network_name = self.options.get(CONF_PREFIX_NETWORK_NAME, self.data.get(CONF_PREFIX_NETWORK_NAME, DEFAULT_PREFIX_NETWORK_NAME))
        conf_suffix_connection_type = self.options.get(CONF_SUFFIX_CONNECTION_TYPE, self.data.get(CONF_SUFFIX_CONNECTION_TYPE, DEFAULT_SUFFIX_CONNECTION_TYPE))
        conf_save_responses = self.options.get(CONF_SAVE_RESPONSES, self.data.get(CONF_SAVE_RESPONSES, DEFAULT_SAVE_RESPONSES))
        conf_show_eero_logo = self.options.get(CONF_SHOW_EERO_LOGO, self.data.get(CONF_SHOW_EERO_LOGO, DEFAULT_SHOW_EERO_LOGO))
        conf_scan_interval = self.options.get(CONF_SCAN_INTERVAL, self.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))
        conf_timeout = self.options.get(CONF_TIMEOUT, self.data.get(CONF_TIMEOUT, DEFAULT_TIMEOUT))

        return self.async_show_form(
            step_id="advanced",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_PREFIX_NETWORK_NAME, default=conf_prefix_network_name): BooleanSelector(),
                    vol.Required(CONF_SUFFIX_CONNECTION_TYPE, default=conf_suffix_connection_type): BooleanSelector(),
                    vol.Required(CONF_SAVE_RESPONSES, default=conf_save_responses): BooleanSelector(),
                    vol.Required(CONF_SHOW_EERO_LOGO, default=conf_show_eero_logo): BooleanSelector(),
                    vol.Required(CONF_SCAN_INTERVAL, default=conf_scan_interval): NumberSelector(
                        NumberSelectorConfig(
                            min=MIN_SCAN_INTERVAL,
                            max=MAX_SCAN_INTERVAL,
                            step=STEP_SCAN_INTERVAL,
                            unit_of_measurement=UnitOfTime.SECONDS,
                        )
                    ),
                    vol.Required(CONF_TIMEOUT, default=conf_timeout): NumberSelector(
                        NumberSelectorConfig(
                            min=MIN_TIMEOUT,
                            max=MAX_TIMEOUT,
                            step=STEP_TIMEOUT,
                            unit_of_measurement=UnitOfTime.SECONDS,
                        )
                    ),
                }
            ),
        )
