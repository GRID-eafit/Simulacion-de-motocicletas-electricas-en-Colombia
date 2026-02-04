// client/src/pages/CostsModelPage.jsx
import React, { useMemo, useState } from "react";
import { MapContainer, TileLayer, Marker, Polyline, useMapEvents } from "react-leaflet";
import L from "leaflet";
import { Button } from "../components/ui/button";
import { Calculator, Undo2, Trash2, MapPin, Info, AlertTriangle, CheckCircle2 } from "lucide-react";
import { makeColoredIcon } from "../utils/icons";
import { COLORS } from "../utils/colors";

const VITE_API_URL = import.meta.env.VITE_API_URL;

// Leaflet default icon fix
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

function to2D(coords) {
  if (!Array.isArray(coords)) return [];
  return coords
    .map((c) => [Number(c[0]), Number(c[1])])
    .filter(([lng, lat]) => Number.isFinite(lng) && Number.isFinite(lat));
}

function ClickToAdd({ onAdd }) {
  useMapEvents({
    click(e) {
      const lng = +e.latlng.lng.toFixed(6);
      const lat = +e.latlng.lat.toFixed(6);
      onAdd?.([lng, lat]);
    },
  });
  return null;
}

function money(n) {
  const v = Number(n);
  if (!Number.isFinite(v)) return "N/D";
  return "$" + v.toLocaleString("es-CO", { maximumFractionDigits: 0 }) + " COP";
}

function fmtVal(n, dec = 2, suffix = '') {
  const v = Number(n);
  if (!Number.isFinite(v)) return "N/D";
  return v.toLocaleString("es-CO", { minimumFractionDigits: dec, maximumFractionDigits: dec }) + suffix;
}

function StatRow({ label, value, subValue, highlight, color }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", padding: "6px 0", borderBottom: "1px solid #f1f5f9" }}>
      <span style={{ color: "#64748b", fontSize: '0.9rem' }}>{label}</span>
      <div style={{ textAlign: "right" }}>
        <div style={{ fontWeight: highlight ? 700 : 500, color: color || (highlight ? "#0f172a" : "#334155"), fontSize: '0.95rem' }}>
          {value}
        </div>
        {subValue && <div style={{ fontSize: "0.8rem", color: "#94a3b8" }}>{subValue}</div>}
      </div>
    </div>
  );
}

