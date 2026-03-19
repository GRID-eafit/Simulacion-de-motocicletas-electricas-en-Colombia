"""
app/api/routers/routes_router.py
---------------------------------
Vehicle route simulation endpoints:
  POST /routes         – JSON input with per-vehicle waypoints
  POST /routes/geojson – GeoJSON FeatureCollection input
"""

import json
from typing import Any, Dict, List

import httpx
from fastapi import APIRouter, HTTPException, Request

from app.api.external.ors_client import fetch_ors_route
from app.core.config import settings
from app.models.schemas import RoutesRequest
from app.services.route_service import moto_consume
from app.utils.geo import _to2d

router = APIRouter(tags=["routes"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_estaciones(city: str, stations_input=None) -> dict:
    """Return the charging-station dataset to use for this request."""
    import json as _json

    if stations_input and stations_input.coords:
        names = list(stations_input.nombre or [])
        for i in range(len(names), len(stations_input.coords)):
            names.append(f"Estación {i + 1}")
        return {"coords": stations_input.coords, "nombre": names, "tipo": stations_input.tipo}

    ruta_archivo = "resources/data/estaciones"
    mapping = {
        "amva": f"{ruta_archivo}/estaciones_amva.json",
        "bog":  f"{ruta_archivo}/estaciones_bog.json",
        "med":  f"{ruta_archivo}/estaciones_med.json",
    }
    path = mapping.get(city)
    if not path:
        raise HTTPException(status_code=500, detail=f"Unknown city: {city!r}")
    with open(path, "r", encoding="utf-8") as f:
        return _json.load(f)


def _validate_tokens(traffic: bool) -> None:
    """Raise HTTPException if required API tokens are missing."""
    if traffic:
        if not settings.AZURE_TOKEN:
            raise HTTPException(
                status_code=500,
                detail="traffic=True but AZURE_TOKEN is not set in .env",
            )
        if not settings.ORS_TOKEN:
            raise HTTPException(
                status_code=500,
                detail="traffic=True but ORS_TOKEN is not set (needed for alt/elevation)",
            )
    else:
        if not settings.ORS_TOKEN:
            raise HTTPException(status_code=500, detail="ORS_TOKEN is not set in .env")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/routes")
async def routes(body: RoutesRequest):
    """Simulate one or more vehicles along their respective waypoint sequences.

    Returns geometry, SoC history, energy data and charging stops for
    each vehicle processed.
    """
    city = body.options.city
    if not city:
        raise HTTPException(status_code=500, detail="No city provided in options")

    traffic = bool(body.options.traffic)
    _validate_tokens(traffic)

    estaciones = _resolve_estaciones(city, body.stations)

    out: List[Dict[str, Any]] = []
    idx = 1

    async with httpx.AsyncClient(timeout=30) as client:
        for v in body.vehicles:
            if len(v.waypoints) < 2:
                continue

            coords = _to2d([wp.coordinates for wp in v.waypoints])
            if len(coords) < 2:
                continue

            try:
                data = await moto_consume(
                    coords=coords,
                    estaciones=estaciones,
                    nombre=f"moto-{idx}",
                    client=client,
                    ors_token=settings.ORS_TOKEN,
                    azure_token=settings.AZURE_TOKEN,
                    profile=body.options.profile,
                    city=city,
                    traffic=traffic,
                    charger_power_kw=body.options.charger_power_kw,
                    price_per_kwh=body.options.price_per_kwh,
                )
            except httpx.RequestError as exc:
                raise HTTPException(status_code=502, detail=f"Network error (ORS/Azure): {exc!s}")

            idx += 1
            out.append({"vehicle_id": v.vehicle_id, **data})

    return {"routes": out}

@router.post("/routes/geojson")
async def routes_geojson(request: Request):
    """Compute routes for vehicles supplied as a GeoJSON FeatureCollection.

    Each Feature must have ``geometry.type == "LineString"`` with the
    waypoints as its coordinates.  An optional ``properties.vehicle_id``
    label is used when present.

    Query parameters mirror the ``Options`` schema for the JSON endpoint.
    """
    if not settings.ORS_TOKEN:
        raise HTTPException(status_code=500, detail="ORS_TOKEN is not set in .env")

    body = await request.json()
    if body.get("type") != "FeatureCollection" or "features" not in body:
        raise HTTPException(status_code=400, detail="Expected a GeoJSON FeatureCollection")

    qp = request.query_params
    profile = (qp.get("profile") or "driving").lower()
    steps = (qp.get("steps") or "true").lower() == "true"
    geometries = qp.get("geometries") or "geojson"
    exclude: List[str] = []

    want_alts = (qp.get("alternatives") or "false").lower() == "true"
    alt_count = int(qp.get("alt_count") or 3)
    alt_share = float(qp.get("alt_share") or 0.6)
    alt_weight = float(qp.get("alt_weight") or 1.4)

    features = body["features"]
    out: List[Dict[str, Any]] = []

    async with httpx.AsyncClient(timeout=30) as client:
        idx = 1
        for feat in features:
            geom = (feat or {}).get("geometry") or {}
            if geom.get("type") != "LineString":
                continue

            coords = _to2d(geom.get("coordinates") or [])
            if len(coords) < 2:
                continue

            vehicle_id = ((feat.get("properties") or {}).get("vehicle_id")) or f"moto-{idx}"
            idx += 1

            try:
                r = await fetch_ors_route(
                    client=client,
                    token=settings.ORS_TOKEN,
                    profile_key=profile,
                    coords=coords,
                    steps=steps,
                    geometries=geometries,
                    exclude=exclude,
                    want_alternatives=want_alts,
                    alt_count=alt_count,
                    alt_share=alt_share,
                    alt_weight=alt_weight,
                )
            except httpx.RequestError as exc:
                raise HTTPException(status_code=502, detail=f"ORS network error: {exc!s}")

            out.append({"vehicle_id": vehicle_id, **r})

    return {"routes": out}
