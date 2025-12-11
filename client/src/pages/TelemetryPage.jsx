import React, { useMemo, useRef, useState } from "react";
import { Card, CardContent } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Slider } from "../components/ui/slider";
import { Upload, Undo2, Route, FileJson } from "lucide-react";
import MapView from "../components/map/MapView.jsx";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  AreaChart,
  Area,
  ResponsiveContainer,
} from "recharts";

/* ---------------- Utilidades geo / tiempo ---------------- */
function to2D(coords) {
  if (!Array.isArray(coords)) return [];
  return coords
    .map((c) => [Number(c[0]), Number(c[1])])
    .filter(([lon, lat]) => Number.isFinite(lon) && Number.isFinite(lat));
}

function fromBikesToFC(src) {
  if (!src.bikes || !Array.isArray(src.bikes)) return null;
  const features = [];
  src.bikes.forEach((bikeGroup, gi) => {
    if (!Array.isArray(bikeGroup)) return;
    bikeGroup.forEach((segmento, li) => {
      const coords = segmento?.coords;
      if (!Array.isArray(coords) || coords.length < 2) return;
      const processed = to2D(coords);
      if (processed.length < 2) return;
      const props = {
        vehicle_id: `moto-${gi + 1}`,
        leg: li + 1,
        origen: segmento.origen,
        destino: segmento.destino,
      };
      features.push({
        type: "Feature",
        properties: props,
        geometry: { type: "LineString", coordinates: processed },
      });
    });
  });
  return { type: "FeatureCollection", features };
}

function parseFechaToEpochSeconds(fecha) {
  try {
    if (typeof fecha !== "string") return null;
    const [ddmmyy, hhmmssRaw] = fecha.split(":");
    if (!ddmmyy || !hhmmssRaw) return null;
    const dd = +ddmmyy.slice(0, 2);
    const MM = +ddmmyy.slice(2, 4);
    const yy = +ddmmyy.slice(4, 6);
    const year = 2000 + yy;
    const hh = +hhmmssRaw.slice(0, 2);
    const mm = +hhmmssRaw.slice(2, 4);
    const ss = parseFloat(hhmmssRaw.slice(4));
    const d = new Date(Date.UTC(year, MM - 1, dd, hh, mm, ss));
    const secs = Math.floor(d.getTime() / 1000);
    return Number.isFinite(secs) ? secs : null;
  } catch {
    return null;
  }
}

function haversineKm([lng1, lat1], [lng2, lat2]) {
  const R = 6371;
  const toRad = (x) => (x * Math.PI) / 180;
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lng2 - lng1);
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) ** 2;
  return 2 * R * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

const cumulative = (arr) => {
  let s = 0;
  return arr.map((v) => (s += v));
};

