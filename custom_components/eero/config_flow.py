"""Adds config flow for Eero integration."""

from datetime import timedelta
import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME, CONF_SCAN_INTERVAL, UnitOfTime
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    BooleanSelector,
    NumberSelector,
    NumberSelectorConfig,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import EeroAPI, EeroException
from .const import (
    ACTIVITIES_DATA_USAGE_DEFAULT,
    ACTIVITIES_DATA_USAGE_PREMIUM,
    ACTIVITIES_DEFAULT,
    ACTIVITIES_PREMIUM,
    CONF_ACTIVITY,
    CONF_ACTIVITY_CLIENTS,
    CONF_ACTIVITY_EEROS,
    CONF_ACTIVITY_NETWORK,
    CONF_ACTIVITY_PROFILES,
    CONF_BACKUP_NETWORKS,
    CONF_CODE,
    CONF_CONSIDER_HOME,
    CONF_EEROS,
    CONF_LOGIN,
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
    DEFAULT_CONSIDER_HOME,
    DEFAULT_PREFIX_NETWORK_NAME,
    DEFAULT_SAVE_RESPONSES,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SHOW_EERO_LOGO,
    DEFAULT_SUFFIX_CONNECTION_TYPE,
    DEFAULT_TIMEOUT,
    DEFAULT_WIRED_CLIENTS_FILTER,
    DEFAULT_WIRELESS_CLIENTS_FILTER,
    DOMAIN,
    MAX_CONSIDER_HOME,
    MAX_SCAN_INTERVAL,
    MAX_TIMEOUT,
    MIN_CONSIDER_HOME,
    MIN_SCAN_INTERVAL,
    MIN_TIMEOUT,
    STEP_CONSIDER_HOME,
    STEP_SCAN_INTERVAL,
    STEP_TIMEOUT,
    VALUES_CLIENTS_FILTER,
)

_LOGGER = logging.getLogger(__name__)


class EeroConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Eero integration."""

    VERSION = 3
    MINOR_VERSION = 0
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self) -> None:
        """Initialize."""
        self.api = None
        self.index = 0
        self.response = None
        self.user_input = {}

    @property
    def config_title(self) -> str:
        """Return the config title."""
        return f"{self.user_input[CONF_NAME]} ({self.user_input[CONF_LOGIN]})"

    async def async_step_user(self, user_input=None):
        """Async step user."""
        errors = {}

        if user_input:
            self.api = EeroAPI()
            try:
                self.response = await self.hass.async_add_executor_job(
                    self.api.login,
                    user_input[CONF_LOGIN],
                )
            except EeroException as exception:
                _LOGGER.error(
                    "Status: %s, Error Message: %s", exception.code, exception.error
                )
                errors["base"] = "invalid_login"
            else:
                self.user_input[CONF_LOGIN] = user_input[CONF_LOGIN]
                self.user_input[CONF_USER_TOKEN] = self.response["user_token"]
                return await self.async_step_verify()

        user_input = {}
        conf_login = user_input[CONF_LOGIN] if user_input else None

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_LOGIN, default=conf_login): TextSelector(
                        TextSelectorConfig(
                            type=TextSelectorType.TEXT,
                        )
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_verify(self, user_input=None):
        """Async step verify."""
        errors = {}

        if user_input:
            try:
                self.response = await self.hass.async_add_executor_job(
                    self.api.login_verify,
                    user_input[CONF_CODE],
                )
            except EeroException as exception:
                _LOGGER.error(
                    "Status: %s, Error Message: %s", exception.code, exception.error
                )
                errors["base"] = "invalid_code"
            else:
                await self.async_set_unique_id(self.response["log_id"].lower())
                self._abort_if_unique_id_configured()
                self.user_input[CONF_NAME] = self.response["name"]
                self.response = await self.hass.async_add_executor_job(self.api.update)
                return await self.async_step_networks()

        user_input = {}
        conf_code = user_input[CONF_CODE] if user_input else None

        return self.async_show_form(
            step_id="verify",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_CODE, default=conf_code): TextSelector(
                        TextSelectorConfig(
                            type=TextSelectorType.NUMBER,
                        )
                    ),
                }
            ),
            description_placeholders={"login": self.user_input[CONF_LOGIN]},
            errors=errors,
        )

    async def async_step_networks(self, user_input=None):
        """Async step networks."""
        if user_input is not None:
            self.user_input[CONF_NETWORKS] = [
                network.id
                for network in self.response.networks
                if network.name_unique in user_input[CONF_NETWORKS]
            ]
            return await self.async_step_resources()

        network_names = [network.name_unique for network in self.response.networks]

        return self.async_show_form(
            step_id="networks",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_NETWORKS, default=network_names): SelectSelector(
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
        """Async step resources."""
        if user_input is not None:
            target_network = self.user_input[CONF_NETWORKS][self.index]
            for network in self.response.networks:
                if network.id == target_network:
                    self.user_input[CONF_RESOURCES][network.id] = {
                        CONF_BACKUP_NETWORKS: [
                            backup_network.id
                            for backup_network in network.backup_networks
                            if backup_network.name
                            in user_input.get(CONF_BACKUP_NETWORKS, [])
                        ],
                        CONF_EEROS: [
                            eero.id
                            for eero in network.eeros
                            if eero.name in user_input[CONF_EEROS]
                        ],
                        CONF_PROFILES: [
                            profile.id
                            for profile in network.profiles
                            if profile.name in user_input[CONF_PROFILES]
                        ],
                        CONF_WIRED_CLIENTS: [
                            client.id
                            for client in network.clients
                            if client.name_mac in user_input[CONF_WIRED_CLIENTS]
                        ],
                        CONF_WIRED_CLIENTS_FILTER: user_input[
                            CONF_WIRED_CLIENTS_FILTER
                        ],
                        CONF_WIRELESS_CLIENTS: [
                            client.id
                            for client in network.clients
                            if client.name_mac in user_input[CONF_WIRELESS_CLIENTS]
                        ],
                        CONF_WIRELESS_CLIENTS_FILTER: user_input[
                            CONF_WIRELESS_CLIENTS_FILTER
                        ],
                    }
                    self.index += 1

        if self.index == len(self.user_input[CONF_NETWORKS]):
            self.index = 0
            return await self.async_step_activity()
        if self.index == 0:
            self.user_input[CONF_RESOURCES] = {}

        target_network = self.user_input[CONF_NETWORKS][self.index]
        for network in self.response.networks:
            if network.id == target_network:
                eero_names = [eero.name for eero in network.eeros]
                profile_names = [profile.name for profile in network.profiles]
                wired_client_names = [
                    client.name_mac for client in network.clients if not client.wireless
                ]
                wireless_client_names = [
                    client.name_mac for client in network.clients if client.wireless
                ]
                schema = {
                    vol.Optional(CONF_EEROS, default=eero_names): SelectSelector(
                        SelectSelectorConfig(
                            options=eero_names,
                            multiple=True,
                            mode=SelectSelectorMode.DROPDOWN,
                            sort=True,
                        )
                    ),
                    vol.Optional(CONF_PROFILES, default=profile_names): SelectSelector(
                        SelectSelectorConfig(
                            options=profile_names,
                            multiple=True,
                            mode=SelectSelectorMode.DROPDOWN,
                            sort=True,
                        )
                    ),
                    vol.Optional(CONF_WIRED_CLIENTS, default=[]): SelectSelector(
                        SelectSelectorConfig(
                            options=wired_client_names,
                            multiple=True,
                            mode=SelectSelectorMode.DROPDOWN,
                            sort=True,
                        )
                    ),
                    vol.Optional(
                        CONF_WIRED_CLIENTS_FILTER, default=DEFAULT_WIRED_CLIENTS_FILTER
                    ): SelectSelector(
                        SelectSelectorConfig(
                            options=VALUES_CLIENTS_FILTER,
                            translation_key="all",
                        )
                    ),
                    vol.Optional(CONF_WIRELESS_CLIENTS, default=[]): SelectSelector(
                        SelectSelectorConfig(
                            options=wireless_client_names,
                            multiple=True,
                            mode=SelectSelectorMode.DROPDOWN,
                            sort=True,
                        )
                    ),
                    vol.Optional(
                        CONF_WIRELESS_CLIENTS_FILTER,
                        default=DEFAULT_WIRELESS_CLIENTS_FILTER,
                    ): SelectSelector(
                        SelectSelectorConfig(
                            options=VALUES_CLIENTS_FILTER,
                            translation_key="all",
                        )
                    ),
                }
                if network.premium_enabled:
                    backup_network_names = [
                        backup_network.name
                        for backup_network in network.backup_networks
                    ]
                    schema[
                        vol.Optional(CONF_BACKUP_NETWORKS, default=backup_network_names)
                    ] = SelectSelector(
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
        return None

    async def async_step_activity(self, user_input=None):
        """Async step activity."""
        if user_input is not None:
            target_network = self.user_input[CONF_NETWORKS][self.index]
            for network in self.response.networks:
                if network.id == target_network:
                    self.user_input[CONF_ACTIVITY][network.id] = {
                        CONF_ACTIVITY_NETWORK: user_input[CONF_ACTIVITY_NETWORK],
                        CONF_ACTIVITY_EEROS: user_input.get(CONF_ACTIVITY_EEROS, []),
                        CONF_ACTIVITY_PROFILES: user_input.get(
                            CONF_ACTIVITY_PROFILES, []
                        ),
                        CONF_ACTIVITY_CLIENTS: user_input.get(
                            CONF_ACTIVITY_CLIENTS, []
                        ),
                    }
                    self.index += 1

        if self.index == len(self.user_input[CONF_NETWORKS]):
            self.index = 0
            return await self.async_step_miscellaneous()
        if self.index == 0:
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
                    vol.Optional(CONF_ACTIVITY_NETWORK, default=[]): SelectSelector(
                        SelectSelectorConfig(
                            options=activity_options,
                            multiple=True,
                            mode=SelectSelectorMode.DROPDOWN,
                            translation_key="all",
                        )
                    ),
                }

                if self.user_input[CONF_RESOURCES][network.id][CONF_EEROS]:
                    data_schema[vol.Optional(CONF_ACTIVITY_EEROS, default=[])] = (
                        SelectSelector(
                            SelectSelectorConfig(
                                options=data_usage_options,
                                multiple=True,
                                mode=SelectSelectorMode.DROPDOWN,
                                translation_key="all",
                            )
                        )
                    )

                if self.user_input[CONF_RESOURCES][network.id][CONF_PROFILES]:
                    data_schema[vol.Optional(CONF_ACTIVITY_PROFILES, default=[])] = (
                        SelectSelector(
                            SelectSelectorConfig(
                                options=activity_options,
                                multiple=True,
                                mode=SelectSelectorMode.DROPDOWN,
                                translation_key="all",
                            )
                        )
                    )

                if any(
                    [
                        self.user_input[CONF_RESOURCES][network.id][CONF_WIRED_CLIENTS],
                        self.user_input[CONF_RESOURCES][network.id][
                            CONF_WIRELESS_CLIENTS
                        ],
                    ]
                ):
                    data_schema[vol.Optional(CONF_ACTIVITY_CLIENTS, default=[])] = (
                        SelectSelector(
                            SelectSelectorConfig(
                                options=activity_options,
                                multiple=True,
                                mode=SelectSelectorMode.DROPDOWN,
                                translation_key="all",
                            )
                        )
                    )

                return self.async_show_form(
                    step_id="activity",
                    data_schema=vol.Schema(data_schema),
                    description_placeholders={"network": network.name_unique},
                )
        return None

    async def async_step_miscellaneous(self, user_input=None):
        """Async step miscellaneous."""
        if user_input is not None:
            target_network = self.user_input[CONF_NETWORKS][self.index]
            for network in self.response.networks:
                if network.id == target_network:
                    self.user_input[CONF_MISCELLANEOUS][network.id] = {
                        CONF_CONSIDER_HOME: user_input[CONF_CONSIDER_HOME],
                        CONF_PREFIX_NETWORK_NAME: user_input[CONF_PREFIX_NETWORK_NAME],
                        CONF_SUFFIX_CONNECTION_TYPE: user_input[
                            CONF_SUFFIX_CONNECTION_TYPE
                        ],
                        CONF_SHOW_EERO_LOGO: user_input[CONF_SHOW_EERO_LOGO],
                    }
                    self.index += 1

        if self.index == len(self.user_input[CONF_NETWORKS]):
            self.index = 0
            if self.show_advanced_options:
                return await self.async_step_advanced()
            return self.async_create_entry(
                title=self.config_title, data=self.user_input
            )
        if self.index == 0:
            self.user_input[CONF_MISCELLANEOUS] = {}

        target_network = self.user_input[CONF_NETWORKS][self.index]
        for network in self.response.networks:
            if network.id == target_network:
                return self.async_show_form(
                    step_id="miscellaneous",
                    data_schema=vol.Schema(
                        {
                            vol.Optional(
                                CONF_CONSIDER_HOME, default=DEFAULT_CONSIDER_HOME
                            ): NumberSelector(
                                NumberSelectorConfig(
                                    min=MIN_CONSIDER_HOME,
                                    max=MAX_CONSIDER_HOME,
                                    step=STEP_CONSIDER_HOME,
                                    unit_of_measurement=UnitOfTime.MINUTES,
                                )
                            ),
                            vol.Optional(
                                CONF_PREFIX_NETWORK_NAME,
                                default=DEFAULT_PREFIX_NETWORK_NAME,
                            ): BooleanSelector(),
                            vol.Optional(
                                CONF_SUFFIX_CONNECTION_TYPE,
                                default=DEFAULT_SUFFIX_CONNECTION_TYPE,
                            ): BooleanSelector(),
                            vol.Optional(
                                CONF_SHOW_EERO_LOGO, default=DEFAULT_SHOW_EERO_LOGO
                            ): BooleanSelector(),
                        }
                    ),
                    description_placeholders={"network": network.name_unique},
                )
        return None

    async def async_step_advanced(self, user_input=None):
        """Handle a flow initialized by the user."""
        errors = {}

        if user_input:
            conf_scan_interval = user_input[CONF_SCAN_INTERVAL]
            conf_timeout = user_input[CONF_TIMEOUT]

            invalid_scan_interval_timeout = timedelta(
                seconds=conf_scan_interval
            ) <= timedelta(seconds=conf_timeout)

            if invalid_scan_interval_timeout:
                errors["base"] = "invalid_scan_interval_timeout"
            else:
                self.user_input[CONF_SAVE_RESPONSES] = user_input[CONF_SAVE_RESPONSES]
                self.user_input[CONF_SCAN_INTERVAL] = conf_scan_interval
                self.user_input[CONF_TIMEOUT] = conf_timeout
                return self.async_create_entry(
                    title=self.config_title, data=self.user_input
                )

        return self.async_show_form(
            step_id="advanced",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SAVE_RESPONSES, default=DEFAULT_SAVE_RESPONSES
                    ): BooleanSelector(),
                    vol.Optional(
                        CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                    ): NumberSelector(
                        NumberSelectorConfig(
                            min=MIN_SCAN_INTERVAL,
                            max=MAX_SCAN_INTERVAL,
                            step=STEP_SCAN_INTERVAL,
                            unit_of_measurement=UnitOfTime.SECONDS,
                        )
                    ),
                    vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): NumberSelector(
                        NumberSelectorConfig(
                            min=MIN_TIMEOUT,
                            max=MAX_TIMEOUT,
                            step=STEP_TIMEOUT,
                            unit_of_measurement=UnitOfTime.SECONDS,
                        )
                    ),
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Eero options callback."""
        return EeroOptionsFlowHandler()


