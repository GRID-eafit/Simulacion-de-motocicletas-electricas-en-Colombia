# utils/charge_functions.py

def linear_function(x, b, m):
    return x * m + b


def resolve_values(station_type: str, energy_charged_time: float) -> tuple[int, float]:
    """
    Returns (steps_to_add, adjusted_charge_time).
    steps_to_add: how many interpolation points to insert.
    adjusted_charge_time: actual charge duration in hours.
    """
    mapping = {
        "Estándar":              (40, energy_charged_time),
        "Alta Capacidad":        (10, 0.2 * energy_charged_time),
        "Intercambio":  (2,  1/60),  # near-instant swap, 1 min
    }
    result = mapping.get(station_type)
    if result is None:
        raise ValueError(f"Unknown station type: {station_type!r}")
    return result


def compute_charge_curve(
    station_type: str,
    soc_history: list[float],
    charge_time: float,
) -> tuple[list[float], float]:
    """
    Interpolates intermediate SOC values between the last two history
    points to simulate a realistic charge transition.

    Returns:
        (intermediate_soc_points, adjusted_charge_time_h)
    """
    if len(soc_history) < 2:
        raise ValueError("soc_history must have at least 2 points to interpolate.")

    steps_to_add, charge_time = resolve_values(station_type, charge_time)

    y1 = soc_history[-2]   # SOC just before charging started
    y2 = soc_history[-1]   # SOC target (full battery)

    # Slope so the line goes from y1 to y2 over `steps_to_add` intervals
    m = (y2 - y1) / steps_to_add
    b = y1  # at x=0 the value is y1

    # Generate points x=1 .. steps_to_add-1 (exclude endpoints; caller owns them)
    intermediate = [linear_function(x, b, m) for x in range(1, steps_to_add)]

    return intermediate, charge_time