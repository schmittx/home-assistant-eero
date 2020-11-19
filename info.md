# Eero Home Assistant Integration
Custom component to allow control of Eero networks in [Home Assistant](https://home-assistant.io).

## Credit
- [@343max's eero-client project](https://github.com/343max/eero-client) - Basic API auth and refresh methods
- [@jrlucier's eero_tracker project](https://github.com/jrlucier/eero_tracker) - Initial Home Assistant idea

## Install
1. Use HACS and add as a custom repo.
2. Once the integration is installed follow the standard process to setup via UI and search for `eero`.
3. Follow the prompts.

## Options
- Networks and resources can be updated via integration options.
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

## Coming Soon
- Sensors for activity data (ad blocks, data usage, scans, threat blocks)
