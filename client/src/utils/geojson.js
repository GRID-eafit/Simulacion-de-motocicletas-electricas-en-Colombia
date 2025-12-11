export function vehiclesToFeatureCollection(vehicles) {
  const features = vehicles
    .filter(v => v.waypoints.length >= 2)
    .map(v => ({
      type: "Feature",
      properties: { vehicle_id: v.id },
      geometry: {
        type: "LineString",
        coordinates: v.waypoints.map(wp => {
          const c = wp.coordinates || [];
          return [c[0], c[1]]; // fuerza 2D al exportar
        })
      }
    }));
  return { type: "FeatureCollection", features };
}

export function featureCollectionToVehicles(fc) {
  if (!fc || fc.type !== "FeatureCollection" || !Array.isArray(fc.features)) {
    throw new Error("GeoJSON inválido: se esperaba FeatureCollection");
  }
  const vehicles = [];
  let i = 1;
  for (const feat of fc.features) {
    if (feat?.geometry?.type !== "LineString") continue;
    const id = feat.properties?.vehicle_id || `moto-${i++}`;
    const waypoints = (feat.geometry.coordinates || []).map(coord => ({
      coordinates: [coord[0], coord[1]] // fuerza 2D al importar
    }));
    vehicles.push({ id, waypoints });
  }
  return vehicles;
}