# Eero Home Assistant Integration

Custom component to allow control of [Eero](https://eero.com) wireless networks in [Home Assistant](https://home-assistant.io).

## Credit

- [@343max's eero-client project](https://github.com/343max/eero-client) - Basic API auth and refresh methods
- [@jrlucier's eero_tracker project](https://github.com/jrlucier/eero_tracker) - Initial Home Assistant idea

## Install

1. Ensure Home Assistant is updated to version 2021.4.0 or newer.
2. Use [HACS](https://hacs.xyz/) and add as a custom repo.
3. Once the integration is installed, follow the standard setup process via UI and search for `eero`.
4. Follow the prompts.

## Options

- Networks, resources, and activity metrics can be updated via integration options.
- If `Advanced Mode` is enabled for the current profile, additional options are available (interval, timeout, and response logging).

## Currently Working

- Multiple physically separate networks on a single Eero account
- Control network properties (i.e. guest network, Eero Secure features, Eero Labs features)
- Pause access for profiles or clients
- Control content filters for profiles
- Create device trackers for clients
- Sensors for various metrics
- Custom services to control features that require network restarts
- Custom service to control nightlight features for Eero Beacon devices
- Camera entities to display QR code for joining main network and guest network (if enabled)
- Sensors for activity data (requires Eero Secure subscription)

## Coming Soon

- TBD, feature requests are welcome.

## See Also

* [eero Integration Support](https://community.home-assistant.io/t/new-custom-component-eero-integration/244583) - for questions and help regarding this integration
* [eero Home Assistant Forum](https://community.home-assistant.io/t/eero-support/21153)


## Lovelace Examples

Show QR code and WiFi connection details on Home Assistant wall panel:

```yaml
type: grid
cards:
  - type: picture-entity
    entity: camera.guest_network
    show_name: false
    show_state: false
    tap_action:
      action: none
    hold_action:
      action: none
  - type: markdown
    content: |-
      Scan the QR code to the left to access WiFi, or:

      **SSID:** Guest Network
      **Password:** yourwelcome
    title: Connect to WiFi
columns: 2
```
