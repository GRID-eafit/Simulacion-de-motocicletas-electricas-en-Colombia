import httpx, json
from typing import Any, Dict, List, Tuple
from fastapi import HTTPException

PROFILE_MAP = {
    "driving": "driving-car",
    "walking": "foot-walking",
    "cycling": "cycling-regular",
}

def _to2d(coords):
    """
    Acepta puntos [lon,lat] o [lon,lat,alt] y devuelve solo [lon,lat].
    Filtra puntos inválidos.
    """
    out = []
    for pt in coords:
        if isinstance(pt, (list, tuple)) and len(pt) >= 2:
            try:
                out.append([float(pt[0]), float(pt[1])])
            except Exception:
                continue
    return out

async def _fetch_ors_route(
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
    headers = {"Authorization": token, "Content-Type": "application/json"}

    coords2d = _to2d(coords)  # fuerza 2D SIEMPRE

    data: Dict[str, Any] = {
        "elevation":True,
        "coordinates": coords2d,
        "instructions": steps,
        "geometry": geometries == "geojson",
        "extra_info": [],
        "preference": "fastest",
        "options": {},
    }
    if exclude:
        data["options"]["avoid_features"] = exclude

    if want_alternatives:
        data["alternative_routes"] = {
            "target_count": max(1, int(alt_count)),
            "share_factor": float(alt_share),
            "weight_factor": float(alt_weight),
        }

    url = f"https://api.openrouteservice.org/v2/directions/driving-car/geojson"

    resp = await client.post(url, headers=headers, json=data)
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

    with open("resources/examples/petition_raw_ors.json","w") as f:
        json.dump(principal,f,indent=2)
    
    return principal

async def _fecth_alt(
    client: httpx.AsyncClient,
    token: str,
    coords: List[Tuple[float, float]]
)->List[Tuple[float,float,float]]:
    url = "https://api.openrouteservice.org/elevation/line"
    headers = {
        "Authorization": token,
        "Content-Type": "application/json"
    }

    # ORS espera formato lat, lon para ENCODED_POLYLINE
    geometry_latlng = [(lng, lat) for lng, lat in coords]

    payload = {
        "format_in": "polyline",
        "format_out": "geojson",
        "geometry": geometry_latlng
    }

    response = await client.post(url, headers=headers, json=payload)
    if response.status_code != 200:
        raise Exception(f"Error elevación: {response.text}")
    data = response.json()
    return data['geometry']['coordinates']

async def _fetch_azure_route(
    client: httpx.AsyncClient,
    token: str,
    coords: List[Tuple[float, float]]
) -> Dict[str, Any]:
    
    features = []
    for idx, (lon, lat) in enumerate(coords):
        point_type = "waypoint" if idx in (0, len(coords) - 1) else "viaWaypoint"
        features.append({
            "type": "Feature",
            "geometry": {
                "coordinates": [lon, lat],
                "type": "Point"
            },
            "properties": {
                "pointIndex": idx,
                "pointType": point_type
            }
        })
    date = "2025-10-30T" + "08:00:00" + "-05:00" 

    body = {
        "type": "FeatureCollection",
        "features": features,
        "optimizeRoute": "fastestWithTraffic",
        "routeOutputOptions": ["itinerary","routePath"],
        "maxRouteCount": 1,
        "travelMode": "driving",
        "departAt": date
    }

    url = "https://atlas.microsoft.com/route/directions"
    params = {"api-version": "2025-01-01"}

    response = await client.post(
        url=url,
        params=params,
        headers={
            "Content-Type": "application/json; charset=UTF-8",
            "subscription-key": token
        },
        json=body
    )
    response.raise_for_status()
    return response.json()