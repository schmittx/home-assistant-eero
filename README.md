# Eero Home Assistant Integration
Custom component to allow control of Eero networks in [Home Assistant](https://home-assistant.io).

## Credit
- [@343max's eero-client project](https://github.com/343max/eero-client) - Basic API auth and refresh methods
- [@jrlucier's eero_tracker project](https://github.com/jrlucier/eero_tracker) - Initial Home Assistant idea

## Install
1. Ensure Home Assistant is updated to version 2021.4.0 or newer.
2. Use HACS and add as a custom repo.
3. Once the integration is installed follow the standard process to setup via UI and search for `eero`.
4. Follow the prompts.

## Options
- Networks, resources, and activity metrics can be updated via integration options.
- If `Advanced Mode` is enabled for the current profile, additional options are available (interval, timeout, and response logging).


## Currently Working
- Multiple networks supported
- Control network properties (i.e. guest network, Eero Secure features, Eero Labs features)
- Pause access for profiles and/or clients
- Control content filters for profiles
- Create device trackers for clients
- Sensors for various metrics
- Custom services to control features that require network restarts
- Custom service to control nightlight features for Eero Beacon devices
- Camera entities to display QR code for joining main network and guest network (if enabled)
- Sensors for activity data (requires Eero Secure subscription)

## Coming Soon
- TBD, feature requests are welcome.
