"""
app/api/external/azure_client.py
---------------------------------
HTTP client wrappers for the Azure Maps Routing API.
"""

from typing import Any, Dict, List, Tuple

import httpx


async def fetch_azure_route(
    client: httpx.AsyncClient,
    token: str,
    coords: List[Tuple[float, float]],
) -> Dict[str, Any]:
    """Request a route from Azure Maps and return the raw GeoJSON response.

    Parameters
    ----------
    client:
        Shared async HTTP client.
    token:
        Azure Maps subscription key.
    coords:
        List of [lon, lat] coordinate pairs.  The first and last are treated
        as waypoints; intermediate points are treated as via-waypoints.
    """
    features = []
    for idx, (lon, lat) in enumerate(coords):
        point_type = "waypoint" if idx in (0, len(coords) - 1) else "viaWaypoint"
        features.append({
            "type": "Feature",
            "geometry": {"coordinates": [lon, lat], "type": "Point"},
            "properties": {"pointIndex": idx, "pointType": point_type},
        })

    # Fixed departure time – adjust to a configurable value if needed
    date = "2025-10-30T08:00:00-05:00"

    body = {
        "type": "FeatureCollection",
        "features": features,
        "optimizeRoute": "fastestWithTraffic",
        "routeOutputOptions": ["itinerary", "routePath"],
        "maxRouteCount": 1,
        "travelMode": "driving",
        "departAt": date,
    }

    url = "https://atlas.microsoft.com/route/directions"
    params = {"api-version": "2025-01-01"}

    response = await client.post(
        url=url,
        params=params,
        headers={
            "Content-Type": "application/json; charset=UTF-8",
            "subscription-key": token,
        },
        json=body,
    )
    response.raise_for_status()
    return response.json()


# Backward-compatible alias
_fetch_azure_route = fetch_azure_route