export default function ModeloCostosPage() {
  const center = useMemo(() => [6.2442, -75.5812], []);
  const [waypoints, setWaypoints] = useState([]);

  const [routeLine, setRouteLine] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Defaults (used only if inference fails, handled by backend)
  const municipio = "Medellín";
  const estrato = "3";
  const motivo = "Trabajo";

  function addPoint(p) {
    if (waypoints.length >= 2) {
      if (confirm("Ya seleccionaste origen y destino. ¿Quieres limpiar y empezar de nuevo?")) {
        clearAll();
        setWaypoints([p]);
      }
      return;
    }
    setWaypoints((prev) => [...prev, p]);
    resetResults();
  }

  function resetResults() {
    setRouteLine(null);
    setAnalysis(null);
    setError(null);
  }

  function undoPoint() {
    setWaypoints((prev) => prev.slice(0, -1));
    resetResults();
  }

  function clearAll() {
    setWaypoints([]);
    resetResults();
  }

  async function computeRouteAndCosts() {
    if (waypoints.length < 2) return;
    setLoading(true);
    setError(null);
    setAnalysis(null);

    const coords = to2D(waypoints);

    try {
      // 1. Get Route Geometry from ORS
      const r1 = await fetch(`${VITE_API_URL}/route_only`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ coords, profile: "driving-car" }),
      });
      if (r1.ok) {
        const routeData = await r1.json();
        console.log("Route data received:", routeData);
        if (routeData.geometry?.coordinates?.length > 0) {
          setRouteLine(routeData.geometry);
          console.log("Route line set successfully");
        } else {
          console.error("No coordinates in route geometry:", routeData.geometry);
        }
      } else {
        const errorText = await r1.text();
        console.error("route_only failed:", r1.status, errorText);
      }

      // 2. Call Simulation Model
      const r2 = await fetch(`${VITE_API_URL}/costs/compute`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          coords,
          municipio_origen: municipio,
          municipio_destino: municipio,
          estrato,
          motivo_viaje: motivo
        }),
      });

      if (!r2.ok) {
        const t = await r2.text();
        throw new Error(`Error en servidor: ${r2.status} - ${t}`);
      }

      const data = await r2.json();
      if (data.error && !data.fallback) {
        throw new Error(data.details || data.error);
      }
      setAnalysis(data);

    } catch (err) {
      console.error(err);
      setError(err.message || "Error desconocido al calcular");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="page">
      <div className="page-main">
        {/* Sidebar */}
        <aside className="sidebar">
          <div className="stats-card" style={{ marginBottom: 16 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
              <div style={{ background: '#f1f5f9', padding: 8, borderRadius: 8 }}>
                <Calculator className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <h3 style={{ margin: 0, fontSize: '1rem' }}>Simulador de Viaje</h3>
                <p style={{ margin: 0, fontSize: '0.8rem', color: '#64748b' }}>
                  Selecciona Origen y Destino.
                </p>
              </div>
            </div>

            <div style={{ display: "grid", gap: 12 }}>
              <div style={{ fontSize: '0.85rem', color: '#475569', lineHeight: 1.4 }}>
                El sistema detectará automáticamente el <strong>Municipio</strong> y <strong>Estrato</strong> de los puntos seleccionados.
              </div>

              {/* Actions */}
              <div style={{ display: "grid", gap: 8 }}>
                <Button
                  onClick={computeRouteAndCosts}
                  disabled={waypoints.length < 2 || loading}
                  className="btn"
                  style={{ background: waypoints.length < 2 ? '#94a3b8' : COLORS[0], color: 'white' }}
                >
                  <Calculator className="w-4 h-4 mr-2" />
                  {loading ? "Calculando..." : "Calcular Costos"}
                </Button>

                <div style={{ display: "flex", gap: 8 }}>
                  <Button
                    variant="ghost"
                    onClick={undoPoint}
                    disabled={!waypoints.length || loading}
                    className="btn ghost"
                    style={{ flex: 1 }}
                  >
                    <Undo2 className="w-4 h-4 mr-1" /> Deshacer
                  </Button>

                  <Button
                    variant="ghost"
                    onClick={clearAll}
                    disabled={!waypoints.length || loading}
                    className="btn ghost"
                    style={{ flex: 1 }}
                  >
                    <Trash2 className="w-4 h-4 mr-1" /> Limpiar
                  </Button>
                </div>
              </div>

              {waypoints.length < 2 && (
                <div style={{ fontSize: '0.75rem', color: '#64748b', textAlign: 'center', marginTop: 4 }}>
                  {waypoints.length === 0 ? "1. Selecciona punto de Origen (A)" : "2. Selecciona punto de Destino (B)"}
                </div>
              )}
            </div>
          </div>
        </aside>

        {/* Map */}
        <div className="map-wrapper" style={{ height: '75vh', minHeight: '600px', display: 'flex', flexDirection: 'column' }}>
          <div style={{ flex: '1 1 auto', position: 'relative', height: '100%' }}>
            <MapContainer center={center} zoom={13} className="map-root" zoomControl preferCanvas>
              <TileLayer url={`${VITE_API_URL}/tiles/carto/{z}/{x}/{y}.png`} maxZoom={18} />
              <ClickToAdd onAdd={addPoint} />
              {waypoints.map(([lng, lat], i) => {
                const type = i === 0 ? "start" : i === waypoints.length - 1 ? "end" : "normal";
                return <Marker key={`wp-${i}`} position={[lat, lng]} icon={makeColoredIcon(COLORS[0], i + 1, type)} />;
              })}
              {routeLine?.coordinates?.length > 1 && (
                <Polyline positions={routeLine.coordinates.map(([lng, lat]) => [lat, lng])} pathOptions={{ color: COLORS[0], weight: 5, opacity: 0.8 }} />
              )}
            </MapContainer>
          </div>
        </div>
      </div>

      {/* Results Section */}
      <section className="stats-section">
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
          {error && <div style={{ padding: '0 20px', color: '#ef4444', fontWeight: 500, margin: '0 auto 10px' }}>Error: {error}</div>}

          {analysis?.error && (
            <div style={{ padding: '0 20px', marginBottom: 20 }}>
              <div style={{ background: '#fef2f2', border: '1px solid #fee2e2', borderRadius: 8, padding: 16, display: 'flex', gap: 12 }}>
                <AlertTriangle className="w-5 h-5 text-red-500" style={{ flexShrink: 0 }} />
                <div>
                  <div style={{ fontWeight: 600, color: '#991b1b' }}>Error en el Modelo</div>
                  <div style={{ color: '#b91c1c', fontSize: 13 }}>{analysis.details || analysis.error}</div>
                  <div style={{ color: '#b91c1c', fontSize: 12, marginTop: 4, fontStyle: 'italic' }}>Revisa las librerías del servidor.</div>
                </div>
              </div>
            </div>
          )}

          <div className="stats-header" style={{ padding: '0 20px' }}>
            <h2 style={{ margin: 0 }}>Resultados de Simulación</h2>
            <div style={{ fontSize: '0.8rem', background: '#e2e8f0', padding: '4px 10px', borderRadius: 20, fontWeight: 500 }}>
              Ida y Vuelta (Ciclo Completo)
            </div>
          </div>

          <div className="stats-layout" style={{ padding: '0 20px' }}>
            {/* 1. INFORMACIÓN DEL VIAJE */}
            <div className="stats-card stats-card-full">
              <h3 style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <Info className="w-4 h-4 text-gray-500" /> Información del Viaje
              </h3>
              <div className="stats-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 20, marginTop: 12 }}>
                <div>
                  <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Origen</div>
                  <div style={{ fontWeight: 600 }}>{analysis?.municipio_origen || "N/D"}</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Destino</div>
                  <div style={{ fontWeight: 600 }}>{analysis?.municipio_destino || "N/D"}</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Estrato Detectado</div>
                  <div style={{ fontWeight: 600 }}>{analysis?.estrato || "N/D"}</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Motivo</div>
                  <div style={{ fontWeight: 600 }}>{analysis?.motivo_viaje || "N/D"}</div>
                </div>
              </div>
              <div style={{ marginTop: 16, paddingTop: 16, borderTop: '1px solid #f1f5f9', display: 'flex', gap: 32, flexWrap: 'wrap' }}>
                <div>
                  <span style={{ color: '#64748b', marginRight: 8, fontSize: '0.9rem' }}>Distancia Total:</span>
                  <span style={{ fontWeight: 700, fontSize: '1rem' }}>{fmtVal(analysis?.distancia_km, 2, ' km')}</span>
                </div>
                <div style={{ display: 'flex', gap: 16 }}>
                  <span style={{ fontSize: '0.9rem', color: '#475569' }}>
                    Ida: <strong>{fmtVal(analysis?.distancia_ida_km, 2, ' km')}</strong>
                  </span>
                  <span style={{ fontSize: '0.9rem', color: '#475569' }}>
                    Vuelta: <strong>{fmtVal(analysis?.distancia_vuelta_km, 2, ' km')}</strong>
                  </span>
                </div>
              </div>
            </div>

            {/* 2. COMPARACIÓN DETALLADA */}
            <div className="stats-row stats-row-two">
              {/* ELÉCTRICA */}
              <div className="stats-card">
                <h3 style={{ color: COLORS[1], borderBottom: `2px solid ${COLORS[1]}`, paddingBottom: 8, marginBottom: 16 }}>
                  Motocicleta Eléctrica
                </h3>

                <div style={{ marginBottom: 16 }}>
                  <div style={{ fontWeight: 600, fontSize: '0.9rem', marginBottom: 8 }}>Consumo Energía</div>
                  <StatRow label="Ida" value={fmtVal(analysis?.consumo_electrico_kwh_ida, 4, ' kWh')} />
                  <StatRow label="Vuelta" value={fmtVal(analysis?.consumo_electrico_kwh_vuelta, 4, ' kWh')} />
                  <StatRow label="Total" value={fmtVal(analysis?.consumo_electrico_kwh, 4, ' kWh')} highlight />
                </div>

                <div>
                  <div style={{ fontWeight: 600, fontSize: '0.9rem', marginBottom: 8 }}>Costos Estimados</div>
                  <StatRow label="Precio Min" value={money(analysis?.costo_electrico_min)} />
                  <StatRow label="Precio Max" value={money(analysis?.costo_electrico_max)} />
                  <StatRow label="Promedio" value={analysis ? money((analysis.costo_electrico_min + analysis.costo_electrico_max) / 2) : "N/D"} highlight color={COLORS[1]} />
                </div>
              </div>

              {/* COMBUSTIÓN */}
              <div className="stats-card">
                <h3 style={{ color: COLORS[4], borderBottom: `2px solid ${COLORS[4]}`, paddingBottom: 8, marginBottom: 16 }}>
                  Motocicleta a Combustión
                </h3>

                <div style={{ marginBottom: 16 }}>
                  <div style={{ fontWeight: 600, fontSize: '0.9rem', marginBottom: 8 }}>Consumo Gasolina</div>
                  <StatRow label="Ida" value={fmtVal(analysis?.consumo_galones_ida, 5, ' gal')} />
                  <StatRow label="Vuelta" value={fmtVal(analysis?.consumo_galones_vuelta, 5, ' gal')} />
                  <StatRow label="Total" value={fmtVal(analysis?.consumo_galones, 5, ' gal')} highlight />
                </div>

                <div>
                  <div style={{ fontWeight: 600, fontSize: '0.9rem', marginBottom: 8 }}>Costos Estimados</div>
                  <StatRow label="Precio Min" value={money(analysis?.costo_combustion_min)} />
                  <StatRow label="Precio Max" value={money(analysis?.costo_combustion_max)} />
                  <StatRow label="Promedio" value={analysis ? money((analysis.costo_combustion_min + analysis.costo_combustion_max) / 2) : "N/D"} highlight color={COLORS[4]} />
                </div>
              </div>
            </div>

            {/* 3. AHORRO */}
            <div className="stats-card" style={{ background: '#ecfdf5', borderColor: '#a7f3d0' }}>
              <h3 style={{ color: '#047857', textAlign: 'center', marginBottom: 16 }}>Comparativa de Ahorro</h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 24, textAlign: 'center' }}>
                <div>
                  <div style={{ fontSize: '0.9rem', color: '#065f46' }}>Ahorro Promedio por Viaje</div>
                  <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#059669', margin: '4px 0' }}>
                    {money(analysis?.ahorro_promedio)}
                  </div>
                  <div style={{ fontSize: '0.8rem', color: '#047857' }}>
                    Min: {money(analysis?.ahorro_min)} - Max: {money(analysis?.ahorro_max)}
                  </div>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                  <div style={{ fontSize: '0.9rem', color: '#065f46', marginBottom: 4 }}>Porcentaje de Ahorro</div>
                  <div style={{ fontSize: '1.4rem', fontWeight: 700, color: '#059669' }}>
                    {fmtVal(analysis?.porcentaje_ahorro_min, 1)}% - {fmtVal(analysis?.porcentaje_ahorro_max, 1)}%
                  </div>
                </div>
              </div>
            </div>

            {/* 4. CANASTA FAMILIAR */}
            <div className="stats-card stats-card-full">
              <h3 style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <CheckCircle2 className="w-5 h-5 text-blue-600" /> Analisis: Canasta Familiar
              </h3>

              {analysis?.gasto_total_canasta ? (
                <div style={{ marginTop: 12 }}>
                  <div style={{ marginBottom: 16, padding: '10px', background: '#f8fafc', borderRadius: 8, fontSize: '0.9rem' }}>
                    Hogar estrato <strong>{analysis.estrato}</strong> en <strong>{analysis.ciudad}</strong>.<br />
                    Presupuesto mensual total: <strong>{money(analysis.gasto_total_canasta)}</strong>
                  </div>

                  <div className="stats-grid" style={{ gridTemplateColumns: '1fr 1fr', gap: 32 }}>
                    <div>
                      <div style={{ fontSize: '0.9rem', fontWeight: 600, marginBottom: 8, color: COLORS[4] }}>Gasto Combustible (Mensual)</div>
                      <StatRow label="Mínimo" value={money(analysis.gasto_mensual_combustion_min)} />
                      <StatRow label="Máximo" value={money(analysis.gasto_mensual_combustion_max)} />
                    </div>

                    <div>
                      <div style={{ fontSize: '0.9rem', fontWeight: 600, marginBottom: 8, color: '#dc2626' }}>Impacto en Canasta (%)</div>
                      <StatRow label="Mínimo" value={fmtVal(analysis.porcentaje_canasta_min, 2, '%')} />
                      <StatRow label="Máximo" value={fmtVal(analysis.porcentaje_canasta_max, 2, '%')} />
                      <StatRow label="Promedio" value={fmtVal((analysis.porcentaje_canasta_min + analysis.porcentaje_canasta_max) / 2, 2, '%')} highlight />
                    </div>
                  </div>
                </div>
              ) : (
                <div style={{ display: 'flex', gap: 10, alignItems: 'center', color: '#64748b', fontSize: '0.9rem', padding: '10px 0' }}>
                  {analysis ? (
                    <><AlertTriangle className="w-4 h-4 text-amber-500" /> <span>No hay datos de canasta disponibles para esta zona.</span></>
                  ) : <span>Calcula una ruta para ver el análisis.</span>}
                </div>
              )}
            </div>

          </div>
        </div>
      </section>
    </section>
  );
}