class EeroOptionsFlowHandler(config_entries.OptionsFlow):
    """Config flow options for Eero."""

    def __init__(self) -> None:
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
            self.user_input[CONF_NETWORKS] = [
                network.id
                for network in self.response.networks
                if network.name_unique in user_input[CONF_NETWORKS]
            ]
            return await self.async_step_resources()

        conf_networks = [
            network.name_unique
            for network in self.response.networks
            if network.id in self.options.get(CONF_NETWORKS, self.data[CONF_NETWORKS])
        ]
        network_names = [network.name_unique for network in self.response.networks]

        return self.async_show_form(
            step_id="networks",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_NETWORKS, default=conf_networks): SelectSelector(
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
                        CONF_BACKUP_NETWORKS: [
                            backup_network.id
                            for backup_network in network.backup_networks
                            if backup_network.name
                            in user_input.get(CONF_BACKUP_NETWORKS, [])
                        ],
                        CONF_EEROS: [
                            eero.id
                            for eero in network.eeros
                            if eero.name in user_input[CONF_EEROS]
                        ],
                        CONF_PROFILES: [
                            profile.id
                            for profile in network.profiles
                            if profile.name in user_input[CONF_PROFILES]
                        ],
                        CONF_WIRED_CLIENTS: [
                            client.id
                            for client in network.clients
                            if client.name_mac in user_input[CONF_WIRED_CLIENTS]
                        ],
                        CONF_WIRED_CLIENTS_FILTER: user_input[
                            CONF_WIRED_CLIENTS_FILTER
                        ],
                        CONF_WIRELESS_CLIENTS: [
                            client.id
                            for client in network.clients
                            if client.name_mac in user_input[CONF_WIRELESS_CLIENTS]
                        ],
                        CONF_WIRELESS_CLIENTS_FILTER: user_input[
                            CONF_WIRELESS_CLIENTS_FILTER
                        ],
                    }
                    self.index += 1

        if self.index == len(self.user_input[CONF_NETWORKS]):
            self.index = 0
            return await self.async_step_activity()
        if self.index == 0:
            self.user_input[CONF_RESOURCES] = {}

        target_network = self.user_input[CONF_NETWORKS][self.index]
        for network in self.response.networks:
            if network.id == target_network:
                conf_resources = self.options.get(
                    CONF_RESOURCES, self.data.get(CONF_RESOURCES, {})
                ).get(network.id, {})

                conf_eeros = [
                    eero.name
                    for eero in network.eeros
                    if eero.id in conf_resources.get(CONF_EEROS, [])
                ]
                eero_names = [eero.name for eero in network.eeros]

                conf_profiles = [
                    profile.name
                    for profile in network.profiles
                    if profile.id in conf_resources.get(CONF_PROFILES, [])
                ]
                profile_names = [profile.name for profile in network.profiles]

                conf_wired_clients = [
                    client.name_mac
                    for client in network.clients
                    if client.id in conf_resources.get(CONF_WIRED_CLIENTS, [])
                ]
                wired_client_names = [
                    client.name_mac for client in network.clients if not client.wireless
                ]

                conf_wired_clients_filter = conf_resources.get(
                    CONF_WIRED_CLIENTS_FILTER, DEFAULT_WIRED_CLIENTS_FILTER
                )

                conf_wireless_clients = [
                    client.name_mac
                    for client in network.clients
                    if client.id in conf_resources.get(CONF_WIRELESS_CLIENTS, [])
                ]
                wireless_client_names = [
                    client.name_mac for client in network.clients if client.wireless
                ]

                conf_wireless_clients_filter = conf_resources.get(
                    CONF_WIRELESS_CLIENTS_FILTER, DEFAULT_WIRELESS_CLIENTS_FILTER
                )

                schema = {
                    vol.Optional(CONF_EEROS, default=conf_eeros): SelectSelector(
                        SelectSelectorConfig(
                            options=eero_names,
                            multiple=True,
                            mode=SelectSelectorMode.DROPDOWN,
                            sort=True,
                        )
                    ),
                    vol.Optional(CONF_PROFILES, default=conf_profiles): SelectSelector(
                        SelectSelectorConfig(
                            options=profile_names,
                            multiple=True,
                            mode=SelectSelectorMode.DROPDOWN,
                            sort=True,
                        )
                    ),
                    vol.Optional(
                        CONF_WIRED_CLIENTS, default=conf_wired_clients
                    ): SelectSelector(
                        SelectSelectorConfig(
                            options=wired_client_names,
                            multiple=True,
                            mode=SelectSelectorMode.DROPDOWN,
                            sort=True,
                        )
                    ),
                    vol.Optional(
                        CONF_WIRED_CLIENTS_FILTER, default=conf_wired_clients_filter
                    ): SelectSelector(
                        SelectSelectorConfig(
                            options=VALUES_CLIENTS_FILTER,
                            translation_key="all",
                        )
                    ),
                    vol.Optional(
                        CONF_WIRELESS_CLIENTS, default=conf_wireless_clients
                    ): SelectSelector(
                        SelectSelectorConfig(
                            options=wireless_client_names,
                            multiple=True,
                            mode=SelectSelectorMode.DROPDOWN,
                            sort=True,
                        )
                    ),
                    vol.Optional(
                        CONF_WIRELESS_CLIENTS_FILTER,
                        default=conf_wireless_clients_filter,
                    ): SelectSelector(
                        SelectSelectorConfig(
                            options=VALUES_CLIENTS_FILTER,
                            translation_key="all",
                        )
                    ),
                }
                if network.premium_enabled:
                    conf_backup_networks = [
                        backup_network.name
                        for backup_network in network.backup_networks
                        if backup_network.id
                        in conf_resources.get(CONF_BACKUP_NETWORKS, [])
                    ]
                    backup_network_names = [
                        backup_network.name
                        for backup_network in network.backup_networks
                    ]
                    schema[
                        vol.Optional(CONF_BACKUP_NETWORKS, default=conf_backup_networks)
                    ] = SelectSelector(
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
        return None

    async def async_step_activity(self, user_input=None):
        """Async step activity."""
        if user_input is not None:
            target_network = self.user_input[CONF_NETWORKS][self.index]
            for network in self.response.networks:
                if network.id == target_network:
                    self.user_input[CONF_ACTIVITY][network.id] = {
                        CONF_ACTIVITY_NETWORK: user_input[CONF_ACTIVITY_NETWORK],
                        CONF_ACTIVITY_EEROS: user_input.get(CONF_ACTIVITY_EEROS, []),
                        CONF_ACTIVITY_PROFILES: user_input.get(
                            CONF_ACTIVITY_PROFILES, []
                        ),
                        CONF_ACTIVITY_CLIENTS: user_input.get(
                            CONF_ACTIVITY_CLIENTS, []
                        ),
                    }
                    self.index += 1

        if self.index == len(self.user_input[CONF_NETWORKS]):
            self.index = 0
            return await self.async_step_miscellaneous()
        if self.index == 0:
            self.user_input[CONF_ACTIVITY] = {}

        target_network = self.user_input[CONF_NETWORKS][self.index]
        for network in self.response.networks:
            if network.id == target_network:
                activity_options = ACTIVITIES_DEFAULT
                data_usage_options = ACTIVITIES_DATA_USAGE_DEFAULT
                if network.premium_enabled:
                    activity_options = ACTIVITIES_PREMIUM
                    data_usage_options = ACTIVITIES_DATA_USAGE_PREMIUM

                conf_activity = self.options.get(
                    CONF_ACTIVITY, self.data.get(CONF_ACTIVITY, {})
                ).get(network.id, {})

                conf_activity_network = conf_activity.get(CONF_ACTIVITY_NETWORK, [])
                conf_activity_eero = conf_activity.get(CONF_ACTIVITY_EEROS, [])
                conf_activity_profile = conf_activity.get(CONF_ACTIVITY_PROFILES, [])
                conf_activity_client = conf_activity.get(CONF_ACTIVITY_CLIENTS, [])

                data_schema = {
                    vol.Optional(
                        CONF_ACTIVITY_NETWORK, default=conf_activity_network
                    ): SelectSelector(
                        SelectSelectorConfig(
                            options=activity_options,
                            multiple=True,
                            mode=SelectSelectorMode.DROPDOWN,
                            translation_key="all",
                        )
                    ),
                }

                if self.user_input[CONF_RESOURCES][network.id][CONF_EEROS]:
                    data_schema[
                        vol.Optional(CONF_ACTIVITY_EEROS, default=conf_activity_eero)
                    ] = SelectSelector(
                        SelectSelectorConfig(
                            options=data_usage_options,
                            multiple=True,
                            mode=SelectSelectorMode.DROPDOWN,
                            translation_key="all",
                        )
                    )

                if self.user_input[CONF_RESOURCES][network.id][CONF_PROFILES]:
                    data_schema[
                        vol.Optional(
                            CONF_ACTIVITY_PROFILES, default=conf_activity_profile
                        )
                    ] = SelectSelector(
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
                        self.user_input[CONF_RESOURCES][network.id][
                            CONF_WIRELESS_CLIENTS
                        ],
                    ]
                ):
                    data_schema[
                        vol.Optional(
                            CONF_ACTIVITY_CLIENTS, default=conf_activity_client
                        )
                    ] = SelectSelector(
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
        return None

    async def async_step_miscellaneous(self, user_input=None):
        """Async step miscellaneous."""
        if user_input is not None:
            target_network = self.user_input[CONF_NETWORKS][self.index]
            for network in self.response.networks:
                if network.id == target_network:
                    self.user_input[CONF_MISCELLANEOUS][network.id] = {
                        CONF_CONSIDER_HOME: user_input[CONF_CONSIDER_HOME],
                        CONF_PREFIX_NETWORK_NAME: user_input[CONF_PREFIX_NETWORK_NAME],
                        CONF_SUFFIX_CONNECTION_TYPE: user_input[
                            CONF_SUFFIX_CONNECTION_TYPE
                        ],
                        CONF_SHOW_EERO_LOGO: user_input[CONF_SHOW_EERO_LOGO],
                    }
                    self.index += 1

        if self.index == len(self.user_input[CONF_NETWORKS]):
            self.index = 0
            if self.show_advanced_options:
                return await self.async_step_advanced()
            return self.async_create_entry(title="", data=self.user_input)
        if self.index == 0:
            self.user_input[CONF_MISCELLANEOUS] = {}

        target_network = self.user_input[CONF_NETWORKS][self.index]
        for network in self.response.networks:
            if network.id == target_network:
                conf_miscellaneous = self.options.get(
                    CONF_MISCELLANEOUS, self.data.get(CONF_MISCELLANEOUS, {})
                ).get(network.id, {})

                conf_consider_home = conf_miscellaneous.get(
                    CONF_CONSIDER_HOME, DEFAULT_CONSIDER_HOME
                )
                conf_prefix_network_name = conf_miscellaneous.get(
                    CONF_PREFIX_NETWORK_NAME, DEFAULT_PREFIX_NETWORK_NAME
                )
                conf_suffix_connection_type = conf_miscellaneous.get(
                    CONF_SUFFIX_CONNECTION_TYPE, DEFAULT_SUFFIX_CONNECTION_TYPE
                )
                conf_show_eero_logo = conf_miscellaneous.get(
                    CONF_SHOW_EERO_LOGO, DEFAULT_SHOW_EERO_LOGO
                )

                return self.async_show_form(
                    step_id="miscellaneous",
                    data_schema=vol.Schema(
                        {
                            vol.Optional(
                                CONF_CONSIDER_HOME, default=conf_consider_home
                            ): NumberSelector(
                                NumberSelectorConfig(
                                    min=MIN_CONSIDER_HOME,
                                    max=MAX_CONSIDER_HOME,
                                    step=STEP_CONSIDER_HOME,
                                    unit_of_measurement=UnitOfTime.MINUTES,
                                )
                            ),
                            vol.Optional(
                                CONF_PREFIX_NETWORK_NAME,
                                default=conf_prefix_network_name,
                            ): BooleanSelector(),
                            vol.Optional(
                                CONF_SUFFIX_CONNECTION_TYPE,
                                default=conf_suffix_connection_type,
                            ): BooleanSelector(),
                            vol.Optional(
                                CONF_SHOW_EERO_LOGO, default=conf_show_eero_logo
                            ): BooleanSelector(),
                        }
                    ),
                    description_placeholders={"network": network.name_unique},
                )
        return None

    async def async_step_advanced(self, user_input=None):
        """Handle a flow initialized by the user."""
        errors = {}

        if user_input:
            conf_scan_interval = user_input[CONF_SCAN_INTERVAL]
            conf_timeout = user_input[CONF_TIMEOUT]

            invalid_scan_interval_timeout = timedelta(
                seconds=conf_scan_interval
            ) <= timedelta(seconds=conf_timeout)

            if invalid_scan_interval_timeout:
                errors["base"] = "invalid_scan_interval_timeout"
            else:
                self.user_input[CONF_SAVE_RESPONSES] = user_input[CONF_SAVE_RESPONSES]
                self.user_input[CONF_SCAN_INTERVAL] = conf_scan_interval
                self.user_input[CONF_TIMEOUT] = conf_timeout
                return self.async_create_entry(title="", data=self.user_input)

        conf_save_responses = self.options.get(
            CONF_SAVE_RESPONSES,
            self.data.get(CONF_SAVE_RESPONSES, DEFAULT_SAVE_RESPONSES),
        )
        conf_scan_interval = self.options.get(
            CONF_SCAN_INTERVAL,
            self.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        )
        conf_timeout = self.options.get(
            CONF_TIMEOUT, self.data.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)
        )

        return self.async_show_form(
            step_id="advanced",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SAVE_RESPONSES, default=conf_save_responses
                    ): BooleanSelector(),
                    vol.Optional(
                        CONF_SCAN_INTERVAL, default=conf_scan_interval
                    ): NumberSelector(
                        NumberSelectorConfig(
                            min=MIN_SCAN_INTERVAL,
                            max=MAX_SCAN_INTERVAL,
                            step=STEP_SCAN_INTERVAL,
                            unit_of_measurement=UnitOfTime.SECONDS,
                        )
                    ),
                    vol.Optional(CONF_TIMEOUT, default=conf_timeout): NumberSelector(
                        NumberSelectorConfig(
                            min=MIN_TIMEOUT,
                            max=MAX_TIMEOUT,
                            step=STEP_TIMEOUT,
                            unit_of_measurement=UnitOfTime.SECONDS,
                        )
                    ),
                }
            ),
            errors=errors,
        )
