"""API client for the Italian MIMIT Osservaprezzi Carburanti service."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

from aiohttp import ClientError, ClientSession
from homeassistant.exceptions import HomeAssistantError

from .const import API_BASE_URL


class FuelPricesItalyError(HomeAssistantError):
    """Base error for Fuel Prices Italy."""


class FuelPricesItalyApiError(FuelPricesItalyError):
    """Raised when the remote API cannot be queried."""


@dataclass(slots=True)
class FuelPrice:
    """One fuel price exposed by a station."""

    id: int
    fuel_id: int
    name: str
    price: float
    is_self: bool

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> "FuelPrice":
        """Build a fuel price from API data."""
        return cls(
            id=int(data["id"]),
            fuel_id=int(data["fuelId"]),
            name=str(data["name"]),
            price=float(data["price"]),
            is_self=bool(data.get("isSelf")),
        )

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""
        return {
            "id": self.id,
            "fuel_id": self.fuel_id,
            "name": self.name,
            "price": round(self.price, 3),
            "price_display": f"{self.price:.3f} EUR/L",
            "is_self": self.is_self,
        }


@dataclass(slots=True)
class Station:
    """Fuel station returned by Osservaprezzi."""

    id: int
    name: str
    brand: str | None
    latitude: float
    longitude: float
    distance_km: float
    insert_date: str | None
    fuels: list[FuelPrice]

    @property
    def display_name(self) -> str:
        """Return a friendly station name."""
        if self.name and not re.fullmatch(r"\d+", self.name.strip()):
            return self.name
        if self.brand:
            return f"{self.brand} {self.id}"
        return f"Distributore {self.id}"

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> "Station":
        """Build a station from API data."""
        location = data.get("location") or {}
        return cls(
            id=int(data["id"]),
            name=str(data.get("name") or data["id"]),
            brand=data.get("brand"),
            latitude=float(location["lat"]),
            longitude=float(location["lng"]),
            distance_km=float(data.get("distance", 0)),
            insert_date=data.get("insertDate"),
            fuels=[FuelPrice.from_api(fuel) for fuel in data.get("fuels", [])],
        )

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""
        return {
            "id": self.id,
            "name": self.display_name,
            "brand": self.brand,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "distance_km": round(self.distance_km, 3),
            "insert_date": self.insert_date,
            "fuels": [fuel.as_dict() for fuel in self.fuels],
        }


class FuelPricesItalyClient:
    """Small async client for the MIMIT search endpoint."""

    def __init__(self, session: ClientSession) -> None:
        """Initialize the client."""
        self._session = session

    async def search_zone(
        self,
        latitude: float,
        longitude: float,
        radius_km: float,
        fuel_type: int,
    ) -> list[Station]:
        """Search stations around a point."""
        payload = {
            "points": [{"lat": latitude, "lng": longitude}],
            "fuelType": fuel_type,
            "priceOrder": "asc",
            "radius": radius_km,
        }

        try:
            response = await self._session.post(
                f"{API_BASE_URL}/search/zone",
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            data = await response.json()
        except (ClientError, TimeoutError) as err:
            raise FuelPricesItalyApiError(
                "Unable to fetch fuel prices from Osservaprezzi"
            ) from err

        if not data.get("success"):
            raise FuelPricesItalyApiError("Osservaprezzi returned an unsuccessful response")

        return [Station.from_api(station) for station in data.get("results", [])]
