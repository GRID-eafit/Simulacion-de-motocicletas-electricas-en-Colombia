"""
app/utils/emissions.py
----------------------
Emissions and energy-consumption calculation utilities.
"""


def calcular_consumo_y_emisiones(
    potencia_electrica_w: list,
    potencia_combustion_kw: list,
    tiempos: list,
    speeds: list,
) -> dict:
    """Calculate total energy consumption and lifecycle-equivalent CO₂ emissions.

    Parameters
    ----------
    potencia_electrica_w:
        Electric power at each step (W).
    potencia_combustion_kw:
        Combustion power at each step (kW).
    tiempos:
        Timestamps for each step (s).
    speeds:
        Speed at each step (km/h).

    Returns
    -------
    dict with keys:
        consumo_electrico_kwh, consumo_combustion_kwh, consumo_galones,
        distancia_km, emisiones_electrico_kg, emisiones_combustion_kg,
        factor_emision_electrico, factor_emision_combustion
    """
    consumo_electrico_total = 0.0
    consumo_combustion_total = 0.0

    for i in range(len(potencia_electrica_w)):
        if i == 0:
            delta_t = tiempos[0] if tiempos[0] > 0 else 1.0
        else:
            delta_t = max(tiempos[i] - tiempos[i - 1], 0.1)

        tiempo_horas = delta_t / 3600
        consumo_electrico_total += (potencia_electrica_w[i] / 1000) * tiempo_horas
        consumo_combustion_total += potencia_combustion_kw[i] * tiempo_horas

    # Total distance (km)
    distancia_total = 0.0
    for i in range(len(speeds)):
        if i == 0:
            delta_t = tiempos[0] if tiempos[0] > 0 else 1.0
        else:
            delta_t = max(tiempos[i] - tiempos[i - 1], 0.1)
        vel_ms = speeds[i] / 3.6
        distancia_total += vel_ms * delta_t
    distancia_km = distancia_total / 1000

    # Lifecycle-equivalent emission factors (gCO₂/km)
    factor_emision_electrico_gco2_km = 35   # electric motorcycle
    factor_emision_combustion_gco2_km = 70  # combustion motorcycle

    emisiones_electrico_kg = (factor_emision_electrico_gco2_km * distancia_km) / 1000
    emisiones_combustion_kg = (factor_emision_combustion_gco2_km * distancia_km) / 1000

    # Fuel gallons equivalent
    poder_calorifico_gasolina_kwh_galon = 33.7
    consumo_galones = consumo_combustion_total / poder_calorifico_gasolina_kwh_galon

    return {
        "consumo_electrico_kwh": consumo_electrico_total,
        "consumo_combustion_kwh": consumo_combustion_total,
        "consumo_galones": consumo_galones,
        "distancia_km": distancia_km,
        "emisiones_electrico_kg": emisiones_electrico_kg,
        "emisiones_combustion_kg": emisiones_combustion_kg,
        "factor_emision_electrico": factor_emision_electrico_gco2_km,
        "factor_emision_combustion": factor_emision_combustion_gco2_km,
    }
