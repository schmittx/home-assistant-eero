"""Adds config flow for Eero integration."""

import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME, CONF_SCAN_INTERVAL
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv

from .api import EeroAPI, EeroException
from .const import (
    ACTIVITIES_DEFAULT,
    ACTIVITIES_DATA_USAGE_DEFAULT,
    ACTIVITIES_DATA_USAGE_PREMIUM,
    ACTIVITIES_PREMIUM,
    ACTIVITY_MAP_TO_EERO,
    ACTIVITY_MAP_TO_HASS,
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
    CONF_PROFILES,
    CONF_SAVE_RESPONSES,
    CONF_SHOW_EERO_LOGO,
    CONF_TIMEOUT,
    CONF_USER_TOKEN,
    CONF_WIRED_CLIENTS,
    CONF_WIRELESS_CLIENTS,
    DATA_API,
    DEFAULT_SAVE_RESPONSES,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SHOW_EERO_LOGO,
    DEFAULT_TIMEOUT,
    DOMAIN,
    VALUES_SCAN_INTERVAL,
    VALUES_TIMEOUT,
)

_LOGGER = logging.getLogger(__name__)


class EeroConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Eero integration."""

    VERSION = 1
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
                _LOGGER.error(f"Status: {exception.status_code}, Error Message: {exception.error_message}")
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
                _LOGGER.error(f"Status: {exception.status_code}, Error Message: {exception.error_message}")
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

        network_names = sorted([network.name_unique for network in self.response.networks])

        return self.async_show_form(
            step_id="networks",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NETWORKS, default=network_names): cv.multi_select(network_names),
                }
            ),
        )

    async def async_step_resources(self, user_input=None):
        if user_input is not None:
            target_network = self.user_input[CONF_NETWORKS][self.index]
            for network in self.response.networks:
                if network.id == target_network:
                    self.user_input[CONF_EEROS].extend([eero.id for eero in network.eeros if eero.name in user_input[CONF_EEROS]])
                    self.user_input[CONF_PROFILES].extend([profile.id for profile in network.profiles if profile.name in user_input[CONF_PROFILES]])
                    self.user_input[CONF_WIRED_CLIENTS].extend([client.id for client in network.clients if client.name_mac in user_input[CONF_WIRED_CLIENTS]])
                    self.user_input[CONF_WIRELESS_CLIENTS].extend([client.id for client in network.clients if client.name_mac in user_input[CONF_WIRELESS_CLIENTS]])
                    if network.premium_enabled:
                        self.user_input[CONF_BACKUP_NETWORKS].extend([backup_network.id for backup_network in network.backup_networks if backup_network.name in user_input[CONF_BACKUP_NETWORKS]])
                    self.index += 1

        if self.index == len(self.user_input[CONF_NETWORKS]):
            self.index = 0
            return await self.async_step_activity()
        elif self.index == 0:
            for conf in [CONF_BACKUP_NETWORKS, CONF_EEROS, CONF_PROFILES, CONF_WIRED_CLIENTS, CONF_WIRELESS_CLIENTS]:
                self.user_input[conf] = []

        target_network = self.user_input[CONF_NETWORKS][self.index]
        for network in self.response.networks:
            if network.id == target_network:
                eero_names = sorted(eero.name for eero in network.eeros)
                profile_names = sorted(profile.name for profile in network.profiles)
                wired_client_names = sorted(client.name_mac for client in network.clients if not client.wireless)
                wireless_client_names = sorted(client.name_mac for client in network.clients if client.wireless)
                schema = {
                    vol.Required(CONF_EEROS, default=eero_names): cv.multi_select(eero_names),
                    vol.Required(CONF_PROFILES, default=profile_names): cv.multi_select(profile_names),
                    vol.Required(CONF_WIRED_CLIENTS, default=[]): cv.multi_select(wired_client_names),
                    vol.Required(CONF_WIRELESS_CLIENTS, default=[]): cv.multi_select(wireless_client_names),
                }
                if network.premium_enabled:
                    backup_network_names = sorted(backup_network.name for backup_network in network.backup_networks)
                    schema[vol.Required(CONF_BACKUP_NETWORKS, default=backup_network_names)] = cv.multi_select(backup_network_names)

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
                            CONF_ACTIVITY_NETWORK: [ACTIVITY_MAP_TO_EERO[activity] for activity in user_input[CONF_ACTIVITY_NETWORK]],
                            CONF_ACTIVITY_EEROS: [ACTIVITY_MAP_TO_EERO[activity] for activity in user_input.get(CONF_ACTIVITY_EEROS, [])],
                            CONF_ACTIVITY_PROFILES: [ACTIVITY_MAP_TO_EERO[activity] for activity in user_input.get(CONF_ACTIVITY_PROFILES, [])],
                            CONF_ACTIVITY_CLIENTS: [ACTIVITY_MAP_TO_EERO[activity] for activity in user_input.get(CONF_ACTIVITY_CLIENTS, [])],
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
                        vol.Required(CONF_ACTIVITY_NETWORK, default=[]): cv.multi_select(activity_options),
                }

                if any([bool(eero.id in self.user_input[CONF_EEROS]) for eero in network.eeros]):
                    data_schema[vol.Required(CONF_ACTIVITY_EEROS, default=[])] = cv.multi_select(data_usage_options)

                if any([bool(profile.id in self.user_input[CONF_PROFILES]) for profile in network.profiles]):
                    data_schema[vol.Required(CONF_ACTIVITY_PROFILES, default=[])] = cv.multi_select(activity_options)

                if any([bool(client.id in self.user_input[CONF_WIRED_CLIENTS] + self.user_input[CONF_WIRELESS_CLIENTS]) for client in network.clients]):
                    data_schema[vol.Required(CONF_ACTIVITY_CLIENTS, default=[])] = cv.multi_select(activity_options)

                return self.async_show_form(
                    step_id="activity",
                    data_schema=vol.Schema(data_schema),
                    description_placeholders={"network": network.name_unique},
                )

    async def async_step_advanced(self, user_input=None):
        """Handle a flow initialized by the user."""
        if user_input is not None:
            self.user_input[CONF_SAVE_RESPONSES] = user_input[CONF_SAVE_RESPONSES]
            self.user_input[CONF_SHOW_EERO_LOGO] = user_input[CONF_SHOW_EERO_LOGO]
            self.user_input[CONF_SCAN_INTERVAL] = user_input[CONF_SCAN_INTERVAL]
            self.user_input[CONF_TIMEOUT] = user_input[CONF_TIMEOUT]
            return self.async_create_entry(title=self.user_input[CONF_NAME], data=self.user_input)

        return self.async_show_form(
            step_id="advanced",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_SAVE_RESPONSES, default=DEFAULT_SAVE_RESPONSES): cv.boolean,
                    vol.Required(CONF_SHOW_EERO_LOGO, default=DEFAULT_SHOW_EERO_LOGO): cv.boolean,
                    vol.Required(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.In(VALUES_SCAN_INTERVAL),
                    vol.Required(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): vol.In(VALUES_TIMEOUT),
                }
            ),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Eero options callback."""
        return EeroOptionsFlowHandler(config_entry)


