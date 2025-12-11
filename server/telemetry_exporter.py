# server/telemetry_exporter.py

import math
from datetime import datetime, timedelta, timezone


def build_point_telemetry(route_data):
    """
    Construye telemetría punto a punto a partir de lo que devuelve ors_routes + moto_consume.
    """

    # geometry.coordinates → lista de [lon, lat, alt]
    coords = route_data["geometry"]["coordinates"]

    # potencia
    potencia = route_data["properties"].get("potencia", [])
    soc = route_data["properties"].get("soc", [])

    # Puede venir desde ORS si tienes altitud habilitada
    altitudes = [c[2] if len(c) > 2 else None for c in coords]

    # Si no hay velocidades reales, derivamos velocidad aproximada
    speeds_ms = []
    for i in range(len(coords)):
        if i == 0:
            speeds_ms.append(0)
            continue

        lon1, lat1, _ = coords[i - 1]
        lon2, lat2, _ = coords[i]

        # Haversine
        R = 6371000.0
        d_lat = math.radians(lat2 - lat1)
        d_lon = math.radians(lon2 - lon1)

        a = math.sin(d_lat / 2) ** 2 + math.cos(math.radians(lat1)) * \
            math.cos(math.radians(lat2)) * math.sin(d_lon / 2) ** 2
        
        d = 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        # tiempo sintético si no existe nada más
        dt = 1.0  # 1 segundo por segmento → reemplazable si tu backend tiene tiempos reales
        v = d / dt
        speeds_ms.append(v)

    # Energía acumulada (aprox): potencia_kW * tiempo_horas
    energy_kwh = []
    cum = 0
    for i in range(len(potencia)):
        p = potencia[i] / 1000.0 if isinstance(potencia[i], (int, float)) else 0
        dt_h = 1 / 3600  # si no hay tiempo real, creamos un timeline sintético uniforme
        cum += p * dt_h
        energy_kwh.append(cum)

    # timestamps sintéticos: 1 punto = 1 segundo
    base = datetime.now(timezone.utc)
    timestamps = [(base + timedelta(seconds=i)).timestamp() for i in range(len(coords))]

    # Telemetría final
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
            "t_epoch": timestamps[i]
        })

    return telemetry
