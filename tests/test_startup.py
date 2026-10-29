"""Startup regressions using real Home Assistant lifecycle/coordinator objects."""

import asyncio
from copy import deepcopy
import inspect
import logging
from pathlib import Path
import sys
import tempfile
from types import MappingProxyType, SimpleNamespace
import unittest
from unittest.mock import AsyncMock, Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from homeassistant.config_entries import ConfigEntries, ConfigEntry, ConfigEntryState
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.core import HomeAssistant
from homeassistant.helpers import frame

from custom_components import eero
from custom_components.eero import sensor
from custom_components.eero.api.account import EeroAccount


class StartupTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.hass = HomeAssistant(self.directory.name)
        if hasattr(frame, "async_setup"):
            frame.async_setup(self.hass)
        self.hass.config_entries = ConfigEntries(self.hass, {})
        self.integration = SimpleNamespace(
            domain="eero",
            logger=logging.getLogger("homeassistant.config_entries"),
            async_get_component=AsyncMock(return_value=eero),
            async_get_platform=AsyncMock(),
        )
        self.entry = self.make_entry()
        self.api = Mock()
        self.client = SimpleNamespace(id="client", wireless=True)
        self.node = SimpleNamespace(id="node", status="green", is_network=False)
        self.network = SimpleNamespace(
            id="network",
            name="Test network",
            status="connected",
            is_network=True,
            premium_enabled=False,
            clients=[self.client],
            eeros=[self.node],
            backup_networks=[],
            profiles=[],
            resources=[self.node, self.client],
        )
        self.account = SimpleNamespace(networks=[self.network])
        self.entities = []
        self.forward = AsyncMock(side_effect=self.forward_sensors)
        patches = [
            patch.object(eero, "EeroAPI", return_value=self.api),
            patch.object(eero.dr, "async_get", return_value=Mock()),
            patch.object(eero.er, "async_get", return_value=Mock()),
            patch.object(eero.dr, "async_entries_for_config_entry", return_value=[]),
            # This fixture already has version-3 options. Skip loader discovery,
            # retaining the real entry setup, retry and coordinator behavior.
            patch.object(ConfigEntry, "async_migrate", new=AsyncMock(return_value=True)),
            patch.object(ConfigEntries, "async_forward_entry_setups", self.forward),
        ]
        for item in patches:
            item.start()
            self.addCleanup(item.stop)

    def make_entry(self, networks=None):
        if networks is None:
            networks = ["network"]
        values = dict(
            domain="eero",
            title="Test account",
            version=3,
            minor_version=0,
            source="user",
            unique_id="test-account",
            discovery_keys=MappingProxyType({}),
            data={"name": "Test account", "user_token": "synthetic"},
            options={
                "networks": networks,
                "resources": {
                    key: {
                        "backup_networks": [],
                        "eeros": ["node"],
                        "profiles": [],
                        "wired_clients": [],
                        "wired_clients_filter": "include",
                        "wireless_clients": [],
                        "wireless_clients_filter": "include",
                    }
                    for key in networks
                },
                "activity": {key: {} for key in networks},
                "miscellaneous": {
                    key: {
                        "consider_home": 0,
                        "prefix_network_name": True,
                        "suffix_connection_type": True,
                        "show_eero_logo": False,
                    }
                    for key in networks
                },
                "scan_interval": 120,
                "timeout": 30,
            },
        )
        # Added after the documented minimum HA version (2025.2).
        if "subentries_data" in inspect.signature(ConfigEntry).parameters:
            values["subentries_data"] = []
        entry = ConfigEntry(**values)
        entry.supports_unload = True
        entry.supports_remove_device = False
        entry._integration_for_domain = self.integration
        self.hass.config_entries._entries[entry.entry_id] = entry
        return entry

    async def asyncTearDown(self):
        self.entry.async_cancel_retry_setup()
        await self.hass.async_stop(force=True)

    async def forward_sensors(self, entry, platforms):
        runtime = self.hass.data["eero"][entry.entry_id]
        self.assertTrue(runtime["coordinator"].last_update_success)
        self.assertIs(runtime["coordinator"].config_entry, entry)
        await sensor.async_setup_entry(self.hass, entry, self.entities.extend)
        self.assertEqual(platforms, eero.PLATFORMS)

    def assert_populated_once(self):
        self.assertEqual(self.entry.state, ConfigEntryState.LOADED)
        self.forward.assert_awaited_once()
        self.assertEqual(len(self.entry.update_listeners), 1)
        self.assertEqual(
            [item.unique_id for item in self.entities],
            ["network-status", "network-node-status"],
        )
        self.assertEqual(
            [item.native_value for item in self.entities], ["connected", "green"]
        )
        coordinator = self.hass.data["eero"][self.entry.entry_id]["coordinator"]
        self.assertIs(coordinator.data, self.account)
        self.assertEqual(coordinator.data.networks[0].clients, [self.client])

    async def retry_after(self, initial_result):
        self.api.update.side_effect = [initial_result, self.account]
        before = deepcopy((dict(self.entry.data), dict(self.entry.options)))
        with self.assertLogs(level="DEBUG") as captured:
            await self.entry.async_setup_locked(self.hass, self.integration)
        self.assertEqual(self.entry.state, ConfigEntryState.SETUP_RETRY)
        self.assertNotIn(self.entry.entry_id, self.hass.data.get("eero", {}))
        self.assertEqual(len(self.entry.update_listeners), 0)
        self.forward.assert_not_awaited()
        self.assertNotIn("synthetic-provider-detail", "\n".join(captured.output))

        # Invoke HA's registered startup callback, not a manual integration reload.
        self.hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
        for _ in range(200):
            await asyncio.sleep(0.01)
            if self.entry.state == ConfigEntryState.LOADED:
                break
        self.assert_populated_once()
        self.assertEqual(self.api.update.call_count, 2)
        self.assertEqual((dict(self.entry.data), dict(self.entry.options)), before)

        # A redundant native setup request must not duplicate platforms/listeners.
        await self.entry.async_setup_locked(self.hass, self.integration)
        self.assert_populated_once()
        self.assertEqual(self.api.update.call_count, 2)

    async def test_provider_failure_then_native_startup_retry(self):
        # The provider exception logs at construction. Only setup/retry logging
        # is under test here; no real response or credential is used.
        with self.assertLogs("custom_components.eero.api", level="WARNING"):
            failure = eero.EeroException(error="synthetic-provider-detail")
        await self.retry_after(failure)

    async def test_timeout_then_native_startup_retry(self):
        await self.retry_after(TimeoutError())

    async def test_none_then_native_startup_retry(self):
        await self.retry_after(None)

    async def test_empty_initial_account_then_native_startup_retry(self):
        # EeroAPI.update can swallow a provider failure and return its initial data.
        await self.retry_after(EeroAccount(self.api, {}))

    async def test_successful_first_refresh(self):
        self.api.update.return_value = self.account
        await self.entry.async_setup_locked(self.hass, self.integration)
        self.assert_populated_once()

    async def test_nonempty_cached_account_remains_accepted(self):
        self.api.update.side_effect = [self.account, self.account]
        await self.entry.async_setup_locked(self.hass, self.integration)
        coordinator = self.hass.data["eero"][self.entry.entry_id]["coordinator"]
        await coordinator.async_refresh()
        self.assert_populated_once()
        self.assertEqual(self.api.update.call_count, 2)
        self.assertTrue(coordinator.last_update_success)

    async def test_intentionally_empty_selection(self):
        self.entry = self.make_entry(networks=[])
        self.api.update.return_value = EeroAccount(self.api, {})
        await self.entry.async_setup_locked(self.hass, self.integration)
        self.assertEqual(self.entry.state, ConfigEntryState.LOADED)
        self.forward.assert_awaited_once()
        self.assertEqual(self.entities, [])


if __name__ == "__main__":
    unittest.main()
