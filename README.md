[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)
# Eero Home Assistant Integration
Custom component to allow control of Eero networks in [Home Assistant](https://home-assistant.io).

## Credit
- [@343max's eero-client project](https://github.com/343max/eero-client) - Basic API auth and refresh methods
- [@jrlucier's eero_tracker project](https://github.com/jrlucier/eero_tracker) - Initial Home Assistant idea

## Install
1. Ensure Home Assistant is updated to version 2025.2.0 or newer.
2. Use HACS and add as a [custom repo](https://hacs.xyz/docs/faq/custom_repositories); or download and manually move to the `custom_components` folder.
3. Once the integration is installed follow the standard process to setup via UI and search for `eero`.
4. Follow the prompts.

## Options
- Networks, resources, and activity metrics can be updated via integration options.
- The inclusion method for clients can be toggled between whitelisting (include only selected clients) or blacklisting (exclude only selected clients).
- If `Advanced Mode` is enabled for the current profile, additional options are available (interval, timeout, and response logging).

## Notes
- This integration does not support login via Amazon account. A workaround is to create a new account without Amazon login and add that account as another network admin. Refer to this [post](https://github.com/schmittx/home-assistant-eero/issues/77#issuecomment-1960875926) for step-by-step instructions.

## Currently Working
- Multiple networks supported
- Control network properties (ex. guest network, Eero Plus features, Eero Labs features)
- Pause access for profiles and/or clients
- Control content filters for profiles
- Device tracker entities for clients and profiles
- Sensors for various metrics
- Button entities to control features that require network restarts
- Select and time entities to control nightlight features for Eero Beacon devices
- Image entities to display QR code for joining main network and guest network
- Sensors for activity data (requires Eero Plus subscription)
- Set blocked apps for profiles (requires Eero Plus subscription)
- Update entities for Eero device firmware management
- Control backup networks (requires Eero Plus subscription)
- Read and manage DHCP reservations (static IPs) for clients

## DHCP Reservations
Client `device_tracker` entities expose whether their current IP is a static DHCP reservation:
- `ip_reserved` (bool) — whether the client's IP is reserved
- `reserved_ip` — the reserved IP address, when one exists

Two services create or remove reservations (pin an IP to a MAC address):

**`eero.set_reservation`** — create or update a reservation
| Field | Required | Description |
| --- | --- | --- |
| `mac` | yes | MAC address of the device |
| `ip` | yes | IP address to assign |
| `name` | no | Description shown for the reservation |
| `target_network` | no | Network name(s)/ID(s); defaults to all |

**`eero.delete_reservation`** — remove a reservation
| Field | Required | Description |
| --- | --- | --- |
| `mac` | yes | MAC address of the device |
| `target_network` | no | Network name(s)/ID(s); defaults to all |

### Example: one-tap "reserve" button on a dashboard
Because each `device_tracker` exposes its live `mac` and `ip`, you can pin a device to
its **current** IP straight from a dashboard button. A small script reads those
attributes and toggles the reservation:

```yaml
# scripts.yaml
eero_toggle_reservation:
  alias: "eero: toggle reservation"
  fields:
    tracker:
      description: The eero device_tracker to reserve/unreserve
  sequence:
    - choose:
        - conditions: "{{ state_attr(tracker, 'ip_reserved') | default(false) }}"
          sequence:
            - service: eero.delete_reservation
              data:
                mac: "{{ state_attr(tracker, 'mac') }}"
        - conditions: "{{ (state_attr(tracker, 'ip') | default('')) not in ['', 'None', none] }}"
          sequence:
            - service: eero.set_reservation
              data:
                mac: "{{ state_attr(tracker, 'mac') }}"
                ip: "{{ state_attr(tracker, 'ip') }}"
                name: "{{ state_attr(tracker, 'host_name') or tracker }}"
```

Any button can then call it with a device's entity, e.g. a `tap_action`:

```yaml
tap_action:
  action: perform-action
  perform_action: script.eero_toggle_reservation
  data:
    tracker: device_tracker.my_device
```

Tapping once reserves the device at its current IP; tapping again releases it.

## Coming Soon
- TBD, feature requests are welcome.