/* ---------------- Página ---------------- */
export default function TelemetryPage() {
  const [fileName, setFileName] = useState("");
  const [geojson, setGeojson] = useState(null);
  const [telemetryRows, setTelemetryRows] = useState([]);
  const [downsample, setDownsample] = useState(1);
  const [chargeSummary, setChargeSummary] = useState(null);
  const [chargePoints, setChargePoints] = useState([]);
  const inputRef = useRef(null);

  function handleFile(e) {
    const f = e.target.files?.[0];
    if (!f) return;
    setFileName(f.name);

    const reader = new FileReader();
    reader.onload = () => {
      try {
        const json = JSON.parse(reader.result);
        let fc = null;
        let rows = null;
        let summary = null;
        let points = [];

        /* ------------------------------------------
         * 1) GeoJSON válido: FeatureCollection
         *    (incluye caso exportado desde el mapa
         *     con properties.telemetry)
         * ------------------------------------------ */
        if (json?.type === "FeatureCollection") {
          fc = json;

          const rowsFromFeatures = [];

          (json.features || []).forEach((feat) => {
            const props = feat?.properties || {};
            const telem = props.telemetry;
            if (Array.isArray(telem)) {
              telem.forEach((p) => {
                const lat = Number(p.lat ?? p.latitude);
                const lng = Number(p.lng ?? p.longitude);
                const alt = Number(
                  p.altitude ?? p.alt ?? p.alt_m ?? p.altitude_m ?? NaN,
                );

                const speed = Number(
                  p.speed_kmh ?? p.speed ?? p.v_kmh ?? NaN,
                );
                const power = Number(
                  p.power_kW ?? p.power ?? p.pw ?? NaN,
                );
                const energy = Number(
                  p.energy_kWh ?? p.energy ?? NaN,
                );
                const soc = Number(p.soc ?? NaN);
                const tEpoch = Number(
                  p.t_epoch ??
                    parseFechaToEpochSeconds(
                      p.fecha ?? p.timestamp ?? null,
                    ) ??
                    NaN,
                );

                rowsFromFeatures.push({
                  i: rowsFromFeatures.length,
                  lat: Number.isFinite(lat) ? lat : null,
                  lng: Number.isFinite(lng) ? lng : null,
                  alt: Number.isFinite(alt) ? alt : null,
                  speed_kmh: Number.isFinite(speed) ? speed : null,
                  power_kW: Number.isFinite(power) ? power : null,
                  energy_kWh: Number.isFinite(energy) ? energy : null,
                  soc: Number.isFinite(soc) ? soc : null,
                  t_epoch: Number.isFinite(tEpoch) ? tEpoch : null,
                });
              });
            }

            // Datos de carga si están en las propiedades
            if (!summary && props.chargeSummary) {
              summary = props.chargeSummary;
            }
            if (Array.isArray(props.chargePoints)) {
              points = points.concat(props.chargePoints);
            }
          });

          if (rowsFromFeatures.length) {
            rows = rowsFromFeatures;
          }

          setChargeSummary(summary || null);
          setChargePoints(points);

          /* ------------------------------------------
           * 2) Formato ORS “bikes”
           * ------------------------------------------ */
        } else if (json?.bikes) {
          fc = fromBikesToFC(json);
          rows = [];
          setChargeSummary(null);
          setChargePoints([]);

          /* ------------------------------------------
           * 3) Formato exportado por Mapa (Rutas):
           *    vehicles_request.json
           * ------------------------------------------ */
        } else if (Array.isArray(json?.vehicles)) {
          const features = [];

          json.vehicles.forEach((v, idx) => {
            const waypoints = Array.isArray(v.waypoints) ? v.waypoints : [];

            const coords = waypoints
              .map((w) => {
                if (
                  Array.isArray(w.coordinates) &&
                  w.coordinates.length >= 2
                ) {
                  const lon = Number(w.coordinates[0]);
                  const lat = Number(w.coordinates[1]);
                  return [lon, lat];
                }

                const lat =
                  w.latitude ?? w.lat ?? w.latitud ?? w.y ?? null;
                const lon =
                  w.longitude ?? w.lng ?? w.lon ?? w.x ?? null;

                return [Number(lon), Number(lat)];
              })
              .filter(
                ([lon, lat]) =>
                  Number.isFinite(lon) && Number.isFinite(lat),
              );

            if (coords.length >= 2) {
              features.push({
                type: "Feature",
                properties: {
                  vehicle_id:
                    v.vehicle_id ||
                    v.id ||
                    v.name ||
                    `vehiculo-${idx + 1}`,
                  source: "map-routes-export",
                },
                geometry: {
                  type: "LineString",
                  coordinates: coords,
                },
              });
            }
          });

          if (features.length) {
            fc = { type: "FeatureCollection", features };
            rows = [];
          }

          setChargeSummary(null);
          setChargePoints([]);

          /* ------------------------------------------
           * 4) Telemetría real:
           *    [ { latitude, longitude, altitude, speed, pw, fecha } ]
           * ------------------------------------------ */
        } else if (
          Array.isArray(json) &&
          json.length > 1 &&
          ("latitude" in json[0] || "lat" in json[0])
        ) {
          const coords = json.map((p) => [
            Number(p.longitude ?? p.lng),
            Number(p.latitude ?? p.lat),
          ]);

          fc = {
            type: "FeatureCollection",
            features: [
              {
                type: "Feature",
                properties: { source: "telemetry" },
                geometry: { type: "LineString", coordinates: coords },
              },
            ],
          };

          rows = json.map((p, i) => ({
            i,
            lat: Number(p.latitude ?? p.lat),
            lng: Number(p.longitude ?? p.lng),
            alt: Number(p.altitude ?? p.alt),
            speed_kmh: Number.isFinite(Number(p.speed))
              ? Number(p.speed)
              : null,
            power_kW: Number.isFinite(Number(p.pw))
              ? Number(p.pw)
              : null,
            energy_kWh: null,
            soc: null,
            t_epoch: parseFechaToEpochSeconds(p.fecha),
          }));

          setChargeSummary(null);
          setChargePoints([]);
        }

        /* ------------------------------------------
         * Si ningún formato fue reconocido
         * ------------------------------------------ */
        if (!fc) {
          alert(
            "Formato no reconocido.\nUsa: GeoJSON (con telemetría opcional), bikes, vehicles o lista de puntos.",
          );
          return;
        }

        setGeojson(fc);
        setTelemetryRows(rows || []);
      } catch (err) {
        console.error(err);
        alert("Error procesando JSON: " + err.message);
      }
    };

    reader.readAsText(f);
  }

  function clearAll() {
    setFileName("");
    setGeojson(null);
    setTelemetryRows([]);
    setChargeSummary(null);
    setChargePoints([]);
  }

  /* ---------- Cálculos/Métricas/datasets ---------- */
  const {
    totalKm,
    totalTimeMin,
    totalEnergy_kWh,
    chart_time_power,
    chart_speed,
    chart_soc,
    chart_energy_vs_dist,
  } = useMemo(() => {
    const coords = geojson?.features?.[0]?.geometry?.coordinates || [];
    const segKm = [];
    for (let i = 0; i < coords.length - 1; i++) {
      segKm.push(haversineKm(coords[i], coords[i + 1]));
    }
    const cumDistKm = cumulative(segKm);
    const totalKm = segKm.reduce((a, b) => a + b, 0);

    if (!telemetryRows?.length) {
      return {
        totalKm,
        totalTimeMin: 0,
        totalEnergy_kWh: 0,
        chart_time_power: [],
        chart_speed: [],
        chart_soc: [],
        chart_energy_vs_dist: cumDistKm.map((v, i) => ({
          i,
          cum_km: v,
          cum_kWh: 0,
        })),
      };
    }

    const rows = [...telemetryRows];
    const haveEpoch = rows.every((r) => r.t_epoch !== null);
    if (haveEpoch) rows.sort((a, b) => a.t_epoch - b.t_epoch);
    const ds = Math.max(1, Math.round(downsample));
    const dsRows = rows.filter((_, idx) => idx % ds === 0);

    let cum_kWh = 0;
    let totalSeconds = 0;
    const t0 = haveEpoch ? dsRows[0].t_epoch : 0;

    const chart_time_power = [];
    const chart_speed = [];
    const chart_soc = [];
    const chart_energy_vs_dist = [];

    const cumSegKm = cumulative(segKm);

    for (let i = 0; i < dsRows.length; i++) {
      const r = dsRows[i];
      const t = haveEpoch ? r.t_epoch - t0 : i;

      if (i > 0) {
        const prev = dsRows[i - 1];
        let dt = haveEpoch ? r.t_epoch - prev.t_epoch : 1;
        if (!Number.isFinite(dt) || dt <= 0) dt = 1;
        totalSeconds += dt;

        const P = Number.isFinite(prev.power_kW) ? prev.power_kW : 0;
        cum_kWh += P * (dt / 3600);
      }

      chart_time_power.push({
        t_s: t,
        power_kW: Number.isFinite(r.power_kW) ? r.power_kW : 0,
      });
      chart_speed.push({
        t_s: t,
        speed_kmh: Number.isFinite(r.speed_kmh) ? r.speed_kmh : 0,
      });
      chart_soc.push({
        t_s: t,
        soc: Number.isFinite(r.soc) ? r.soc : null,
      });

      const idxDist = Math.min(i, Math.max(0, cumSegKm.length - 1));
      chart_energy_vs_dist.push({
        i: i + 1,
        cum_km: cumSegKm[idxDist] || 0,
        cum_kWh: cum_kWh,
      });
    }

    return {
      totalKm,
      totalTimeMin: totalSeconds / 60,
      totalEnergy_kWh: cum_kWh,
      chart_time_power,
      chart_speed,
      chart_soc,
      chart_energy_vs_dist,
    };
  }, [geojson, telemetryRows, downsample]);

  /* ---------- LAYOUT ESTILO MAPA (Rutas) ---------- */

  return (
    <section className="page">
      {/* Bloque superior: panel + mapa */}
      <div className="page-main">
        {/* Sidebar de telemetría */}
        <aside className="sidebar">
          <div className="card telemetry-card">
            {/* Header del panel */}
            <div className="telemetry-card-header">
              <div className="telemetry-title-block">
                <div className="telemetry-icon-badge">
                  <Route className="w-4 h-4" />
                </div>
                <div>
                  <h2 className="panel-title" style={{ margin: 0 }}>
                    Telemetría
                  </h2>
                  <p className="telemetry-subtitle">
                    Carga un archivo JSON con datos de la moto o una ruta
                    exportada desde el mapa para ver la trayectoria y las
                    curvas de potencia, velocidad, SoC y energía.
                  </p>
                </div>
              </div>
            </div>

            {/* input oculto */}
            <input
              ref={inputRef}
              type="file"
              accept=".json,.geojson"
              className="hidden"
              onChange={handleFile}
            />

            {/* Caja de archivo */}
            <div className="telemetry-file-row">
              <FileJson className="w-4 h-4" />
              <span className="telemetry-file-name">
                {fileName || "Ningún archivo seleccionado"}
              </span>
            </div>

            {/* Métricas principales */}
            <div className="telemetry-metrics-grid">
              <Card className="rounded-xl shadow-none border telemetry-metric-card">
                <CardContent className="p-2">
                  <div className="telemetry-metric-label">Distancia</div>
                  <div className="telemetry-metric-value">
                    {(totalKm ?? 0).toFixed(2)} km
                  </div>
                </CardContent>
              </Card>

              <Card className="rounded-xl shadow-none border telemetry-metric-card">
                <CardContent className="p-2">
                  <div className="telemetry-metric-label">Tiempo</div>
                  <div className="telemetry-metric-value">
                    {(totalTimeMin ?? 0).toFixed(1)} min
                  </div>
                </CardContent>
              </Card>

              <Card className="rounded-xl shadow-none border telemetry-metric-card">
                <CardContent className="p-2">
                  <div className="telemetry-metric-label">Energía</div>
                  <div className="telemetry-metric-value">
                    {(totalEnergy_kWh ?? 0).toFixed(3)} kWh
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Downsample */}
            <div className="telemetry-downsample">
              <label className="telemetry-downsample-label">
                <span>Downsample</span>
                <span className="telemetry-downsample-value">
                  {downsample}x
                </span>
              </label>
              <Slider
                value={[downsample]}
                onValueChange={([v]) =>
                  setDownsample(Math.max(1, Math.round(v)))
                }
                min={1}
                max={10}
                step={1}
              />
            </div>

            <p className="telemetry-hint">
              Puedes usar:
              <br />
              • GeoJSON exportado desde el mapa (con telemetría y puntos de
              carga) <br />
              • Archivos de telemetría reales en formato JSON.
            </p>

            {/* BOTONES ABAJO */}
            <div className="telemetry-actions telemetry-actions-bottom">
              <Button
                variant="outline"
                size="sm"
                onClick={() => inputRef.current?.click()}
                className="btn ghost"
              >
                <Upload className="w-4 h-4 mr-1" /> Cargar
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={clearAll}
                disabled={!geojson && !fileName}
                className="btn ghost"
              >
                <Undo2 className="w-4 h-4 mr-1" /> Limpiar
              </Button>
            </div>
          </div>
        </aside>

        {/* Mapa a la derecha */}
        <div className="map-wrapper">
          <MapView
            vehicles={[]}
            routes={{}}
            importedGeoJSON={geojson}
            drawOnly={true}
          />
        </div>
      </div>

      {/* Bloque inferior: gráficas de telemetría (layout vertical tipo MapPage) */}
      <section className="stats-section">
        <div className="stats-header">
          <h2>Estadísticas de la telemetría</h2>
        </div>

        <div className="stats-layout">
          {/* === Fila 1: Resumen general (full width) === */}
          <section className="stats-row">
            <div className="stats-card stats-card-full">
              <h3>Resumen general</h3>
              {geojson ? (
                <ul>
                  <li>
                    <strong>Distancia total:</strong>{" "}
                    {Number.isFinite(totalKm)
                      ? `${totalKm.toFixed(2)} km`
                      : "N/D"}
                  </li>
                  <li>
                    <strong>Tiempo total:</strong>{" "}
                    {Number.isFinite(totalTimeMin)
                      ? `${totalTimeMin.toFixed(1)} min`
                      : "N/D"}
                  </li>
                  <li>
                    <strong>Energía estimada:</strong>{" "}
                    {Number.isFinite(totalEnergy_kWh)
                      ? `${totalEnergy_kWh.toFixed(3)} kWh`
                      : "N/D"}
                  </li>
                  <li>
                    <strong>Puntos de telemetría:</strong>{" "}
                    {telemetryRows.length || "N/D"}
                  </li>
                </ul>
              ) : (
                <p>Aún no hay telemetría cargada.</p>
              )}
            </div>
          </section>

          {/* === Fila 2: Potencia + Velocidad === */}
          <section className="stats-row stats-row-two">
            <div className="stats-card">
              <h3>Potencia vs tiempo</h3>
              {chart_time_power.length ? (
                <ResponsiveContainer width="100%" height={220}>
                  <AreaChart data={chart_time_power}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="t_s"
                      tick={{ fontSize: 10 }}
                      label={{
                        value: "Tiempo (s)",
                        position: "insideBottomRight",
                        offset: -4,
                      }}
                    />
                    <YAxis
                      tick={{ fontSize: 10 }}
                      label={{
                        value: "kW",
                        angle: -90,
                        position: "insideLeft",
                      }}
                    />
                    <Tooltip />
                    <Area
                      type="monotone"
                      dataKey="power_kW"
                      name="Potencia (kW)"
                      fill="#e5e7eb"
                      stroke="#4b5563"
                      strokeWidth={2}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              ) : (
                <p>No hay datos de potencia aún.</p>
              )}
            </div>

            <div className="stats-card">
              <h3>Velocidad vs tiempo</h3>
              {chart_speed.length ? (
                <ResponsiveContainer width="100%" height={220}>
                  <LineChart data={chart_speed}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="t_s"
                      tick={{ fontSize: 10 }}
                      label={{
                        value: "Tiempo (s)",
                        position: "insideBottomRight",
                        offset: -4,
                      }}
                    />
                    <YAxis
                      tick={{ fontSize: 10 }}
                      label={{
                        value: "km/h",
                        angle: -90,
                        position: "insideLeft",
                      }}
                    />
                    <Tooltip />
                    <Line
                      type="monotone"
                      dataKey="speed_kmh"
                      name="Velocidad (km/h)"
                      dot={false}
                      strokeWidth={2}
                    />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <p>No hay datos de velocidad aún.</p>
              )}
            </div>
          </section>

          {/* === Fila 3: SoC + Energía acumulada === */}
          <section className="stats-row stats-row-two">
            <div className="stats-card">
              <h3>SoC vs tiempo</h3>
              {chart_soc.length ? (
                <ResponsiveContainer width="100%" height={220}>
                  <LineChart data={chart_soc}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="t_s"
                      tick={{ fontSize: 10 }}
                      label={{
                        value: "Tiempo (s)",
                        position: "insideBottomRight",
                        offset: -4,
                      }}
                    />
                    <YAxis
                      tick={{ fontSize: 10 }}
                      label={{
                        value: "SoC",
                        angle: -90,
                        position: "insideLeft",
                      }}
                    />
                    <Tooltip />
                    <Line
                      type="monotone"
                      dataKey="soc"
                      name="SoC"
                      dot={false}
                      strokeWidth={2}
                    />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <p>No hay datos de SoC aún.</p>
              )}
            </div>

            <div className="stats-card">
              <h3>Energía acumulada vs distancia</h3>
              {chart_energy_vs_dist.length ? (
                <ResponsiveContainer width="100%" height={220}>
                  <AreaChart data={chart_energy_vs_dist}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="cum_km"
                      tick={{ fontSize: 10 }}
                      label={{
                        value: "Distancia (km)",
                        position: "insideBottomRight",
                        offset: -4,
                      }}
                    />
                    <YAxis
                      tick={{ fontSize: 10 }}
                      label={{
                        value: "kWh",
                        angle: -90,
                        position: "insideLeft",
                      }}
                    />
                    <Tooltip />
                    <Area
                      type="monotone"
                      dataKey="cum_kWh"
                      name="Energía acumulada (kWh)"
                      fill="#e5e7eb"
                      stroke="#6b7280"
                      strokeWidth={2}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              ) : (
                <p>No hay datos de energía aún.</p>
              )}
            </div>
          </section>

          {/* === Fila 4: Puntos de carga === */}
        </div>
      </section>
    </section>
  );
}