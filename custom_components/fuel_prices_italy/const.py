"""Constants for the Fuel Prices Italy integration."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "fuel_prices_italy"
NAME = "Fuel Prices Italy"

API_BASE_URL = "https://carburanti.mise.gov.it/ospzApi"
DEFAULT_RADIUS_KM = 5.0
DEFAULT_SCAN_INTERVAL = timedelta(minutes=60)
MIN_SCAN_INTERVAL_MINUTES = 30
MAX_STATIONS = 50

CONF_FUEL_TYPES = "fuel_types"
CONF_LATITUDE = "latitude"
CONF_LONGITUDE = "longitude"
CONF_RADIUS_KM = "radius_km"
CONF_SHOW_SELF = "show_self"
CONF_SHOW_SERVICED = "show_serviced"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_MAX_STATIONS = "max_stations"

ATTR_BRAND = "brand"
ATTR_ADDRESS = "address"
ATTR_DISTANCE_KM = "distance_km"
ATTR_DISTANCE_UNIT = "distance_unit"
ATTR_FUELS = "fuels"
ATTR_INSERT_DATE = "insert_date"
ATTR_STATION_ID = "station_id"
ATTR_STATION_NAME = "station_name"

FUEL_TYPES: dict[int, str] = {
    1: "Benzina",
    2: "Gasolio",
    3: "Metano",
    4: "GPL",
    5: "Blue Super",
    20: "Blue Diesel",
    26: "Benzina speciale",
    27: "Gasolio speciale",
    324: "GNL",
    394: "HVOlution",
    405: "REHVO",
    431: "HVO",
}

FUEL_SELECT_OPTIONS = {str(fuel_id): name for fuel_id, name in FUEL_TYPES.items()}
DEFAULT_FUEL_TYPES = ["1", "2"]
