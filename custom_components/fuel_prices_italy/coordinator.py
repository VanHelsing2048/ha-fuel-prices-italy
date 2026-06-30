"""Data coordinator for Fuel Prices Italy."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import FuelPricesItalyApiError, FuelPricesItalyClient, FuelPrice, Station
from .const import (
    CONF_FUEL_TYPES,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_MAX_STATIONS,
    CONF_RADIUS_KM,
    CONF_SCAN_INTERVAL,
    CONF_SHOW_SELF,
    CONF_SHOW_SERVICED,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_STATIONS,
)

_LOGGER = logging.getLogger(__name__)


class FuelPricesItalyCoordinator(DataUpdateCoordinator[dict[int, Station]]):
    """Coordinate station searches and expose normalized station data."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self.config_entry = entry
        self.client = FuelPricesItalyClient(async_get_clientsession(hass))
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=self._scan_interval,
            config_entry=entry,
        )

    @property
    def _scan_interval(self) -> timedelta:
        minutes = self.config_entry.options.get(CONF_SCAN_INTERVAL)
        if minutes is None:
            return DEFAULT_SCAN_INTERVAL
        return timedelta(minutes=int(minutes))

    @property
    def selected_fuel_types(self) -> list[int]:
        """Return selected fuel type ids."""
        fuel_types = self.config_entry.options.get(
            CONF_FUEL_TYPES, self.config_entry.data[CONF_FUEL_TYPES]
        )
        return [int(fuel_type) for fuel_type in fuel_types]

    @property
    def show_self(self) -> bool:
        """Return whether self-service prices are included."""
        return bool(
            self.config_entry.options.get(
                CONF_SHOW_SELF, self.config_entry.data[CONF_SHOW_SELF]
            )
        )

    @property
    def show_serviced(self) -> bool:
        """Return whether serviced prices are included."""
        return bool(
            self.config_entry.options.get(
                CONF_SHOW_SERVICED, self.config_entry.data[CONF_SHOW_SERVICED]
            )
        )

    async def _async_update_data(self) -> dict[int, Station]:
        """Fetch and merge stations for every selected fuel type."""
        try:
            stations: dict[int, Station] = {}
            for fuel_type in self.selected_fuel_types:
                results = await self.client.search_zone(
                    self.config_entry.options.get(
                        CONF_LATITUDE, self.config_entry.data[CONF_LATITUDE]
                    ),
                    self.config_entry.options.get(
                        CONF_LONGITUDE, self.config_entry.data[CONF_LONGITUDE]
                    ),
                    self.config_entry.options.get(
                        CONF_RADIUS_KM, self.config_entry.data[CONF_RADIUS_KM]
                    ),
                    fuel_type,
                )
                self._merge_stations(stations, results)
        except FuelPricesItalyApiError as err:
            raise UpdateFailed(str(err)) from err

        filtered = [
            station
            for station in stations.values()
            if self._station_has_visible_fuels(station)
        ]
        filtered.sort(key=lambda station: station.distance_km)
        max_stations = int(
            self.config_entry.options.get(CONF_MAX_STATIONS, MAX_STATIONS)
        )
        return {station.id: station for station in filtered[:max_stations]}

    def visible_fuels(self, station: Station) -> list[FuelPrice]:
        """Return fuels matching the configured fuel/mode filters."""
        selected = set(self.selected_fuel_types)
        return [
            fuel
            for fuel in station.fuels
            if fuel.fuel_id in selected
            and ((fuel.is_self and self.show_self) or (not fuel.is_self and self.show_serviced))
        ]

    def best_price(self, fuel_id: int, is_self: bool | None) -> tuple[Station, FuelPrice] | None:
        """Return the best station/fuel tuple for a selected fuel."""
        best: tuple[Station, FuelPrice] | None = None
        for station in self.data.values() if self.data else []:
            for fuel in self.visible_fuels(station):
                if fuel.fuel_id != fuel_id:
                    continue
                if is_self is not None and fuel.is_self != is_self:
                    continue
                if best is None or fuel.price < best[1].price:
                    best = (station, fuel)
        return best

    def _station_has_visible_fuels(self, station: Station) -> bool:
        return bool(self.visible_fuels(station))

    @staticmethod
    def _merge_stations(stations: dict[int, Station], results: Iterable[Station]) -> None:
        for station in results:
            if station.id not in stations:
                stations[station.id] = station
                continue

            known_fuels = {fuel.id for fuel in stations[station.id].fuels}
            stations[station.id].fuels.extend(
                fuel for fuel in station.fuels if fuel.id not in known_fuels
            )
