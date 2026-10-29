"""Keep legacy selected clients through migration and setup using real registries."""

from copy import deepcopy
from attr import asdict
import inspect
import logging
from pathlib import Path
import sys
import tempfile
from types import MappingProxyType, SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from homeassistant.config_entries import ConfigEntries, ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar, frame
from custom_components import eero
from custom_components.eero import binary_sensor, sensor


def make_entry(**values):
    """Support current and minimum-supported HA constructor signatures."""
    if "subentries_data" in inspect.signature(ConfigEntry).parameters:
        values["subentries_data"] = []
    return ConfigEntry(**values)


def make_device(registry, **values):
    """Resolve the parent through the supported HA registry API."""
    if (
        "via_device_id" in values
        and "via_device_id"
        not in inspect.signature(registry.async_get_or_create).parameters
    ):
        parent = registry.async_get(values.pop("via_device_id"))
        values["via_device"] = next(i for i in parent.identifiers if i[0] == "eero")
    return registry.async_get_or_create(**values)


async def load_registry(module, hass):
    """Use an empty registry in each supported HA version."""
    kwargs = (
        {"load_empty": True}
        if "load_empty" in inspect.signature(module.async_load).parameters
        else {}
    )
    await module.async_load(hass, **kwargs)


class SyntheticAPI:
    def __init__(self):
        self.result = None

    def update(self, *args):
        return self.result


