import React, { useState, useMemo } from "react";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import FlotaMapView from "../components/map/FlotaMapView.jsx";
import { postFlota } from "../services/api.js";
import { COLORS } from "../utils/colors.js";

const CHARGING_ROUTE_COLOR = "#7C3AED";
const getColor = (i) => COLORS[i % COLORS.length];

// ─── small helpers ────────────────────────────────────────────────────────────

function StatCard({ title, children, full = false }) {
  return (
    <div className={`stats-card${full ? " stats-card-full" : ""}`}>
      <h3 style={{ margin: "0 0 12px", fontSize: "0.95rem", fontWeight: 700 }}>
        {title}
      </h3>
      {children}
    </div>
  );
}

function EmptyChart({ message }) {
  return (
    <p style={{ color: "#9ca3af", fontSize: 13, margin: 0 }}>{message}</p>
  );
}

// Custom tooltip that shows kWh nicely
function KwhTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div
      style={{
        background: "#fff",
        border: "1px solid #e5e7eb",
        borderRadius: 8,
        padding: "8px 12px",
        fontSize: 12,
        boxShadow: "0 4px 12px rgba(0,0,0,0.08)",
      }}
    >
      <p style={{ margin: "0 0 4px", fontWeight: 600 }}>Tramo {label}</p>
      {payload.map((p) => (
        <p key={p.dataKey} style={{ margin: "2px 0", color: p.color }}>
          {p.name}: <strong>{Number(p.value).toFixed(3)} kWh</strong>
        </p>
      ))}
    </div>
  );
}

// ─── main page ────────────────────────────────────────────────────────────────

