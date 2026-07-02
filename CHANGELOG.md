# Changelog

All notable changes to this project are documented in this file.

This project follows semantic versioning once published with GitHub releases.

## 0.1.6 - 2026-07-02

### Added

- Added explicit `km` unit metadata/attributes to station distances.
- Added station address attributes when MIMIT provides them.
- Added clearer recommended-station attributes for address, distance, price and last update.

## 0.1.5 - 2026-07-02

### Added

- Added per-station fuel price sensors with numeric `EUR/L` states so individual station prices can be graphed and monitored over time.

## 0.1.4 - 2026-07-02

### Changed

- Station map marker names now include the best visible fuel price to avoid confusing the `geo_location` distance state with a fuel price.

## 0.1.3 - 2026-07-02

### Added

- Added a recommended station sensor that balances price and distance for the first configured fuel type.
- Added best-price attributes to station map markers.

### Fixed

- Improved station display names when MIMIT returns only a numeric station name.
- Exposed fuel prices with three decimal places in attributes and sensor values.

## 0.1.2 - 2026-07-02

### Fixed

- Replaced modern selector classes in the config flow with stable Home Assistant config validation helpers to avoid `400: Bad Request` when opening the integration setup flow.

## 0.1.1 - 2026-07-02

### Fixed

- Simplified `hacs.json` to use only keys supported by the current HACS manifest specification.

## 0.1.0 - 2026-06-30

### Added

- Initial Home Assistant custom integration for Italian fuel prices.
- UI configuration flow with latitude, longitude, radius, fuel filters and polling interval.
- Cloud polling client for MIMIT Osservaprezzi Carburanti.
- Best-price sensors for selected fuel types and service modes.
- Station count and nearest-station sensors.
- Geo-location entities for fuel station markers on Home Assistant maps.
- HACS metadata, README and project icon assets.
