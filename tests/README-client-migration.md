# Client migration regressions

Selected clients from a version-1 entry must retain their device/entity identities
and user settings when migrated and set up. Run with Python 3.14 for Home
Assistant 2026.10.1, or Python 3.13 for the minimum supported HA 2025.2.0:

```sh
python3.14 -m venv .venv
.venv/bin/python -m pip install -r tests/requirements-client-migration.txt
.venv/bin/python -m unittest discover -s tests -p 'test_client_migration.py' -v
```

Use a separate virtualenv and `python3.13` for the minimum-version run. Both
versions pass all eight tests. On unmodified upstream, seven preservation cases
fail while the modern-label control passes.

The tests use real device/entity registries, migration, setup cleanup,
unload/setup, coordinator and client entity construction. Provider data is
synthetic; loader, platform scheduling and config-entry storage notifications are
isolated. Registry matching verifies stable device/entity IDs and no duplicates.
This does not exercise full HA bootstrap or disk persistence. No Eero account,
credentials, provider connection or live Home Assistant instance is needed.

Cases cover wired and wireless clients; flat, data-backed and nested selections;
all device fields except the intended model/modification timestamp; entity IDs,
unique IDs, links, disabled/hidden settings; migration/reload idempotence;
legitimate deselection and exclude-filter removal; and unrelated entry ownership.
The fixture has one network. Broader multi-network setup cleanup and recovery of
records already deleted by an earlier upgrade are outside these tests.
