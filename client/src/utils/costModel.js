// Haversine (distancia aproximada entre dos coords en km)
function haversineKm([lng1, lat1], [lng2, lat2]) {
  const R = 6371; // km
  const toRad = (deg) => (deg * Math.PI) / 180;

  const dLat = toRad(lat2 - lat1);
  const dLng = toRad(lng2 - lng1);

  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLng / 2) ** 2;

  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

export function buildLineStringFromWaypoints(waypoints = []) {
  const coords = waypoints.map((w) => w.coordinates);
  if (coords.length < 2) return null;

  return {
    type: "Feature",
    properties: {},
    geometry: {
      type: "LineString",
      coordinates: coords,
    },
  };
}

export function computeDistanceKmFromWaypoints(waypoints = []) {
  if (!waypoints || waypoints.length < 2) return 0;

  let total = 0;
  for (let i = 1; i < waypoints.length; i++) {
    total += haversineKm(waypoints[i - 1].coordinates, waypoints[i].coordinates);
  }
  return total;
}

/**
 * MVP del modelo de costos (placeholder).
 * Luego lo reemplazamos por la integración real con tu modelo.
 *
 * Params:
 * - waypoints: [{coordinates:[lng,lat]}...]
 * - price_per_kwh: number (COP/kWh)
 * - consumption_kwh_per_km: number (kWh/km) => aproximación simple
 */
export function runCostModel({
  waypoints = [],
  price_per_kwh = 0,
  consumption_kwh_per_km = 0.03, // ~ 0.03 kWh/km (placeholder razonable para e-moto ligera)
} = {}) {
  const distance_km = computeDistanceKmFromWaypoints(waypoints);
  const energy_kwh = distance_km * consumption_kwh_per_km;
  const cost_cop = energy_kwh * price_per_kwh;

  return {
    inputs: {
      price_per_kwh,
      consumption_kwh_per_km,
      n_points: waypoints.length,
    },
    results: {
      distance_km,
      energy_kwh,
      cost_cop,
    },
    notes: [
      "MVP: la ruta se calcula uniendo puntos (no es ruta por carretera).",
      "MVP: consumo por km es un parámetro aproximado y fijo (placeholder).",
      "Luego conectamos aquí tu modelo real y mostramos su salida exacta.",
    ],
  };
}