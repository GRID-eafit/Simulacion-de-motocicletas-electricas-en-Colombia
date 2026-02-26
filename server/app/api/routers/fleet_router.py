"""
app/api/routers/fleet_router.py
--------------------------------
Fleet routing endpoint:
  POST /flota
"""

import httpx
from fastapi import APIRouter, HTTPException

from app.api.external.ors_client import fetch_ors_route
from app.core.config import settings
from app.models.schemas import FlotaInput
from app.services.fleet_service import procesar_ruteo

router = APIRouter(tags=["fleet"])


@router.post("/flota")
async def flota(body: FlotaInput):
    """Compute and return the optimal multi-stop fleet route.

    The depot is the first waypoint.  The route is solved with the Gurobi
    EVRP optimiser and the resulting sequence is painted via ORS.

    Request body
    ------------
    waypoints : list of Waypoint
        Up to 4 customer waypoints (plus the implicit depot = first point).
        Maximum 5 total points (including depot).
    """
    try:
        coords = [wp.coordinates for wp in body.waypoints]
        coords = coords + [coords[0]]  # close the tour

        if len(coords) > 5:
            raise HTTPException(
                status_code=400,
                detail="The number of waypoints must be ≤ 4 (5 including depot).",
            )

        recorrido = procesar_ruteo(coords=[coord[::-1] for coord in coords])

        recorrido_coords = [coords[0]]
        for viaje in recorrido:
            recorrido_coords.append(coords[viaje[1]])

        async with httpx.AsyncClient(timeout=30) as client:
            ruta = await fetch_ors_route(
                client, settings.ORS_TOKEN, "driving", recorrido_coords,
                steps=True, geometries="geojson", exclude=[],
            )

        waypoints = ruta["properties"]["way_points"]

        # Classify arcs: charging swaps vs normal delivery arcs
        points = recorrido[0]
        for i in range(1, len(recorrido)):
            points.append(recorrido[i][1])

        ruta_carga = []
        ruta_nodos = []
        for i in range(len(points) - 1):
            if points[i] and not points[i + 1]:
                ruta_carga.append([waypoints[i], waypoints[i + 1]])
            else:
                ruta_nodos.append([waypoints[i], waypoints[i + 1]])

        return {
            "ruta": [[ln, lat] for ln, lat, _ in ruta["geometry"]["coordinates"]],
            "distancia": ruta["properties"]["summary"]["distance"],
            "duracion": ruta["properties"]["summary"]["duration"],
            "ruta_carga": ruta_carga,
            "ruta_nodos": ruta_nodos,
            "viajes": [x + 1 for x in points][:-1] + [1],
        }

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Error: {exc}")
