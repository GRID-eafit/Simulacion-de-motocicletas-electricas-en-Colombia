// client/src/utils/telemetry.js

export function buildClientTelemetry(route) {
  const coords = route.geometry?.coordinates || [];
  const props = route.properties || {};

  const potencia = Array.isArray(props.potencia) ? props.potencia : [];
  const soc = Array.isArray(props.soc) ? props.soc : [];
  const speeds = Array.isArray(props.speeds) ? props.speeds : [];
  const energySeg = Array.isArray(props.energy_kwh_segment)
    ? props.energy_kwh_segment
    : [];
  const timeSeg = Array.isArray(props.time_s_segment)
    ? props.time_s_segment
    : null; // si el back lo manda por segmento

  const telemetry = [];
  let cumEnergy = 0;
  let cumTime = 0;

  for (let i = 0; i < coords.length; i++) {
    const c = coords[i] || [];
    const lon = Number(c[0]);
    const lat = Number(c[1]);
    const alt = c.length > 2 ? Number(c[2]) : null;

    const pW = Number(potencia[i] ?? NaN);
    const power_kW = Number.isFinite(pW) ? pW / 1000 : null;

    const socVal = Number(soc[i] ?? NaN);
    const socClean = Number.isFinite(socVal) ? socVal : null;

    const vVal = Number(speeds[i] ?? NaN);
    const speed_kmh = Number.isFinite(vVal) ? vVal : null;

    const eSeg = Number(energySeg[i] ?? NaN);
    if (Number.isFinite(eSeg)) {
      cumEnergy += eSeg;
    }
    const energy_kWh = cumEnergy || null;

    let dt = 1;
    if (timeSeg) {
      const segDt = Number(timeSeg[i] ?? NaN);
      if (Number.isFinite(segDt) && segDt > 0) {
        dt = segDt;
      }
    }
    cumTime += dt;
    const t_epoch = cumTime; // tiempo sintético acumulado en segundos

    telemetry.push({
      lat: Number.isFinite(lat) ? lat : null,
      lng: Number.isFinite(lon) ? lon : null,
      altitude: Number.isFinite(alt) ? alt : null,
      power_kW,
      soc: socClean,
      speed_kmh,
      energy_kWh,
      t_epoch,
    });
  }

  return telemetry;
}
