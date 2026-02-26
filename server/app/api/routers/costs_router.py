"""
app/api/routers/costs_router.py
--------------------------------
Trip-cost and route-geometry endpoints:
  POST /route_only      – returns only the GeoJSON geometry (no simulation)
  POST /costs/compute   – runs the full cost simulation model
"""

import httpx
from fastapi import APIRouter, HTTPException

from app.api.external.ors_client import fetch_ors_route
from app.core.config import settings
from app.models.schemas import CostsComputeRequest, RouteOnlyRequest, RouteOnlyResponse
from app.services.costs_service import compute_custom_trip
from app.utils.geo import _to2d

router = APIRouter(tags=["costs"])


@router.post("/route_only", response_model=RouteOnlyResponse)
async def route_only(req: RouteOnlyRequest):
    """Return only the route geometry for a given coordinate pair (no simulation).

    Useful for painting a path on the map without computing energy data.
    """
    if not settings.ORS_TOKEN:
        raise HTTPException(status_code=500, detail="ORS_TOKEN is not set in .env")

    coords = _to2d(req.coords)
    if len(coords) < 2:
        raise HTTPException(status_code=400, detail="At least 2 coordinate points are required")

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            r = await fetch_ors_route(
                client=client,
                token=settings.ORS_TOKEN,
                profile_key=req.profile,
                coords=coords,
                steps=False,
                geometries=req.geometries,
                exclude=[],
                want_alternatives=False,
                alt_count=1,
                alt_share=0.6,
                alt_weight=1.4,
            )
        except httpx.RequestError as exc:
            raise HTTPException(status_code=502, detail=f"ORS network error: {exc!s}")

    if not r or "geometry" not in r:
        raise HTTPException(status_code=500, detail="Unexpected ORS response (no geometry)")

    summary = (r.get("properties") or {}).get("summary") or {}
    dist_m = float(summary.get("distance", 0.0))
    dur_s = float(summary.get("duration", 0.0))

    return {
        "distance_km": dist_m / 1000.0,
        "duration_min": dur_s / 60.0,
        "geometry": r.get("geometry") or {},
    }


@router.post("/costs/compute")
async def costs_compute(req: CostsComputeRequest):
    """Compute trip costs using the full simulation model.

    Missing parameters (municipality, estrato, travel purpose) are inferred
    from the model's internal dataset when not supplied.
    """
    coords = _to2d(req.coords)
    if len(coords) < 2:
        raise HTTPException(status_code=400, detail="At least 2 coordinate points are required")

    # Coordinates come as [lng, lat]; model expects separate lat/lng args
    origin_lng, origin_lat = coords[0]
    dest_lng, dest_lat = coords[-1]

    try:
        results = compute_custom_trip(
            origin_lat=origin_lat,
            origin_lng=origin_lng,
            dest_lat=dest_lat,
            dest_lng=dest_lng,
            municipio_origen=req.municipio_origen,
            municipio_destino=req.municipio_destino,
            estrato=req.estrato,
            motivo_viaje=req.motivo_viaje,
        )

        # If the model returned a non-fatal error with fallback data, pass it through
        if "error" in results and not results.get("fallback"):
            pass  # partial data is acceptable

    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Model error: {exc!s}")

    return results
