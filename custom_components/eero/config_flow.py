"""Adds config flow for Eero integration."""

import logging

import voluptuous as vol

from homeassistant import config_entries, exceptions
from homeassistant.const import CONF_NAME, CONF_SCAN_INTERVAL
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv

from .api import EeroAPI, EeroException
from .const import (
    CONF_CODE,
    CONF_EEROS,
    CONF_LOGIN,
    CONF_NETWORKS,
    CONF_PROFILES,
    CONF_SAVE_RESPONSES,
    CONF_TIMEOUT,
    CONF_USER_TOKEN,
    CONF_WIRED_CLIENTS,
    CONF_WIRELESS_CLIENTS,
    DATA_COORDINATOR,
    DEFAULT_SAVE_RESPONSES,
    DEFAULT_SCAN_INTERVAL,
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
            self.api = EeroAPI()

            try:
                self.response = await self.hass.async_add_executor_job(
                    self.api.login, user_input[CONF_LOGIN],
                )
            except EeroException as exception:
                _LOGGER.error(f"Status: {exception.status}, Error Message: {exception.error_message}")
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
                _LOGGER.error(f"Status: {exception.status}, Error Message: {exception.error_message}")
                errors["base"] = "invalid_code"

            await self.async_set_unique_id(self.response["log_id"].lower())
            self._abort_if_unique_id_configured()
            self.user_input[CONF_NAME] = self.response["name"]
            self.response = await self.hass.async_add_executor_job(self.api.update)
            return await self.async_step_networks()

        return self.async_show_form(
            step_id="verify",
            data_schema=vol.Schema({vol.Required(CONF_CODE): cv.string}),
            errors=errors,
        )

    async def async_step_networks(self, user_input=None):
        if user_input is not None:
            self.user_input[CONF_NETWORKS] = [network.id for network in self.response.networks if network.name in user_input[CONF_NETWORKS]]
            return await self.async_step_resources()

        network_names = sorted([network.name for network in self.response.networks])

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
            target_network_id = self.user_input[CONF_NETWORKS][self.index]
            for network in self.response.networks:
                if network.id == target_network_id:
                    self.user_input[CONF_EEROS] = [eero.id for eero in network.eeros if eero.name in user_input[CONF_EEROS]]
                    self.user_input[CONF_PROFILES] = [profile.id for profile in network.profiles if profile.name in user_input[CONF_PROFILES]]
                    self.user_input[CONF_WIRED_CLIENTS] = [client.id for client in network.clients if client.name_mac in user_input[CONF_WIRED_CLIENTS]]
                    self.user_input[CONF_WIRELESS_CLIENTS] = [client.id for client in network.clients if client.name_mac in user_input[CONF_WIRELESS_CLIENTS]]
                    self.index += 1

        if self.index == len(self.user_input[CONF_NETWORKS]):
            return self.async_create_entry(title=self.user_input[CONF_NAME], data=self.user_input)
        else:
            target_network_id = self.user_input[CONF_NETWORKS][self.index]
            for network in self.response.networks:
                if network.id == target_network_id:
                    target_network_name = network.name
                    eero_names = sorted(eero.name for eero in network.eeros)
                    profile_names = sorted(profile.name for profile in network.profiles)
                    wired_client_names = sorted(client.name_mac for client in network.clients if not client.wireless)
                    wireless_client_names = sorted(client.name_mac for client in network.clients if client.wireless)

        return self.async_show_form(
            step_id="resources",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_EEROS, default=eero_names): cv.multi_select(eero_names),
                    vol.Optional(CONF_PROFILES, default=profile_names): cv.multi_select(profile_names),
                    vol.Optional(CONF_WIRED_CLIENTS, default=[]): cv.multi_select(wired_client_names),
                    vol.Optional(CONF_WIRELESS_CLIENTS, default=[]): cv.multi_select(wireless_client_names),
                }
            ),
            description_placeholders={"network": target_network_name},
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
        self.coordinator = None
        self.config_entry = config_entry
        self.data = config_entry.data
        self.index = 0
        self.options = config_entry.options
        self.user_input = {}

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        self.coordinator = self.hass.data[DOMAIN][self.config_entry.entry_id][DATA_COORDINATOR]
        return await self.async_step_networks()

    async def async_step_networks(self, user_input=None):
        """Handle a flow initialized by the user."""
        if user_input is not None:
            self.user_input[CONF_NETWORKS] = [network.id for network in self.coordinator.data.networks if network.name in user_input[CONF_NETWORKS]]
            return await self.async_step_resources()

        conf_networks = [network.name for network in self.coordinator.data.networks if network.id in self.options.get(CONF_NETWORKS, self.data[CONF_NETWORKS])]
        network_names = sorted([network.name for network in self.coordinator.data.networks])

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
            target_network_id = self.user_input[CONF_NETWORKS][self.index]
            for network in self.coordinator.data.networks:
                if network.id == target_network_id:
                    self.user_input[CONF_EEROS] = [eero.id for eero in network.eeros if eero.name in user_input[CONF_EEROS]]
                    self.user_input[CONF_PROFILES] = [profile.id for profile in network.profiles if profile.name in user_input[CONF_PROFILES]]
                    self.user_input[CONF_WIRED_CLIENTS] = [client.id for client in network.clients if client.name_mac in user_input[CONF_WIRED_CLIENTS]]
                    self.user_input[CONF_WIRELESS_CLIENTS] = [client.id for client in network.clients if client.name_mac in user_input[CONF_WIRELESS_CLIENTS]]
                    self.index += 1

        if self.index == len(self.user_input[CONF_NETWORKS]):
            if self.show_advanced_options:
                return await self.async_step_advanced()
            return self.async_create_entry(title="", data=self.user_input)
        else:
            target_network_id = self.user_input[CONF_NETWORKS][self.index]
            for network in self.coordinator.data.networks:
                if network.id == target_network_id:
                    target_network_name = network.name

                    conf_eeros = [eero.name for eero in network.eeros if eero.id in self.options.get(CONF_EEROS, self.data.get(CONF_EEROS, []))]
                    conf_profiles = [profile.name for profile in network.profiles if profile.id in self.options.get(CONF_PROFILES, self.data.get(CONF_PROFILES, []))]
                    conf_wired_clients = [client.name_mac for client in network.clients if client.id in self.options.get(CONF_WIRED_CLIENTS, self.data.get(CONF_WIRED_CLIENTS, []))]
                    conf_wireless_clients = [client.name_mac for client in network.clients if client.id in self.options.get(CONF_WIRELESS_CLIENTS, self.data.get(CONF_WIRELESS_CLIENTS, []))]

                    eero_names = sorted(eero.name for eero in network.eeros)
                    profile_names = sorted(profile.name for profile in network.profiles)
                    wired_client_names = sorted(client.name_mac for client in network.clients if not client.wireless)
                    wireless_client_names = sorted(client.name_mac for client in network.clients if client.wireless)

        return self.async_show_form(
            step_id="resources",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_EEROS, default=conf_eeros): cv.multi_select(eero_names),
                    vol.Optional(CONF_PROFILES, default=conf_profiles): cv.multi_select(profile_names),
                    vol.Optional(CONF_WIRED_CLIENTS, default=conf_wired_clients): cv.multi_select(wired_client_names),
                    vol.Optional(CONF_WIRELESS_CLIENTS, default=conf_wireless_clients): cv.multi_select(wireless_client_names),
                }
            ),
            description_placeholders={"network": target_network_name},
        )

    async def async_step_advanced(self, user_input=None):
        """Handle a flow initialized by the user."""
        if user_input is not None:
            self.user_input[CONF_SAVE_RESPONSES] = user_input[CONF_SAVE_RESPONSES]
            self.user_input[CONF_SCAN_INTERVAL] = user_input[CONF_SCAN_INTERVAL]
            self.user_input[CONF_TIMEOUT] = user_input[CONF_TIMEOUT]
            return self.async_create_entry(title="", data=self.user_input)

        default_save_responses = self.options.get(CONF_SAVE_RESPONSES, DEFAULT_SAVE_RESPONSES)
        default_scan_interval = self.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        default_timeout = self.options.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)

        return self.async_show_form(
            step_id="advanced",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_SAVE_RESPONSES, default=default_save_responses): cv.boolean,
                    vol.Optional(CONF_SCAN_INTERVAL, default=default_scan_interval): vol.In(VALUES_SCAN_INTERVAL),
                    vol.Optional(CONF_TIMEOUT, default=default_timeout): vol.In(VALUES_TIMEOUT),
                }
            ),
        )