export default function FlotillaPage() {
  const [waypoints, setWaypoints] = useState([]);
  const [routeData, setRouteData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [city] = useState("med");

  // Vehicles for the map
  const vehicles = useMemo(
    () =>
      waypoints.map((coord, idx) => ({
        id: `waypoint-${idx}`,
        waypoints: [{ coordinates: coord }],
        color: COLORS[idx % COLORS.length],
      })),
    [waypoints]
  );

  // Route segments for the map
  const routes = useMemo(() => {
    if (!routeData?.ruta) return {};
    const obj = {};
    const full = routeData.ruta;

    (routeData.ruta_carga ?? []).forEach((seg, idx) => {
      const coords = full.slice(seg[0], seg[1] + 1);
      if (coords.length)
        obj[`carga-${idx}`] = {
          geometry: { type: "LineString", coordinates: coords },
          color: CHARGING_ROUTE_COLOR,
        };
    });

    (routeData.ruta_nodos ?? []).forEach((seg, idx) => {
      const coords = full.slice(seg[0], seg[1] + 1);
      if (coords.length)
        obj[`nodo-${idx}`] = {
          geometry: { type: "LineString", coordinates: coords },
          color: COLORS[idx % COLORS.length],
        };
    });

    return obj;
  }, [routeData]);

  // ── consumption_data derived charts ──────────────────────────────────────────
  const cd = routeData?.consumption_data ?? [];

  // Chart 1 – Battery level profile (energy_in_kwh across legs)
  const batteryData = useMemo(
    () =>
      cd.map((d) => ({
        leg: d.leg,
        "Batería entrada (kWh)": d.energy_in_kwh,
        "Batería salida (kWh)": d.energy_out_kwh,
      })),
    [cd]
  );

  // Chart 2 – Energy consumed per leg (bar)
  const consumedData = useMemo(
    () =>
      cd.map((d) => ({
        leg: d.leg,
        "Consumo (kWh)": d.consumed_kwh,
        swap: d.is_swap,
      })),
    [cd]
  );

  // Chart 3 – Stacked: consumed vs recharged (energy balance)
  const balanceData = useMemo(
    () =>
      cd.map((d) => ({
        leg: d.leg,
        "Consumido (kWh)": d.consumed_kwh,
        "Recargado (kWh)": d.recharged_kwh,
      })),
    [cd]
  );

  // Summary KPIs
  const summary = useMemo(() => {
    if (!cd.length) return null;
    const totalConsumed = cd.reduce((a, d) => a + d.consumed_kwh, 0);
    const totalRecharged = cd.reduce((a, d) => a + d.recharged_kwh, 0);
    const totalTravelMin = cd.reduce((a, d) => a + d.travel_time_min, 0);
    const totalChargeMin = cd.reduce((a, d) => a + d.charging_time_min, 0);
    const count = cd.filter((d) => d.is_swap).length;
    const swaps = Math.max(0, count - 1);
    const minBattery = Math.min(...cd.map((d) => d.energy_out_kwh));
    return {
      totalConsumed,
      totalRecharged,
      totalTravelMin,
      totalChargeMin,
      swaps,
      minBattery,
      legs: cd.length,
    };
  }, [cd]);

  // ── handlers ──────────────────────────────────────────────────────────────────
  const handleAddWaypoint = (coord) => {
    setWaypoints((prev) => [...prev, coord]);
    setRouteData(null);
    setError(null);
  };

  const removeWaypointAt = (vehicleIdx) => {
    setWaypoints((prev) => prev.filter((_, i) => i !== vehicleIdx));
    setRouteData(null);
  };

  const clearAll = () => {
    setWaypoints([]);
    setRouteData(null);
    setError(null);
  };

  const handleCalculate = async () => {
    if (waypoints.length < 2) {
      setError("Selecciona al menos 2 puntos.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const payload = { waypoints: waypoints.map((w) => ({ coordinates: w })) };
      const result = await postFlota(payload);
      setRouteData(result);
    } catch (err) {
      console.error(err);
      setError("Error al calcular ruta de flotilla.");
    } finally {
      setLoading(false);
    }
  };

  // ── render ────────────────────────────────────────────────────────────────────
  return (
    <section className="page">
      {/* ── top: sidebar + map ────────────────────────────────────────────── */}
      <div className="page-main">
        <aside className="sidebar">
          <div className="card">
            <h2 className="panel-title">Flotilla</h2>
            <div className="divider" />

            <div className="kv">
              <span className="k">Puntos seleccionados:</span>
              <span className="v">{waypoints.length}</span>
            </div>

            <div className="row" style={{ marginTop: "1rem" }}>
              <button
                className="btn"
                onClick={handleCalculate}
                disabled={loading || waypoints.length < 2}
              >
                {loading ? "Cargando…" : "Calcular Flotilla"}
              </button>
            </div>

            {error && (
              <div style={{ marginTop: 10, fontSize: 13, color: "#b91c1c" }}>
                {error}
              </div>
            )}

            <div className="row" style={{ marginTop: "0.5rem" }}>
              <button
                className="btn ghost"
                onClick={clearAll}
                disabled={loading || waypoints.length === 0}
              >
                Limpiar
              </button>
            </div>

            {/* Results */}
            {routeData && (
              <>
                <div className="divider" />
                <h3
                  className="panel-title"
                  style={{ fontSize: "1rem", marginBottom: "0.5rem" }}
                >
                  Resultados
                </h3>

                <div className="kv">
                  <span className="k">Distancia:</span>
                  <span className="v">
                    {(routeData.distancia / 1000).toFixed(2)} km
                  </span>
                </div>
                <div className="kv">
                  <span className="k">Duración:</span>
                  <span className="v">
                    {Math.round(routeData.duracion / 60)} min
                  </span>
                </div>

                {routeData.viajes?.length > 0 && (
                  <>
                    <div className="divider" />
                    <h3
                      className="panel-title"
                      style={{ fontSize: "1rem", marginBottom: "0.5rem" }}
                    >
                      Orden de visitas
                    </h3>
                    <div style={{ fontSize: "0.875rem", lineHeight: 1.5 }}>
                      {routeData.viajes.map((punto, idx) => (
                        <div key={idx} style={{ marginBottom: "0.25rem" }}>
                          <span style={{ fontWeight: 500 }}>{idx + 1}.</span>
                          {punto === 1 || punto === "1"
                            ? " Depósito"
                            : ` Punto ${punto}`}
                        </div>
                      ))}
                    </div>
                  </>
                )}
              </>
            )}

            <div className="divider" />
            <div className="small">
              Selecciona puntos en el mapa para planificar una ruta de flotilla.
            </div>
          </div>
        </aside>

        <div className="map-wrapper" style={{ minHeight: "75vh" }}>
          <FlotaMapView
            vehicles={vehicles}
            routes={routes}
            handleAddWaypoint={handleAddWaypoint}
            city={city}
          />
        </div>
      </div>

      {/* ── bottom: consumption charts (only after a solve) ───────────────── */}
      {routeData && (
        <section
          className="stats-section"
          style={{ padding: "0 16px 32px" }}
        >
          {/* Header */}
          <div className="stats-header">
            <h2 style={{ margin: 0, fontSize: "1.25rem", fontWeight: 800 }}>
              Análisis de consumo energético
            </h2>
          </div>

          <div className="stats-layout">
            {/* ── Row 1: KPI summary (full width) ───────────────────────── */}
            <section className="stats-row">
              <StatCard title="Resumen de consumo" full>
                {summary ? (
                  <div
                    style={{
                      display: "grid",
                      gridTemplateColumns:
                        "repeat(auto-fit, minmax(140px, 1fr))",
                      gap: 12,
                    }}
                  >
                    {[
                      {
                        label: "Consumo total",
                        value: `${summary.totalConsumed.toFixed(3)} kWh`,
                        color: getColor(0),
                      },
                      {
                        label: "Recargado total",
                        value: `${summary.totalRecharged.toFixed(3)} kWh`,
                        color: getColor(1),
                      },
                      {
                        label: "Batería mín. salida",
                        value: `${summary.minBattery.toFixed(3)} kWh`,
                        color: getColor(2),
                      },
                      {
                        label: "Tramos recorridos",
                        value: summary.legs,
                        color: getColor(3),
                      },
                      {
                        label: "Swaps de batería",
                        value: summary.swaps,
                        color: "#7C3AED",
                      },
                      {
                        label: "Tiempo en carga",
                        value: `${summary.totalChargeMin.toFixed(1)} min`,
                        color: getColor(5),
                      },
                    ].map(({ label, value, color }) => (
                      <div
                        key={label}
                        style={{
                          background: "#f9fafb",
                          border: "1px solid #e5e7eb",
                          borderRadius: 10,
                          padding: "10px 14px",
                          borderLeft: `4px solid ${color}`,
                        }}
                      >
                        <div
                          style={{
                            fontSize: 11,
                            color: "#6b7280",
                            marginBottom: 4,
                          }}
                        >
                          {label}
                        </div>
                        <div
                          style={{
                            fontSize: 16,
                            fontWeight: 700,
                            color: "#111827",
                          }}
                        >
                          {value}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <EmptyChart message="Sin datos de consumo." />
                )}
              </StatCard>
            </section>

            {/* ── Row 2: Battery profile + Per-leg consumption ──────────── */}
            <section className="stats-row stats-row-two">
              <StatCard title="Perfil de batería por tramo">
                {batteryData.length ? (
                  <ResponsiveContainer width="100%" height={220}>
                    <LineChart
                      data={batteryData}
                      margin={{ top: 8, right: 20, left: 0, bottom: 0 }}
                    >
                      <XAxis
                        dataKey="leg"
                        tick={{ fontSize: 10 }}
                        label={{
                          value: "Tramo",
                          position: "insideBottomRight",
                          offset: -4,
                          fontSize: 10,
                        }}
                      />
                      <YAxis
                        tick={{ fontSize: 10 }}
                        label={{
                          value: "kWh",
                          angle: -90,
                          position: "insideLeft",
                          fontSize: 10,
                        }}
                      />
                      <Tooltip content={<KwhTooltip />} />
                      <Legend wrapperStyle={{ fontSize: 11 }} />
                      <Line
                        type="monotone"
                        dataKey="Batería entrada (kWh)"
                        stroke={getColor(0)}
                        strokeWidth={2}
                        dot={{ r: 3 }}
                      />
                      <Line
                        type="monotone"
                        dataKey="Batería salida (kWh)"
                        stroke={getColor(1)}
                        strokeWidth={2}
                        strokeDasharray="4 2"
                        dot={{ r: 3 }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                ) : (
                  <EmptyChart message="No hay datos de batería todavía." />
                )}
              </StatCard>

              <StatCard title="Consumo por tramo (kWh)">
                {consumedData.length ? (
                  <ResponsiveContainer width="100%" height={220}>
                    <BarChart
                      data={consumedData}
                      margin={{ top: 8, right: 20, left: 0, bottom: 0 }}
                    >
                      <XAxis
                        dataKey="leg"
                        tick={{ fontSize: 10 }}
                        label={{
                          value: "Tramo",
                          position: "insideBottomRight",
                          offset: -4,
                          fontSize: 10,
                        }}
                      />
                      <YAxis
                        tick={{ fontSize: 10 }}
                        label={{
                          value: "kWh",
                          angle: -90,
                          position: "insideLeft",
                          fontSize: 10,
                        }}
                      />
                      <Tooltip content={<KwhTooltip />} />
                      <Legend wrapperStyle={{ fontSize: 11 }} />
                      <Bar
                        dataKey="Consumo (kWh)"
                        fill={getColor(2)}
                        radius={[4, 4, 0, 0]}
                      />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <EmptyChart message="No hay datos de consumo todavía." />
                )}
              </StatCard>
            </section>

            {/* ── Row 3: Energy balance stacked + Swap events ───────────── */}
            <section className="stats-row stats-row-two">
              <StatCard title="Balance energético por tramo (consumido vs recargado)">
                {balanceData.length ? (
                  <ResponsiveContainer width="100%" height={220}>
                    <BarChart
                      data={balanceData}
                      margin={{ top: 8, right: 20, left: 0, bottom: 0 }}
                    >
                      <XAxis
                        dataKey="leg"
                        tick={{ fontSize: 10 }}
                        label={{
                          value: "Tramo",
                          position: "insideBottomRight",
                          offset: -4,
                          fontSize: 10,
                        }}
                      />
                      <YAxis
                        tick={{ fontSize: 10 }}
                        label={{
                          value: "kWh",
                          angle: -90,
                          position: "insideLeft",
                          fontSize: 10,
                        }}
                      />
                      <Tooltip content={<KwhTooltip />} />
                      <Legend wrapperStyle={{ fontSize: 11 }} />
                      <Bar
                        dataKey="Consumido (kWh)"
                        stackId="balance"
                        fill={getColor(3)}
                        radius={[0, 0, 0, 0]}
                      />
                      <Bar
                        dataKey="Recargado (kWh)"
                        stackId="balance"
                        fill="#7C3AED"
                        radius={[4, 4, 0, 0]}
                      />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <EmptyChart message="No hay datos de balance todavía." />
                )}
              </StatCard>

              <StatCard title="Eventos de swap de batería">
                {summary?.swaps > 0 ? (
                  <>
                    <p
                      style={{
                        fontSize: 13,
                        color: "#6b7280",
                        marginBottom: 12,
                      }}
                    >
                      Los tramos marcados en morado requirieron un intercambio
                      de batería en el depósito.
                    </p>
                    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                      {cd
                        .filter((d) => d.is_swap)
                        .map((d) => (
                          <div
                            key={d.leg}
                            style={{
                              display: "flex",
                              justifyContent: "space-between",
                              alignItems: "center",
                              background: "#f5f3ff",
                              border: "1px solid #ddd6fe",
                              borderRadius: 8,
                              padding: "8px 12px",
                              fontSize: 13,
                            }}
                          >
                            <span style={{ fontWeight: 600 }}>
                              Tramo {d.leg} →{" "}
                              {d.arc[0] === 0
                                ? "Depósito"
                                : `Nodo ${d.arc[0]}`}{" "}
                              ➜{" "}
                              {d.arc[1] === 0
                                ? "Depósito"
                                : `Nodo ${d.arc[1]}`}
                            </span>
                            <span>
                              +{d.recharged_kwh.toFixed(3)} kWh ·{" "}
                              {d.charging_time_min.toFixed(1)} min
                            </span>
                          </div>
                        ))}
                    </div>
                  </>
                ) : (
                  <EmptyChart message="Esta ruta no realizó swaps de batería." />
                )}
              </StatCard>
            </section>
          </div>
        </section>
      )}
    </section>
  );
}