class EeroOptionsFlowHandler(config_entries.OptionsFlow):
    """Config flow options for Eero."""

    def __init__(self, config_entry):
        """Initialize Eero options flow."""
        self.api = None
        self.config_entry = config_entry
        self.data = config_entry.data
        self.index = 0
        self.options = config_entry.options
        self.response = None
        self.user_input = {}

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
        network_names = sorted([network.name_unique for network in self.response.networks])

        return self.async_show_form(
            step_id="networks",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NETWORKS, default=conf_networks): cv.multi_select(network_names),
                }
            ),
        )

    async def async_step_resources(self, user_input=None):
        """Handle a flow initialized by the user."""
        if user_input is not None:
            target_network = self.user_input[CONF_NETWORKS][self.index]
            for network in self.response.networks:
                if network.id == target_network:
                    self.user_input[CONF_EEROS].extend([eero.id for eero in network.eeros if eero.name in user_input[CONF_EEROS]])
                    self.user_input[CONF_PROFILES].extend([profile.id for profile in network.profiles if profile.name in user_input[CONF_PROFILES]])
                    self.user_input[CONF_WIRED_CLIENTS].extend([client.id for client in network.clients if client.name_mac in user_input[CONF_WIRED_CLIENTS]])
                    self.user_input[CONF_WIRELESS_CLIENTS].extend([client.id for client in network.clients if client.name_mac in user_input[CONF_WIRELESS_CLIENTS]])
                    if network.premium_enabled:
                        self.user_input[CONF_BACKUP_NETWORKS].extend([backup_network.id for backup_network in network.backup_networks if backup_network.name in user_input[CONF_BACKUP_NETWORKS]])
                    self.index += 1

        if self.index == len(self.user_input[CONF_NETWORKS]):
            self.index = 0
            return await self.async_step_activity()
        elif self.index == 0:
            for conf in [CONF_BACKUP_NETWORKS, CONF_EEROS, CONF_PROFILES, CONF_WIRED_CLIENTS, CONF_WIRELESS_CLIENTS]:
                self.user_input[conf] = []

        target_network = self.user_input[CONF_NETWORKS][self.index]
        for network in self.response.networks:
            if network.id == target_network:
                conf_eeros = [eero.name for eero in network.eeros if eero.id in self.options.get(CONF_EEROS, self.data.get(CONF_EEROS, []))]
                conf_profiles = [profile.name for profile in network.profiles if profile.id in self.options.get(CONF_PROFILES, self.data.get(CONF_PROFILES, []))]
                conf_wired_clients = [client.name_mac for client in network.clients if client.id in self.options.get(CONF_WIRED_CLIENTS, self.data.get(CONF_WIRED_CLIENTS, []))]
                conf_wireless_clients = [client.name_mac for client in network.clients if client.id in self.options.get(CONF_WIRELESS_CLIENTS, self.data.get(CONF_WIRELESS_CLIENTS, []))]

                eero_names = sorted(eero.name for eero in network.eeros)
                profile_names = sorted(profile.name for profile in network.profiles)
                wired_client_names = sorted(client.name_mac for client in network.clients if not client.wireless)
                wireless_client_names = sorted(client.name_mac for client in network.clients if client.wireless)
                schema = {
                    vol.Required(CONF_EEROS, default=conf_eeros): cv.multi_select(eero_names),
                    vol.Required(CONF_PROFILES, default=conf_profiles): cv.multi_select(profile_names),
                    vol.Required(CONF_WIRED_CLIENTS, default=conf_wired_clients): cv.multi_select(wired_client_names),
                    vol.Required(CONF_WIRELESS_CLIENTS, default=conf_wireless_clients): cv.multi_select(wireless_client_names),
                }
                if network.premium_enabled:
                    conf_backup_networks = [backup_network.name for backup_network in network.backup_networks if backup_network.id in self.options.get(CONF_BACKUP_NETWORKS, self.data.get(CONF_BACKUP_NETWORKS, []))]
                    backup_network_names = sorted(backup_network.name for backup_network in network.backup_networks)
                    schema[vol.Required(CONF_BACKUP_NETWORKS, default=conf_backup_networks)] = cv.multi_select(backup_network_names)

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
                            CONF_ACTIVITY_NETWORK: [ACTIVITY_MAP_TO_EERO[activity] for activity in user_input[CONF_ACTIVITY_NETWORK]],
                            CONF_ACTIVITY_EEROS: [ACTIVITY_MAP_TO_EERO[activity] for activity in user_input.get(CONF_ACTIVITY_EEROS, [])],
                            CONF_ACTIVITY_PROFILES: [ACTIVITY_MAP_TO_EERO[activity] for activity in user_input.get(CONF_ACTIVITY_PROFILES, [])],
                            CONF_ACTIVITY_CLIENTS: [ACTIVITY_MAP_TO_EERO[activity] for activity in user_input.get(CONF_ACTIVITY_CLIENTS, [])],
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
                conf_activity_network = [ACTIVITY_MAP_TO_HASS[activity] for activity in conf_activity.get(CONF_ACTIVITY_NETWORK, [])]
                conf_activity_eero = [ACTIVITY_MAP_TO_HASS[activity] for activity in conf_activity.get(CONF_ACTIVITY_EEROS, [])]
                conf_activity_profile = [ACTIVITY_MAP_TO_HASS[activity] for activity in conf_activity.get(CONF_ACTIVITY_PROFILES, [])]
                conf_activity_client = [ACTIVITY_MAP_TO_HASS[activity] for activity in conf_activity.get(CONF_ACTIVITY_CLIENTS, [])]

                data_schema = {
                        vol.Required(CONF_ACTIVITY_NETWORK, default=conf_activity_network): cv.multi_select(activity_options),
                }

                if any([bool(eero.id in self.user_input[CONF_EEROS]) for eero in network.eeros]):
                    data_schema[vol.Required(CONF_ACTIVITY_EEROS, default=conf_activity_eero)] = cv.multi_select(data_usage_options)

                if any([bool(profile.id in self.user_input[CONF_PROFILES]) for profile in network.profiles]):
                    data_schema[vol.Required(CONF_ACTIVITY_PROFILES, default=conf_activity_profile)] = cv.multi_select(activity_options)

                if any([bool(client.id in self.user_input[CONF_WIRED_CLIENTS] + self.user_input[CONF_WIRELESS_CLIENTS]) for client in network.clients]):
                    data_schema[vol.Required(CONF_ACTIVITY_CLIENTS, default=conf_activity_client)] = cv.multi_select(activity_options)

                return self.async_show_form(
                    step_id="activity",
                    data_schema=vol.Schema(data_schema),
                    description_placeholders={"network": network.name_unique},
                )

    async def async_step_advanced(self, user_input=None):
        """Handle a flow initialized by the user."""
        if user_input is not None:
            self.user_input[CONF_SAVE_RESPONSES] = user_input[CONF_SAVE_RESPONSES]
            self.user_input[CONF_SHOW_EERO_LOGO] = user_input[CONF_SHOW_EERO_LOGO]
            self.user_input[CONF_SCAN_INTERVAL] = user_input[CONF_SCAN_INTERVAL]
            self.user_input[CONF_TIMEOUT] = user_input[CONF_TIMEOUT]
            return self.async_create_entry(title="", data=self.user_input)

        default_save_responses = self.options.get(CONF_SAVE_RESPONSES, DEFAULT_SAVE_RESPONSES)
        default_show_eero_logo = self.options.get(CONF_SHOW_EERO_LOGO, DEFAULT_SHOW_EERO_LOGO)
        default_scan_interval = self.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        default_timeout = self.options.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)

        return self.async_show_form(
            step_id="advanced",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_SAVE_RESPONSES, default=default_save_responses): cv.boolean,
                    vol.Required(CONF_SHOW_EERO_LOGO, default=default_show_eero_logo): cv.boolean,
                    vol.Required(CONF_SCAN_INTERVAL, default=default_scan_interval): vol.In(VALUES_SCAN_INTERVAL),
                    vol.Required(CONF_TIMEOUT, default=default_timeout): vol.In(VALUES_TIMEOUT),
                }
            ),
        )
