"""
app/utils/telemetry.py
----------------------
Telemetry building utilities – converts simulation output into
a point-by-point telemetry payload.
"""

import math
from datetime import datetime, timedelta, timezone


def build_point_telemetry(route_data: dict) -> list:
    """Build point-by-point telemetry from the output of moto_consume.

    Parameters
    ----------
    route_data:
        Dict returned by :func:`app.services.route_service.moto_consume`,
        containing at least ``geometry.coordinates``,
        ``properties.potencia`` and ``properties.soc``.

    Returns
    -------
    list of telemetry dicts with keys:
        lat, lng, altitude, speed_kmh, power_kW, soc, energy_kWh, t_epoch
    """
    coords = route_data["geometry"]["coordinates"]
    potencia = route_data["properties"].get("potencia", [])
    soc = route_data["properties"].get("soc", [])

    altitudes = [c[2] if len(c) > 2 else None for c in coords]

    # Derive speed from successive coordinates when real speeds are unavailable
    speeds_ms = []
    for i in range(len(coords)):
        if i == 0:
            speeds_ms.append(0.0)
            continue

        lon1, lat1, *_ = coords[i - 1]
        lon2, lat2, *_ = coords[i]

        R = 6_371_000.0
        d_lat = math.radians(lat2 - lat1)
        d_lon = math.radians(lon2 - lon1)
        a = (
            math.sin(d_lat / 2) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(d_lon / 2) ** 2
        )
        d = 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        # Synthetic 1-second timestep
        v = d / 1.0
        speeds_ms.append(v)

    # Cumulative energy (kWh) – synthetic uniform timeline
    energy_kwh = []
    cum = 0.0
    for p in potencia:
        p_kw = p / 1000.0 if isinstance(p, (int, float)) else 0.0
        cum += p_kw * (1 / 3600)
        energy_kwh.append(cum)

    base = datetime.now(timezone.utc)
    timestamps = [(base + timedelta(seconds=i)).timestamp() for i in range(len(coords))]

    telemetry = []
    for i in range(len(coords)):
        lon, lat, *_ = coords[i]
        telemetry.append({
            "lat": lat,
            "lng": lon,
            "altitude": altitudes[i] if i < len(altitudes) else None,
            "speed_kmh": speeds_ms[i] * 3.6,
            "power_kW": potencia[i] if i < len(potencia) else None,
            "soc": soc[i] if i < len(soc) else None,
            "energy_kWh": energy_kwh[i] if i < len(energy_kwh) else None,
            "t_epoch": timestamps[i],
        })

    return telemetry
