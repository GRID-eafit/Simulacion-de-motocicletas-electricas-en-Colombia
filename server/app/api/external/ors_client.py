"""
app/api/external/ors_client.py
------------------------------
HTTP client wrappers for the OpenRouteService (ORS) API.
"""

import json
from typing import Any, Dict, List, Tuple

import httpx
from fastapi import HTTPException

from app.utils.geo import _to2d


PROFILE_MAP = {
    "driving": "driving-car",
    "walking": "foot-walking",
    "cycling": "cycling-regular",
}


async def fetch_ors_route(
    client: httpx.AsyncClient,
    token: str,
    profile_key: str,
    coords: List[Tuple[float, float]],
    steps: bool,
    geometries: str,
    exclude: List[str],
    want_alternatives: bool = False,
    alt_count: int = 3,
    alt_share: float = 0.6,
    alt_weight: float = 1.4,
) -> Dict[str, Any]:
    """Request a route from ORS and return the first (best) feature dict."""
    headers = {"Authorization": token, "Content-Type": "application/json"}
    coords2d = _to2d(coords)

    payload: Dict[str, Any] = {
        "elevation": True,
        "coordinates": coords2d,
        "instructions": steps,
        "geometry": geometries == "geojson",
        "extra_info": [],
        "preference": "fastest",
        "options": {},
    }

    if exclude:
        payload["options"]["avoid_features"] = exclude

    if want_alternatives:
        payload["alternative_routes"] = {
            "target_count": max(1, int(alt_count)),
            "share_factor": float(alt_share),
            "weight_factor": float(alt_weight),
        }

    url = "https://api.openrouteservice.org/v2/directions/driving-car/geojson"
    resp = await client.post(url, headers=headers, json=payload)

    if resp.status_code >= 400:
        try:
            print("ORS ERROR:", resp.status_code, resp.text[:500])
        except Exception:
            pass
        try:
            err = resp.json()
        except Exception:
            err = {"message": resp.text}
        raise HTTPException(status_code=resp.status_code, detail=err)

    gj = resp.json()
    feats = gj.get("features", []) or []

    if not feats:
        return {"geometry": {"type": "LineString", "coordinates": []}, "summary": {}, "alternatives": []}

    principal = feats[0]

    # Persist last raw response for debugging
    try:
        with open("resources/examples/petition_raw_ors.json", "w") as f:
            json.dump(principal, f, indent=2)
    except Exception:
        pass

    return principal


async def fetch_elevation(
    client: httpx.AsyncClient,
    token: str,
    coords: List[Tuple[float, float]],
) -> List[Tuple[float, float, float]]:
    """Fetch elevation data from ORS for a list of [lon, lat] coordinates."""
    url = "https://api.openrouteservice.org/elevation/line"
    headers = {"Authorization": token, "Content-Type": "application/json"}

    geometry_latlng = [(lng, lat) for lng, lat in coords]
    payload = {
        "format_in": "polyline",
        "format_out": "geojson",
        "geometry": geometry_latlng,
    }

    response = await client.post(url, headers=headers, json=payload)
    if response.status_code != 200:
        raise Exception(f"Elevation API error: {response.text}")

    data = response.json()
    return data["geometry"]["coordinates"]


# ---------------------------------------------------------------------------
# Backward-compatible aliases (used by older imports that still expect the
# underscore-prefixed names)
# ---------------------------------------------------------------------------
_fetch_ors_route = fetch_ors_route
_fecth_alt = fetch_elevation
