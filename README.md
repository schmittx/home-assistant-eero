[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)
# Eero Home Assistant Integration
Custom component to allow control of Eero networks in [Home Assistant](https://home-assistant.io).

## Credit
- [@343max's eero-client project](https://github.com/343max/eero-client) - Basic API auth and refresh methods
- [@jrlucier's eero_tracker project](https://github.com/jrlucier/eero_tracker) - Initial Home Assistant idea

## Install
1. Ensure Home Assistant is updated to version 2023.6.0 or newer.
2. Use HACS and add as a [custom repo](https://hacs.xyz/docs/faq/custom_repositories); or download and manually move to the `custom_components` folder.
3. Once the integration is installed follow the standard process to setup via UI and search for `eero`.
4. Follow the prompts.

## Options
- Networks, resources, and activity metrics can be updated via integration options.
- If `Advanced Mode` is enabled for the current profile, additional options are available (QR code behavior, interval, timeout, and response logging).

## Notes
- This integration does not support login via Amazon account. A workaround is to create a new account without Amazon login and add that account as another network admin.

## Currently Working
- Multiple networks supported
- Control network properties (i.e. guest network, Eero Plus features, Eero Labs features)
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

## Coming Soon
- TBD, feature requests are welcome.
