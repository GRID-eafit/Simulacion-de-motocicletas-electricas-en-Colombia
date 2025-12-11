// client/src/utils/exporters.js

import { buildClientTelemetry } from "./telemetry";

// Exporta JSON de entrada (para backend /routes)
export function buildVehiclesJSON(vehicles, options) {
  return {
    options: {
      profile: options?.profile ?? "driving",
      alternatives: !!options?.alternatives,
      steps: !!options?.steps,
      geometries: "geojson",
      alt_count: options?.alt_count ?? 3,
      alt_share: options?.alt_share ?? 0.6,
      alt_weight: options?.alt_weight ?? 1.4,
      city: options?.city ?? "med",
      traffic: !!options?.traffic,
    },
    vehicles: vehicles.map((v) => ({
      vehicle_id: v.id,
      waypoints: v.waypoints.map((wp) => ({
        coordinates: [wp.coordinates[0], wp.coordinates[1]],
      })),
    })),
  };
}

// Exporta GeoJSON de las rutas calculadas por ORS + simulación
export function buildRoutesFeatureCollection(routes) {
  const features = Object.entries(routes).map(([id, r]) => {
    const coords = r.geometry?.coordinates || [];
    const telemetry = buildClientTelemetry(r);

    // Datos de carga (si vienen del back)
    const chargePoints = Array.isArray(r.chargePoints) ? r.chargePoints : [];
    const chargeSummary = r.chargeSummary || null;
    const chargeChartData = Array.isArray(r.chargeChartData)
      ? r.chargeChartData
      : [];

    return {
      type: "Feature",
      properties: {
        vehicle_id: id,
        summary: r.summary || null,
        telemetry,
        chargePoints,
        chargeSummary,
        chargeChartData,
      },
      geometry: {
        type: "LineString",
        coordinates: coords,
      },
    };
  });

  return {
    type: "FeatureCollection",
    features,
  };
}

// (Opcional) Exporta GeoJSON de los waypoints (como LineString)
export function buildWaypointsFeatureCollection(vehicles) {
  const features = vehicles
    .filter((v) => v.waypoints.length >= 2)
    .map((v) => ({
      type: "Feature",
      properties: { vehicle_id: v.id },
      geometry: {
        type: "LineString",
        coordinates: v.waypoints.map((wp) => [
          wp.coordinates[0],
          wp.coordinates[1],
        ]),
      },
    }));
  return { type: "FeatureCollection", features };
}
