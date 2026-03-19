"""
Orchestration logic for the simulation of a single motorcycle trip.

Combines external routing (ORS / Azure) with the Moto simulation class
to produce energy, charging and geometry data for one vehicle.
"""

from typing import Any, Dict, List

import httpx

from app.api.external.ors_client import fetch_ors_route, fetch_elevation
from app.api.external.azure_client import fetch_azure_route
from app.models.moto import Moto
from app.utils.geo import manage_segments, _to2d
# from app.utils.charge_function import 

async def enrutar(
    coords: list,
    traffic: bool,
    ors_token: str,
    azure_token: str,
    client: httpx.AsyncClient,
) -> list:
    """Fetch route segments from the appropriate provider and parse them into
    simulation-ready dicts containing coords, speeds, slopes and times."""
    rutas_moto = []

    if traffic:
        for i in range(len(coords) - 1):
            ruta_azure = await fetch_azure_route(
                client=client,
                token=azure_token,
                coords=[coords[i], coords[i + 1]],
            )

            ruta_alt = await fetch_elevation(
                client=client,
                token=ors_token,
                coords=ruta_azure["features"][-1]["geometry"]["coordinates"][0],
            )

            rutas = manage_segments(
                rutas=ruta_azure,
                traffic=traffic,
                elevation=ruta_alt,
            )
            rutas_moto.append(rutas)

    else:
        ors_route = await fetch_ors_route(
            client, ors_token, "driving", coords,
            steps=True, geometries="geojson", exclude=[],
        )
        rutas_moto = manage_segments(rutas=ors_route, traffic=traffic)

    return rutas_moto


async def moto_consume(
    coords: list,
    estaciones: dict,
    nombre: str,
    client: httpx.AsyncClient,
    ors_token: str,
    azure_token: str,
    profile: str,
    city: str = "med",
    traffic: bool = False,
    charger_power_kw: float = 3.5,
    price_per_kwh: float = 0.0,
) -> Dict[str, Any]:
    """Run the full motorcycle simulation for a single vehicle.

    1. Obtains route segments (ORS or Azure).
    2. Instantiates a :class:`~app.models.moto.Moto` and steps through the route.
    3. Whenever the battery runs low, routes the bike to the nearest station.
    4. Returns geometry, energy/SOC history and charging stop details.
    """
    rutas = await enrutar(
        coords=coords,
        traffic=traffic,
        ors_token=ors_token,
        azure_token=azure_token,
        client=client,
    )

    moto = Moto(
        nombre,
        rutas,
        estaciones,
        hybrid_cont=0,
        charger_power_kw=charger_power_kw,
        price_per_kwh=price_per_kwh,
    )

    step_result = moto.avanzar_paso()

    while step_result != 0:
        if step_result == 3:
            current_pos = moto.route_data[moto.idx]["coords"][moto.idx_ruta][:2]

            idx_est = moto.estacion_cercana(current_pos)
            station_coord = estaciones["coords"][idx_est]
            destiny = moto.route_data[moto.idx]["coords"][-1][:2]

            moto.añadir_punto_carga(idx_est, current_pos)

            nueva_ruta = await enrutar(
                coords=[current_pos, station_coord, destiny],
                traffic=traffic,
                ors_token=ors_token,
                azure_token=azure_token,
                client=client,
            )
            moto.cambiar_ruta(nueva_ruta)

        step_result = moto.avanzar_paso()

    speeds = []
    for ruta in moto.route_data:
        speeds.extend(ruta.get("speeds", []))

    # Lifecycle emission factors (gCO₂/km)
    factor_emision_electrico_gco2_km = 35
    factor_emision_combustion_gco2_km = 70

    emisiones_electrico_kg = (factor_emision_electrico_gco2_km * moto.distance) / 1000
    emisiones_combustion_kg = (factor_emision_combustion_gco2_km * moto.distance) / 1000
    
    return {
        "geometry": {
            "coordinates": [[lon, lat] for lon, lat, _ in moto.positions],
            "type": "LineString",
        },
        "properties": {
            "potencia": moto.power,
            "soc": moto.soc_history,
            "speeds": speeds,
            "map_city": city,
            "total_electric_kwh": moto.total_electric_kwh,
            "total_combustion_kwh": moto.total_combustion_kwh,
            "emisiones_electricas": emisiones_electrico_kg,
            "emisiones_combustion": emisiones_combustion_kg,
            "total_energy_charged_kwh": moto.total_energy_charged_kwh,
            "total_charge_time_min": moto.total_charge_time_min,
            "total_charge_cost": moto.total_charge_cost,
            "charger_power_kw": moto.charger_power_kw,
            "price_per_kwh": moto.price_per_kwh,
        },
        "summary": {
            "distance": moto.distance,
            "duration": moto.duration,
        },
        "alternatives": [],
        "charge_points": moto.puntos_recarga_realizados,
    }