class RegistryFixture(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.hass = HomeAssistant(self.directory.name)
        if hasattr(frame, "async_setup"):
            frame.async_setup(self.hass)
        self.hass.data["integrations"] = {}
        self.hass.config_entries = ConfigEntries(self.hass, {})
        self.entry = make_entry(
            domain="eero",
            title="Synthetic",
            version=1,
            minor_version=1,
            source="user",
            unique_id="fixture",
            discovery_keys=MappingProxyType({}),
            data={"name": "Fixture", "user_token": "synthetic", "networks": ["123"]},
            options={
                "networks": ["123"],
                "eeros": ["456"],
                "wireless_clients": ["789"],
                "wired_clients": [],
                "activity": {"123": {}},
                "scan_interval": 120,
                "timeout": 30,
                "prefix_network_name": True,
            },
        )
        self.hass.config_entries._entries[self.entry.entry_id] = self.entry
        self.entry.supports_unload = True
        self.entry.supports_remove_device = False

        async def component():
            return eero

        async def platform(*args):
            return None

        self.integration = SimpleNamespace(
            domain="eero",
            logger=logging.getLogger("homeassistant.config_entries"),
            async_get_component=component,
            async_get_platform=platform,
        )
        self.entry._integration_for_domain = self.integration
        self.api = SyntheticAPI()
        self.client = SimpleNamespace(
            id="789", wireless=True, name_mac="Phone (synthetic)"
        )
        self.node = SimpleNamespace(
            id="456", name="Node", status="green", is_network=False
        )
        self.network = SimpleNamespace(
            id="123",
            name="Fixture",
            name_unique="Fixture",
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
        if hasattr(eero.dr, "async_setup"):
            eero.dr.async_setup(self.hass)
        await load_registry(eero.dr, self.hass)
        await load_registry(eero.er, self.hass)
        self.registry = eero.dr.async_get(self.hass)
        net = make_device(
            self.registry,
            config_entry_id=self.entry.entry_id,
            identifiers={("eero", "123")},
            name="Fixture",
            model="Network",
        )
        self.devices = [net]
        for label, id, model in [
            ("Node", "456", "eero Pro 6E"),
            ("Phone", "789", "Client (Wireless)"),
        ]:
            self.devices.append(
                make_device(
                    self.registry,
                    config_entry_id=self.entry.entry_id,
                    identifiers={("eero", id)},
                    via_device_id=net.id,
                    name=label,
                    model=model,
                )
            )
        self.forward_calls = 0

        async def forward(manager, entry, platforms):
            self.forward_calls += 1
            await self.forward_sensors(entry, platforms)

        self.entities = []
        for p in [
            patch.object(eero, "EeroAPI", new=lambda **kwargs: self.api),
            # Storage notification/flush belongs to full HA bootstrap, absent here.
            patch.object(
                ConfigEntries,
                (
                    "_async_save_and_notify"
                    if hasattr(ConfigEntries, "_async_save_and_notify")
                    else "_async_schedule_save"
                ),
                new=lambda *args: None,
            ),
            patch.object(ConfigEntries, "async_forward_entry_setups", new=forward),
        ]:
            p.start()
            self.addCleanup(p.stop)

    async def asyncTearDown(self):
        self.entry.async_cancel_retry_setup()
        await self.hass.async_stop(force=True)

    async def forward_sensors(self, entry, platforms):
        await sensor.async_setup_entry(self.hass, entry, self.entities.extend)


class ClientMigrationTests(RegistryFixture):
    # Only the named migration cases below are loaded by this file's runner.
    async def asyncSetUp(self):
        await super().asyncSetUp()
        await load_registry(ar, self.hass)
        self.area = ar.async_get(self.hass).async_create("Synthetic room")
        self.wired = make_device(
            self.registry,
            config_entry_id=self.entry.entry_id,
            identifiers={("eero", "790")},
            connections={("mac", "00:00:00:00:00:02")},
            via_device_id=self.devices[0].id,
            model="Client",
            name="Wired fixture",
        )
        self.phone = self.devices[-1]
        for device in (self.phone, self.wired):
            self.registry.async_update_device(
                device.id,
                model="Client",
                area_id=self.area.id,
                name_by_user="Custom fixture",
            )
        self.registry.async_update_device(
            self.wired.id, disabled_by=eero.dr.DeviceEntryDisabler.USER
        )
        self.phone = self.registry.async_get(self.phone.id)
        self.wired = self.registry.async_get(self.wired.id)
        self.er = eero.er.async_get(self.hass)
        self.entities_before = []
        for device, resource_id in ((self.phone, "789"), (self.wired, "790")):
            for key, disabled, hidden in (
                ("connected", None, None),
                (
                    "blocked",
                    eero.er.RegistryEntryDisabler.USER,
                    eero.er.RegistryEntryHider.USER,
                ),
            ):
                self.entities_before.append(
                    self.er.async_get_or_create(
                        "binary_sensor",
                        "eero",
                        f"123-{resource_id}-{key}",
                        config_entry=self.entry,
                        device_id=device.id,
                        suggested_object_id=f"fixture_{resource_id}_{key}",
                        disabled_by=disabled
                        or (
                            eero.er.RegistryEntryDisabler.DEVICE
                            if device.disabled_by
                            else None
                        ),
                        hidden_by=hidden,
                        original_name="Synthetic client",
                    )
                )
        await self.hass.async_block_till_done()
        self.entities_before = [
            self.er.async_get(e.entity_id) for e in self.entities_before
        ]
        self.flat = {
            "networks": ["123"],
            "eeros": ["456"],
            "wireless_clients": ["789"],
            "wired_clients": ["790"],
            "activity": {"123": {}},
            "scan_interval": 120,
            "timeout": 30,
            "prefix_network_name": True,
        }
        self.reset_v1()
        self.api.result = self.account

    def reset_v1(self, *, data_selections=False, nested=False):
        data = {"name": "Fixture", "user_token": "synthetic", "networks": ["123"]}
        options = deepcopy(self.flat)
        if nested:
            options["resources"] = {
                "123": {
                    k: options.pop(k)
                    for k in ("eeros", "wired_clients", "wireless_clients")
                }
            }
        if data_selections:
            data.update(options)
            options = {}
        self.hass.config_entries.async_update_entry(
            self.entry, data=data, options=options, version=1
        )

    async def migrate(self):
        self.assertTrue(await eero.async_migrate_entry(self.hass, self.entry))
        self.assertEqual(self.entry.version, 3)

    async def setup_and_reload(self):
        # Actual Eero setup/cleanup, API update and sensor construction. Provider,
        # loader/storage and HA platform scheduling remain isolated by base fixture.
        self.assertTrue(await eero.async_setup_entry(self.hass, self.entry))
        with patch.object(
            type(self.hass.config_entries),
            "async_unload_platforms",
            new=AsyncMock(return_value=True),
        ):
            self.assertTrue(await eero.async_unload_entry(self.hass, self.entry))
        self.assertTrue(await eero.async_setup_entry(self.hass, self.entry))

    def assert_preserved(self, before):
        for previous, expected_model in zip(
            before, ("Client (Wireless)", "Client (Wired)")
        ):
            current = self.registry.async_get(previous.id)
            self.assertIsNotNone(current, "Selected legacy client was deleted")
            expected = asdict(previous)
            actual = asdict(current)
            expected["model"] = expected_model
            # HA records the time of the legitimate label update.
            expected["modified_at"] = actual["modified_at"]
            self.assertEqual(actual, expected)
        for entity in self.entities_before:
            self.assertEqual(self.er.async_get(entity.entity_id), entity)

    async def test_selected_legacy_clients_keep_every_registry_field(self):
        before = (self.phone, self.wired)
        await self.migrate()
        self.assert_preserved(before)
        migrated = deepcopy((dict(self.entry.data), dict(self.entry.options)))
        await self.migrate()
        await self.setup_and_reload()
        self.assert_preserved(before)
        self.assertEqual(migrated, (dict(self.entry.data), dict(self.entry.options)))
        self.assertEqual(self.entry.data["user_token"], "synthetic")
        self.assertEqual(
            self.entry.options["resources"]["123"]["wireless_clients"], ["789"]
        )
        self.assertEqual(
            self.entry.options["resources"]["123"]["wired_clients"], ["790"]
        )
        self.assertEqual(len(self.er.entities), 4)

    async def test_data_fallback_selections(self):
        self.reset_v1(data_selections=True)
        await self.migrate()
        await self.setup_and_reload()
        self.assert_preserved((self.phone, self.wired))

    async def test_nested_resource_selections(self):
        self.reset_v1(nested=True)
        await self.migrate()
        await self.setup_and_reload()
        self.assert_preserved((self.phone, self.wired))

    async def test_entity_construction_reuses_ids_and_device_links(self):
        await self.migrate()
        await self.setup_and_reload()
        # Construct real binary sensors and resolve their device_info/unique_id
        # through the real registries, as the platform does. No fake unique IDs.
        for device, identifier, wireless in (
            (self.phone, "789", True),
            (self.wired, "790", False),
        ):
            client = SimpleNamespace(
                id=identifier,
                wireless=wireless,
                connected=True,
                is_network=False,
                is_backup_network=False,
                is_eero=False,
                is_profile=False,
                is_client=True,
                name="Fixture",
                name_connection_type="Fixture",
            )
            self.network.resources[:] = [
                r for r in self.network.resources if r.id != identifier
            ]
            self.network.resources.append(client)
            coordinator = self.hass.data["eero"][self.entry.entry_id]["coordinator"]
            entity = binary_sensor.EeroBinarySensorEntity(
                coordinator,
                "123",
                identifier,
                next(
                    d
                    for d in binary_sensor.BINARY_SENSOR_DESCRIPTIONS
                    if d.key == "connected"
                ),
                self.entry.options["miscellaneous"]["123"],
            )
            info = entity.device_info
            current = make_device(
                self.registry,
                config_entry_id=self.entry.entry_id,
                identifiers=info["identifiers"],
                model=info["model"],
            )
            self.assertEqual(current.id, device.id)
            old = next(
                x for x in self.entities_before if x.unique_id == entity.unique_id
            )
            registered = self.er.async_get_or_create(
                "binary_sensor",
                "eero",
                entity.unique_id,
                config_entry=self.entry,
                device_id=current.id,
            )
            self.assertEqual(registered.entity_id, old.entity_id)
        self.assertEqual(len(self.er.entities), 4)

    async def test_unselected_legacy_client_is_removed(self):
        self.flat["wired_clients"] = []
        self.reset_v1()
        await self.migrate()
        await eero.async_setup_entry(self.hass, self.entry)
        self.assertIsNone(self.registry.async_get(self.wired.id))
        self.assertIsNotNone(self.registry.async_get(self.phone.id))

    async def test_deselection_after_migration_still_removes_client(self):
        await self.migrate()
        options = deepcopy(dict(self.entry.options))
        options["resources"]["123"]["wired_clients"] = []
        self.hass.config_entries.async_update_entry(self.entry, options=options)
        await eero.async_setup_entry(self.hass, self.entry)
        self.assertIsNone(self.registry.async_get(self.wired.id))
        self.assertIsNotNone(self.registry.async_get(self.phone.id))

    async def test_exclude_filters_still_remove_listed_clients(self):
        await self.migrate()
        options = deepcopy(dict(self.entry.options))
        options["resources"]["123"]["wired_clients_filter"] = "exclude"
        self.hass.config_entries.async_update_entry(self.entry, options=options)
        await eero.async_setup_entry(self.hass, self.entry)
        self.assertIsNone(self.registry.async_get(self.wired.id))
        self.assertIsNotNone(self.registry.async_get(self.phone.id))

    async def test_modern_labels_and_unrelated_devices_unchanged(self):
        self.registry.async_update_device(self.phone.id, model="Client (Wireless)")
        unrelated = make_entry(
            domain="other",
            title="Other",
            version=1,
            minor_version=1,
            source="user",
            unique_id="other",
            discovery_keys=MappingProxyType({}),
            data={},
            options={},
        )
        self.hass.config_entries._entries[unrelated.entry_id] = unrelated
        other_entry = unrelated.entry_id
        other = make_device(
            self.registry,
            config_entry_id=other_entry,
            identifiers={("other", "789")},
            model="Client",
        )
        modern = self.registry.async_get(self.phone.id)
        await self.migrate()
        await self.setup_and_reload()
        self.assertEqual(self.registry.async_get(modern.id), modern)
        self.assertEqual(self.registry.async_get(other.id), other)


def load_tests(loader, tests, pattern):
    """Collect only the migration cases, excluding the fixture class."""
    return unittest.TestSuite(
        ClientMigrationTests(name)
        for name in ClientMigrationTests.__dict__
        if name.startswith("test_")
    )


if __name__ == "__main__":
    unittest.main(verbosity=2)
