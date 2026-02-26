"""
app/utils/geo.py
----------------
Geographic utility functions shared across the application.

Includes:
- Coordinate normalisation (_to2d)
- Haversine distance (haversine_km)
- Route vector interpolation (preprocesar_vectores)
- ORS/Azure segment parsing (get_vel, get_vel_azure, manage_segments)
"""

import math
import numpy as np
from geopy.distance import geodesic
from typing import List, Tuple


# ---------------------------------------------------------------------------
# Coordinate helpers
# ---------------------------------------------------------------------------

def _to2d(coords: list) -> list:
    """Strip altitude from coordinate lists, filter invalid entries.

    Accepts points as [lon, lat] or [lon, lat, alt] and returns [[lon, lat], ...].
    """
    out = []
    for pt in coords:
        if isinstance(pt, (list, tuple)) and len(pt) >= 2:
            try:
                out.append([float(pt[0]), float(pt[1])])
            except Exception:
                continue
    return out


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return the great-circle distance in kilometres between two points."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


# ---------------------------------------------------------------------------
# Signal interpolation
# ---------------------------------------------------------------------------

def preprocesar_vectores(
    velocidades: list,
    pendientes: list,
    tiempos: list,
    coordenadas: list,
    puntos_intermedios: int = 10,
) -> Tuple[list, list, list, list]:
    """Linear-interpolate speed, slope, time and coordinate vectors to add
    *puntos_intermedios* synthetic points between every pair of originals."""
    n_original = len(velocidades)
    if n_original < 2:
        return velocidades, pendientes, tiempos, coordenadas

    n_nuevo = n_original + (n_original - 1) * puntos_intermedios
    x_original = np.arange(n_original)
    x_nuevo = np.linspace(0, n_original - 1, n_nuevo)

    velocidades_interp = np.interp(x_nuevo, x_original, velocidades).tolist()
    pendientes_interp = np.interp(x_nuevo, x_original, pendientes).tolist()
    tiempos_interp = np.interp(x_nuevo, x_original, tiempos).tolist()

    coords_interp = []
    for i in range(3):
        valores = [coord[i] for coord in coordenadas]
        coords_interp.append(np.interp(x_nuevo, x_original, valores).tolist())

    coordenadas_interp = [
        [coords_interp[0][i], coords_interp[1][i], coords_interp[2][i]]
        for i in range(n_nuevo)
    ]

    return velocidades_interp, pendientes_interp, tiempos_interp, coordenadas_interp


# ---------------------------------------------------------------------------
# Segment parsers
# ---------------------------------------------------------------------------

def get_vel(steps: list, elevation_data: list) -> dict:
    """Parse an ORS-style route into speed/slope/time/coord vectors."""
    route: dict = {"coords": [], "speeds": [], "slopes": [], "times": []}
    total_time = 0.0
    total_distance = 0.0

    for step in steps:
        start_idx, end_idx = step["way_points"]
        step_duration = step["duration"]
        step_distance = step["distance"]
        num_points = end_idx - start_idx

        if num_points <= 0:
            continue

        duration_per_point = step_duration / num_points
        distance_per_point = step_distance / num_points

        for i in range(num_points):
            idx = start_idx + i
            if idx >= len(elevation_data):
                break

            lng, lat, alt = elevation_data[idx]

            if route["coords"]:
                prev_lng, prev_lat, prev_alt = route["coords"][-1]
            else:
                prev_lng, prev_lat, prev_alt = lng, lat, alt

            horiz_dist = geodesic((prev_lat, prev_lng), (lat, lng)).meters
            delta_alt = alt - prev_alt
            slope_deg = math.degrees(math.atan2(delta_alt, horiz_dist)) if horiz_dist != 0 else 0
            speed_ms = (distance_per_point / duration_per_point) if duration_per_point != 0 else 0

            route["coords"].append([lng, lat, alt])
            route["speeds"].append(round(speed_ms, 2))
            route["slopes"].append(round(slope_deg, 2))
            route["times"].append(round(total_time, 2))

            total_time += duration_per_point
            total_distance += distance_per_point

            # Append last point of the data
            if idx == len(elevation_data) - 2:
                lng, lat, alt = elevation_data[-1]
                delta_alt = alt - prev_alt
                horiz_dist = geodesic((prev_lat, prev_lng), (lat, lng)).meters
                slope_deg = math.degrees(math.atan2(delta_alt, horiz_dist)) if horiz_dist != 0 else 0

                route["coords"].append([lng, lat, alt])
                route["speeds"].append(round(speed_ms, 2))
                route["slopes"].append(round(slope_deg, 2))
                route["times"].append(round(total_time, 2))

    return route


