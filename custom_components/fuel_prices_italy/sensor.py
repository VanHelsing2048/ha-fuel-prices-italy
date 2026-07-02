"""Sensor platform for Fuel Prices Italy."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import Station
from .const import (
    ATTR_BRAND,
    ATTR_DISTANCE_KM,
    ATTR_INSERT_DATE,
    ATTR_STATION_ID,
    ATTR_STATION_NAME,
    DOMAIN,
    FUEL_TYPES,
)
from .coordinator import FuelPricesItalyCoordinator


@dataclass(frozen=True, slots=True)
class PriceSensorDescription:
    """Description of a best-price sensor."""

    key: str
    name: str
    fuel_id: int
    is_self: bool | None


SENSOR_DESCRIPTIONS = (
    PriceSensorDescription("benzina_self", "Benzina self migliore", 1, True),
    PriceSensorDescription("benzina_servito", "Benzina servito migliore", 1, False),
    PriceSensorDescription("gasolio_self", "Gasolio self migliore", 2, True),
    PriceSensorDescription("gasolio_servito", "Gasolio servito migliore", 2, False),
    PriceSensorDescription("gpl", "GPL migliore", 4, None),
    PriceSensorDescription("metano", "Metano migliore", 3, None),
    PriceSensorDescription("hvo", "HVO migliore", 431, None),
    PriceSensorDescription("hvolution", "HVOlution migliore", 394, None),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors for a config entry."""
    coordinator: FuelPricesItalyCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            FuelBestPriceSensor(coordinator, entry, description)
            for description in SENSOR_DESCRIPTIONS
        ]
        + [
            FuelStationCountSensor(coordinator, entry),
            FuelNearestStationSensor(coordinator, entry),
            FuelRecommendedStationSensor(coordinator, entry),
        ]
    )


class FuelPricesItalySensorEntity(CoordinatorEntity[FuelPricesItalyCoordinator], SensorEntity):
    """Base class for Fuel Prices Italy sensors."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: FuelPricesItalyCoordinator, entry: ConfigEntry) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "MIMIT Osservaprezzi Carburanti",
        }


class FuelBestPriceSensor(FuelPricesItalySensorEntity):
    """Best price sensor for a fuel type."""

    _attr_native_unit_of_measurement = "EUR/L"
    _attr_suggested_display_precision = 3
    _attr_icon = "mdi:currency-eur"

    def __init__(
        self,
        coordinator: FuelPricesItalyCoordinator,
        entry: ConfigEntry,
        description: PriceSensorDescription,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator, entry)
        self.entity_description = description
        self._attr_name = description.name
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"

    @property
    def native_value(self) -> float | None:
        """Return the best price."""
        best = self.coordinator.best_price(
            self.entity_description.fuel_id, self.entity_description.is_self
        )
        return round(best[1].price, 3) if best else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return attributes for the station with the best price."""
        best = self.coordinator.best_price(
            self.entity_description.fuel_id, self.entity_description.is_self
        )
        if not best:
            return {}
        station, fuel = best
        return _station_attrs(station) | {
            "fuel_id": fuel.fuel_id,
            "fuel_name": fuel.name,
            "is_self": fuel.is_self,
            "price_eur_l": round(fuel.price, 3),
            "price_display": f"{fuel.price:.3f} EUR/L",
        }


class FuelStationCountSensor(FuelPricesItalySensorEntity):
    """Station count sensor."""

    _attr_name = "Distributori trovati"
    _attr_icon = "mdi:gas-station"

    def __init__(self, coordinator: FuelPricesItalyCoordinator, entry: ConfigEntry) -> None:
        """Initialize the entity."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_station_count"

    @property
    def native_value(self) -> int:
        """Return the number of visible stations."""
        return len(self.coordinator.data or {})


class FuelNearestStationSensor(FuelPricesItalySensorEntity):
    """Nearest station sensor."""

    _attr_name = "Distributore piu vicino"
    _attr_icon = "mdi:map-marker-distance"

    def __init__(self, coordinator: FuelPricesItalyCoordinator, entry: ConfigEntry) -> None:
        """Initialize the entity."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_nearest_station"

    @property
    def native_value(self) -> str | None:
        """Return the nearest station name."""
        station = self._nearest_station
        return station.display_name if station else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return nearest station attributes."""
        station = self._nearest_station
        return _station_attrs(station) if station else {}

    @property
    def _nearest_station(self) -> Station | None:
        stations = list((self.coordinator.data or {}).values())
        if not stations:
            return None
        return min(stations, key=lambda station: station.distance_km)


class FuelRecommendedStationSensor(FuelPricesItalySensorEntity):
    """Recommended station balancing price and distance."""

    _attr_name = "Distributore consigliato"
    _attr_icon = "mdi:map-marker-star"

    def __init__(self, coordinator: FuelPricesItalyCoordinator, entry: ConfigEntry) -> None:
        """Initialize the entity."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_recommended_station"

    @property
    def native_value(self) -> str | None:
        """Return the recommended station name."""
        recommendation = self._recommendation
        return recommendation[0].display_name if recommendation else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return recommendation details."""
        recommendation = self._recommendation
        if not recommendation:
            return {}

        station, fuel, score = recommendation
        return _station_attrs(station) | {
            "fuel_id": fuel.fuel_id,
            "fuel_name": fuel.name,
            "is_self": fuel.is_self,
            "price_eur_l": round(fuel.price, 3),
            "price_display": f"{fuel.price:.3f} EUR/L",
            "convenience_score": round(score, 3),
            "score_formula": "price_eur_l + distance_km * 0.03",
        }

    @property
    def _recommendation(self) -> tuple[Station, Any, float] | None:
        stations = list((self.coordinator.data or {}).values())
        if not stations or not self.coordinator.selected_fuel_types:
            return None

        fuel_id = self.coordinator.selected_fuel_types[0]
        best: tuple[Station, Any, float] | None = None
        for station in stations:
            for fuel in self.coordinator.visible_fuels(station):
                if fuel.fuel_id != fuel_id:
                    continue
                score = fuel.price + station.distance_km * 0.03
                if best is None or score < best[2]:
                    best = (station, fuel, score)
        return best


def _station_attrs(station: Station) -> dict[str, Any]:
    return {
        ATTR_STATION_ID: station.id,
        ATTR_STATION_NAME: station.display_name,
        ATTR_BRAND: station.brand,
        ATTR_DISTANCE_KM: round(station.distance_km, 3),
        ATTR_INSERT_DATE: station.insert_date,
    }
