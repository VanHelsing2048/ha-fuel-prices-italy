"""Geo-location entities for Fuel Prices Italy stations."""

from __future__ import annotations

from typing import Any

from homeassistant.components.geo_location import GeolocationEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import Station
from .const import (
    ATTR_ADDRESS,
    ATTR_BRAND,
    ATTR_DISTANCE_KM,
    ATTR_DISTANCE_UNIT,
    ATTR_FUELS,
    ATTR_INSERT_DATE,
    DOMAIN,
)
from .coordinator import FuelPricesItalyCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up geo-location entities for a config entry."""
    coordinator: FuelPricesItalyCoordinator = hass.data[DOMAIN][entry.entry_id]
    known_station_ids: set[int] = set()

    @callback
    def add_new_stations() -> None:
        entities = []
        for station_id, station in (coordinator.data or {}).items():
            if station_id in known_station_ids:
                continue
            known_station_ids.add(station_id)
            entities.append(FuelStationGeoLocation(coordinator, entry, station))
        if entities:
            async_add_entities(entities)

    add_new_stations()
    entry.async_on_unload(coordinator.async_add_listener(add_new_stations))


class FuelStationGeoLocation(
    CoordinatorEntity[FuelPricesItalyCoordinator], GeolocationEvent
):
    """Map marker for a station."""

    _attr_icon = "mdi:gas-station"
    _attr_source = "fuel_prices_italy"
    _attr_unit_of_measurement = "km"

    def __init__(
        self,
        coordinator: FuelPricesItalyCoordinator,
        entry: ConfigEntry,
        station: Station,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._entry = entry
        self._station_id = station.id
        self._last_station = station
        self._attr_unique_id = f"{entry.entry_id}_station_{station.id}"

    @property
    def available(self) -> bool:
        """Return whether the station still exists in the latest data."""
        return super().available and self._station_id in (self.coordinator.data or {})

    @property
    def name(self) -> str:
        """Return the station name."""
        best_fuel = self._best_visible_fuel
        if best_fuel is None:
            return self._station.display_name
        return (
            f"{self._station.display_name} - "
            f"{best_fuel.name} {best_fuel.price:.3f} EUR/L"
        )

    @property
    def latitude(self) -> float:
        """Return latitude."""
        return self._station.latitude

    @property
    def longitude(self) -> float:
        """Return longitude."""
        return self._station.longitude

    @property
    def distance(self) -> float:
        """Return distance in kilometers."""
        return self._station.distance_km

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return station attributes."""
        station = self._station
        best_fuel = self._best_visible_fuel
        return {
            "station_name": station.display_name,
            ATTR_BRAND: station.brand,
            ATTR_ADDRESS: station.address,
            ATTR_DISTANCE_KM: round(station.distance_km, 3),
            ATTR_DISTANCE_UNIT: "km",
            ATTR_INSERT_DATE: station.insert_date,
            "best_price_eur_l": round(best_fuel.price, 3) if best_fuel else None,
            "best_price_display": f"{best_fuel.price:.3f} EUR/L" if best_fuel else None,
            "best_price_fuel": best_fuel.name if best_fuel else None,
            ATTR_FUELS: [
                fuel.as_dict() for fuel in self.coordinator.visible_fuels(station)
            ],
        }

    @property
    def _station(self) -> Station:
        station = (self.coordinator.data or {}).get(self._station_id)
        if station is not None:
            self._last_station = station
        return self._last_station

    @property
    def _best_visible_fuel(self):
        visible_fuels = self.coordinator.visible_fuels(self._station)
        return min(visible_fuels, key=lambda fuel: fuel.price) if visible_fuels else None