def get_vel_azure(features: list, elevation_data: list) -> dict:
    """Parse an Azure Maps route (with elevation overlay) into speed/slope/time/coord vectors."""
    route: dict = {"coords": [], "speeds": [], "slopes": [], "times": []}
    total_time = 0.0
    total_distance = 0.0

    for feature in features:
        props = feature["properties"]
        steps = props.get("steps", [])

        for step in steps:
            start_idx, end_idx = step["routePathRange"]["range"]
            step_duration = props.get("durationInSeconds", 0)
            step_distance = props.get("distanceInMeters", 0)
            num_points = end_idx - start_idx

            if num_points <= 0:
                continue

            duration_per_point = step_duration / num_points
            distance_per_point = step_distance / num_points

            for i in range(num_points):
                idx = start_idx + i
                lng, lat, alt = elevation_data[idx]

                if route["coords"]:
                    prev_lng, prev_lat, prev_alt = route["coords"][-1]
                else:
                    prev_lng, prev_lat, prev_alt = lng, lat, alt

                horiz_dist = geodesic((prev_lat, prev_lng), (lat, lng)).meters
                delta_alt = alt - prev_alt
                slope_deg = math.degrees(math.atan2(delta_alt, horiz_dist)) if horiz_dist != 0 else 0
                speed_ms = (distance_per_point / duration_per_point) if duration_per_point != 0 else 0

                prev_alt = route["coords"][-1][2] if route["coords"] else alt

                route["coords"].append([lng, lat, alt])
                route["speeds"].append(round(speed_ms, 2))
                route["slopes"].append(round(slope_deg, 2))
                route["times"].append(round(total_time, 2))

                total_time += duration_per_point
                total_distance += distance_per_point

                if idx == len(elevation_data) - 2:
                    lng, lat, alt = elevation_data[-1]
                    delta_alt = alt - prev_alt
                    horiz_dist = geodesic((prev_lat, prev_lng), (lat, lng)).meters
                    slope_deg = math.degrees(math.atan2(delta_alt, horiz_dist)) if horiz_dist != 0 else 0

                    route["coords"].append([lng, lat, alt])
                    route["speeds"].append(round(distance_per_point / duration_per_point, 2))
                    route["slopes"].append(round(slope_deg, 2))
                    route["times"].append(round(total_time, 2))

    return route


def manage_segments(rutas: dict, traffic: bool, elevation: list = None) -> list:
    """Convert a raw ORS or Azure route response into simulation-ready segments."""
    rutas_moto = []

    if traffic:
        features = rutas["features"]
        data = get_vel_azure(features, elevation)
        data["distance"] = features[-1]["properties"]["distanceInMeters"]
        data["duration"] = features[-1]["properties"]["durationInSeconds"]

        vel_interp, pend_interp, time_interp, coords_interp = preprocesar_vectores(
            data["speeds"], data["slopes"], data["times"], data["coords"], puntos_intermedios=2
        )
        data["speeds"] = vel_interp
        data["slopes"] = pend_interp
        data["times"] = time_interp
        data["coords"] = coords_interp
        rutas_moto = data

    else:
        for segment in rutas["properties"]["segments"]:
            data = get_vel(segment["steps"], rutas["geometry"]["coordinates"])
            data["duration"] = segment["duration"]
            data["distance"] = segment["distance"]

            vel_interp, pend_interp, time_interp, coords_interp = preprocesar_vectores(
                data["speeds"], data["slopes"], data["times"], data["coords"], puntos_intermedios=2
            )
            data["speeds"] = vel_interp
            data["slopes"] = pend_interp
            data["times"] = time_interp
            data["coords"] = coords_interp
            rutas_moto.append(data)

    return rutas_moto
