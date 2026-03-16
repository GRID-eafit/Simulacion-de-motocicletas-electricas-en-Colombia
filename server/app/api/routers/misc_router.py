"""
app/api/routers/misc_router.py
-------------------------------
Miscellaneous endpoints:
  GET  /health
  GET  /telemetria
  GET  /estaciones
  POST /geojson
"""

import json

from fastapi import APIRouter, HTTPException, Request

from app.core.config import settings

router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_estaciones(ubicacion: str = "amva") -> dict:
    """Load the charging-station dataset for *ubicacion*."""
    ruta_archivo = "resources/data/estaciones"
    mapping = {
        "amva": f"{ruta_archivo}/estaciones_amva.json",
        "bog":  f"{ruta_archivo}/estaciones_bog.json",
        "med":  f"{ruta_archivo}/estaciones_med.json",
    }
    path = mapping.get(ubicacion)
    if not path:
        raise ValueError(f"Unknown city: {ubicacion!r}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/health")
def health():
    """Return server liveness and token configuration status."""
    return {
        "ok": True,
        "provider": "ors/azure",
        "has_ors_token": bool(settings.ORS_TOKEN),
        "has_azure_token": bool(settings.AZURE_TOKEN),
    }


@router.get("/telemetria")
def telemetria():
    """Return example telemetry data from disk."""
    with open("resources/data/telemetry/telemetry_example.json", "r") as f:
        return json.load(f)


@router.get("/estaciones")
async def estaciones(city: str = "amva"):
    """Return the default charging stations for the given city.

    Query parameters
    ----------------
    city : str
        ``"amva"`` (default), ``"med"`` or ``"bog"``.
    """
    try:
        return _get_estaciones(city)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Error: {exc}")


@router.post("/geojson")
async def geojson_echo(req: Request):
    """Echo back a received GeoJSON FeatureCollection (for debugging)."""
    data = await req.json()
    if data.get("type") != "FeatureCollection":
        raise HTTPException(status_code=400, detail="Se esperaba FeatureCollection")
    return {"ok": True, "received": data}
