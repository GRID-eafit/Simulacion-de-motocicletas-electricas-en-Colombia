"""
Pydantic request/response schemas used by the API routers.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Shared primitives
# ---------------------------------------------------------------------------

class Waypoint(BaseModel):
    """A geographic point expressed as [lng, lat] or [lng, lat, alt]."""
    coordinates: List[float]


# ---------------------------------------------------------------------------
# /routes
# ---------------------------------------------------------------------------

class VehicleInput(BaseModel):
    vehicle_id: str
    waypoints: List[Waypoint] = Field(default_factory=list)


class StationsInput(BaseModel):
    """
    Manual charging stations sent from the frontend (optional).

    coords: list of [lng, lat]
    nombre: list of station names (may be empty)
    """
    coords: List[List[float]] = Field(default_factory=list)
    nombre: List[str] = Field(default_factory=list)


class Options(BaseModel):
    profile: str = "driving"
    alternatives: bool = False
    steps: bool = True
    geometries: str = "geojson"
    exclude: List[str] = Field(default_factory=list)

    # ORS alternative-route parameters
    alt_count: int = 3
    alt_share: float = 0.6
    alt_weight: float = 1.4

    # Map city / stations scope
    city: str = "med"  # "med", "bog" or "amva"

    traffic: bool = False

    charger_power_kw: float = 3.5
    price_per_kwh: float = 0.0


class RoutesRequest(BaseModel):
    options: Options
    vehicles: List[VehicleInput]
    stations: Optional[StationsInput] = None


# ---------------------------------------------------------------------------
# /flota
# ---------------------------------------------------------------------------

class FlotaInput(BaseModel):
    waypoints: List[Waypoint] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# /route_only
# ---------------------------------------------------------------------------

class RouteOnlyRequest(BaseModel):
    coords: List[List[float]] = Field(..., min_length=2)  # [[lng, lat], ...]
    profile: str = "driving"
    geometries: str = "geojson"


class RouteOnlyResponse(BaseModel):
    distance_km: float
    duration_min: float
    geometry: Dict[str, Any]  # GeoJSON LineString


# ---------------------------------------------------------------------------
# /costs/compute
# ---------------------------------------------------------------------------

class CostsComputeRequest(BaseModel):
    coords: List[List[float]] = Field(..., min_length=2)

    # Optional: if not provided the backend selects from the CSV
    municipio_origen: Optional[str] = None
    municipio_destino: Optional[str] = None
    estrato: Optional[str] = None
    motivo_viaje: Optional[str] = None
