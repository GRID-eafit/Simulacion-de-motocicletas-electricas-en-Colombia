"""
app/api/routers/tiles_router.py
--------------------------------
Map tile proxy endpoints:
  GET /tiles/carto/{z}/{x}/{y}.png
  GET /tiles/osm/{z}/{x}/{y}.png
"""

import httpx
from fastapi import APIRouter, HTTPException, Path, Response

router = APIRouter(prefix="/tiles", tags=["tiles"])


@router.get("/carto/{z}/{x}/{y}.png")
async def tile_carto(
    z: int = Path(..., ge=0, le=22),
    x: int = Path(..., ge=0),
    y: str = Path(...),
):
    """Proxy a CartoDB tile (supports @2x retina suffix)."""
    retina_suffix = ""
    if "@2x" in y:
        y_clean = y.replace("@2x", "")
        retina_suffix = "@2x"
    else:
        y_clean = y

    subdomains = ["a", "b", "c", "d"]
    s = subdomains[(x + z) % len(subdomains)]
    url = f"https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y_clean}{retina_suffix}.png"

    async with httpx.AsyncClient(timeout=20) as client:
        try:
            r = await client.get(url)
        except httpx.RequestError as exc:
            raise HTTPException(status_code=502, detail=f"Error fetching Carto tile: {exc!s}")

    if r.status_code != 200:
        raise HTTPException(status_code=r.status_code, detail=f"Carto returned {r.status_code}")

    return Response(
        content=r.content,
        headers={"Content-Type": "image/png", "Cache-Control": "public, max-age=86400"},
        media_type="image/png",
    )


@router.get("/osm/{z}/{x}/{y}.png")
async def tile_osm(
    z: int = Path(..., ge=0, le=22),
    x: int = Path(..., ge=0),
    y: int = Path(..., ge=0),
):
    """Proxy an OpenStreetMap raster tile."""
    url = f"https://tile.openstreetmap.org/{z}/{x}/{y}.png"

    async with httpx.AsyncClient(timeout=20) as client:
        try:
            r = await client.get(url)
        except httpx.RequestError as exc:
            raise HTTPException(status_code=502, detail=f"Error fetching OSM tile: {exc!s}")

    if r.status_code != 200:
        raise HTTPException(status_code=r.status_code, detail=f"OSM returned {r.status_code}")

    return Response(
        content=r.content,
        headers={"Content-Type": "image/png", "Cache-Control": "public, max-age=86400"},
        media_type="image/png",
    )
