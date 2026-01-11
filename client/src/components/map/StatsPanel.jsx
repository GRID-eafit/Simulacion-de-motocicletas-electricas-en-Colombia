// client/src/components/map/StatsPanel.jsx
import React, { useMemo } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
  BarChart,
  Bar,
} from "recharts";

import { COLORS } from "../../utils/colors";

const getColor = (index) => COLORS[index % COLORS.length];

export default function StatsPanel({
  routes,
  totalSummary,
  vehicles,
  activeVehicle,
}) {
  // === 1. Ruta activa (misma lógica que el mapa) ===
  const activeId = vehicles[activeVehicle]?.id;
  const activeRoute =
    routes && activeId && typeof routes === "object" ? routes[activeId] : null;

  // === 2. Resumen numérico (usa summary de la ruta + totalSummary) ===
  const { distanceKm, durationMin } = useMemo(() => {
    const distanceMeters = activeRoute?.summary?.distance ?? null;
    const durationSeconds = activeRoute?.summary?.duration ?? null;

    const tsDist =
      typeof totalSummary?.distance_km === "string"
        ? parseFloat(totalSummary.distance_km)
        : totalSummary?.distance_km;
    const tsDur =
      typeof totalSummary?.duration_min === "string"
        ? parseFloat(totalSummary.duration_min)
        : totalSummary?.duration_min;

    const dKm =
      Number.isFinite(tsDist) && tsDist > 0
        ? tsDist
        : distanceMeters != null
        ? distanceMeters / 1000
        : null;

    const dMin =
      Number.isFinite(tsDur) && tsDur > 0
        ? tsDur
        : durationSeconds != null
        ? durationSeconds / 60
        : null;

    return { distanceKm: dKm, durationMin: dMin };
  }, [activeRoute, totalSummary]);

  // === 3. Datos para gráficas (potencia & SoC) ===
  const powerSocData = useMemo(() => {
    const pot = activeRoute?.properties?.potencia;
    const soc = activeRoute?.properties?.soc;
    if (!Array.isArray(pot) || !Array.isArray(soc)) return [];

    return pot.map((p, idx) => ({
      idx,
      power: p,
      soc: soc[idx] ?? null,
    }));
  }, [activeRoute]);

  const avgPower = useMemo(() => {
    if (!powerSocData.length) return null;
    const sum = powerSocData.reduce((acc, d) => acc + d.power, 0);
    return sum / powerSocData.length;
  }, [powerSocData]);

  // === 4. "Energía acumulada" como índice (suma de potencia) ===
  const cumulativeEnergyData = useMemo(() => {
    if (!powerSocData.length) return [];
    let cum = 0;
    return powerSocData.map((d) => {
      cum += d.power;
      return { idx: d.idx, energyIndex: cum };
    });
  }, [powerSocData]);

  // Emisiones (puedes ajustar factores si quieres)
  const emisiones_co2_kg = useMemo(() => {
    const factor_emision_gco2_km = 70;
    if (!Number.isFinite(distanceKm)) return null;
    return (distanceKm * factor_emision_gco2_km) / 1000;
  }, [distanceKm]);

  const emisiones_co2_equivalente_electrico_kg = useMemo(() => {
    const factor_emision_electrico_gco2_km = 35;
    if (!Number.isFinite(distanceKm)) return null;
    return (distanceKm * factor_emision_electrico_gco2_km) / 1000;
  }, [distanceKm]);

  const emisiones_co2_equivalente_kg = useMemo(() => {
    const factor_emision_co2_kg_galon = 8.887;
    if (!Number.isFinite(distanceKm) || !cumulativeEnergyData.length)
      return null;
    const c = cumulativeEnergyData[cumulativeEnergyData.length - 1];
    const poder_calorifico_gasolina_kwh_galon = 33.7;
    const consumo_galones = c.energyIndex / poder_calorifico_gasolina_kwh_galon;
    return consumo_galones * factor_emision_co2_kg_galon;
  }, [distanceKm, cumulativeEnergyData]);

  // === 5. Comparación entre vehículos (multi-moto) ===
  const comparisonData = useMemo(() => {
    if (!routes || typeof routes !== "object") return [];
    return Object.entries(routes)
      .map(([id, route]) => ({
        vehicle: id,
        distanceKm: route.summary?.distance ? route.summary.distance / 1000 : null,
        durationMin: route.summary?.duration ? route.summary.duration / 60 : null,
      }))
      .filter((d) => Number.isFinite(d.distanceKm) && Number.isFinite(d.durationMin));
  }, [routes]);

  // === 6. Exportar CSV (datos de la ruta activa) ===
  const handleExportCsv = () => {
    if (!activeRoute || !powerSocData.length) return;

    const rows = [];
    rows.push(`# Vehículo: ${activeId || "N/D"}`);
    if (Number.isFinite(distanceKm)) rows.push(`# Distancia (km): ${distanceKm.toFixed(3)}`);
    if (Number.isFinite(durationMin)) rows.push(`# Duración (min): ${durationMin.toFixed(2)}`);
    rows.push("");
    rows.push("segmento,potencia,soc");

    powerSocData.forEach((d) => {
      rows.push(`${d.idx},${d.power},${d.soc ?? ""}`);
    });

    const blob = new Blob([rows.join("\n")], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.href = url;
    a.download = `ruta_${activeId || "vehiculo"}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleExportPdf = () => {
    window.print();
  };

  // === 7. Puntos de carga (card nueva) ===
  const chargePoints = Array.isArray(activeRoute?.charge_points)
    ? activeRoute.charge_points
    : [];

  const chargeSummary = useMemo(() => {
    if (!chargePoints.length)
      return { totalEnergyKwh: 0, totalTimeMin: 0, totalCost: 0, count: 0 };

    let totalEnergy = 0;
    let totalTimeMin = 0;
    let totalCost = 0;

    chargePoints.forEach((cp) => {
      if (typeof cp.energy_charged === "number") totalEnergy += cp.energy_charged;
      if (typeof cp.charge_time_min === "number") totalTimeMin += cp.charge_time_min;
      if (typeof cp.charge_cost === "number") totalCost += cp.charge_cost;
    });

    return {
      totalEnergyKwh: totalEnergy,
      totalTimeMin,
      totalCost,
      count: chargePoints.length,
    };
  }, [chargePoints]);

  const chargeChartData = useMemo(() => {
    if (!chargePoints.length) return [];
    return chargePoints.map((cp, idx) => ({
      idx: idx + 1,
      station_name: cp.station_name || `Punto ${idx + 1}`,
      energy_kwh: typeof cp.energy_charged === "number" ? cp.energy_charged : null,
      time_min: typeof cp.charge_time_min === "number" ? cp.charge_time_min : null,
      cost: typeof cp.charge_cost === "number" ? cp.charge_cost : null,
      price_per_kwh: typeof cp.price_per_kwh === "number" ? cp.price_per_kwh : null,
      charger_power_kw:
        typeof cp.charger_power_kw === "number" ? cp.charger_power_kw : null,
    }));
  }, [chargePoints]);

  const hasChargeCost = useMemo(() => {
    return chargeChartData.some((d) => Number.isFinite(d.cost) && d.cost > 0);
  }, [chargeChartData]);

  return (
    <>
      {/* Header con acciones */}
      <div className="stats-header">
        <h2>Estadísticas de la simulación</h2>
        <div className="stats-actions">
          <button
            className="btn ghost"
            type="button"
            onClick={handleExportCsv}
            disabled={!activeRoute || !powerSocData.length}
          >
            Exportar CSV
          </button>
          <button
            className="btn"
            type="button"
            onClick={handleExportPdf}
            disabled={!activeRoute}
          >
            Exportar PDF
          </button>
        </div>
      </div>

      {/* LAYOUT VERTICAL */}
      <div className="stats-layout">
        {/* === Fila 1: Resumen general (full width) === */}
        <section className="stats-row">
          <div className="stats-card stats-card-full">
            <h3>Resumen general</h3>
            {activeRoute ? (
              <ul>
                <li>
                  <strong>Vehículo:</strong> {activeId}
                </li>
                {Number.isFinite(distanceKm) && (
                  <li>
                    <strong>Distancia:</strong> {distanceKm.toFixed(2)} km
                  </li>
                )}
                {Number.isFinite(durationMin) && (
                  <li>
                    <strong>Duración:</strong> {durationMin.toFixed(1)} min
                  </li>
                )}
                {Number.isFinite(avgPower) && (
                  <li>
                    <strong>Potencia media:</strong> {avgPower.toFixed(0)} W
                  </li>
                )}
                <li>
                  <strong>Puntos de ruta:</strong>{" "}
                  {powerSocData.length || activeRoute.geometry?.coordinates?.length || "N/D"}
                </li>
                {Number.isFinite(emisiones_co2_kg) && (
                  <li>
                    <strong>Emisiones de CO₂:</strong> {emisiones_co2_kg.toFixed(1)} kg
                  </li>
                )}
                {Number.isFinite(emisiones_co2_equivalente_kg) && (
                  <li>
                    <strong>Emisiones (desde galones):</strong>{" "}
                    {emisiones_co2_equivalente_kg.toFixed(1)} kg
                  </li>
                )}
                {Number.isFinite(emisiones_co2_equivalente_electrico_kg) && (
                  <li>
                    <strong>Emisiones equivalentes (motocicleta eléctrica):</strong>{" "}
                    {emisiones_co2_equivalente_electrico_kg.toFixed(1)} kg
                  </li>
                )}
              </ul>
            ) : (
              <p>Aún no hay rutas calculadas.</p>
            )}
          </div>
        </section>

        {/* === Fila 2: Potencia + SoC === */}
        <section className="stats-row stats-row-two">
          <div className="stats-card">
            <h3>Potencia por segmento</h3>
            {powerSocData.length ? (
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={powerSocData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                  <XAxis
                    dataKey="idx"
                    tick={{ fontSize: 10 }}
                    label={{ value: "Segmento", position: "insideBottomRight", offset: -4 }}
                  />
                  <YAxis
                    yAxisId="left"
                    tick={{ fontSize: 10 }}
                    label={{ value: "Potencia (W)", angle: -90, position: "insideLeft" }}
                  />
                  <Tooltip />
                  <Legend />
                  <Line
                    yAxisId="left"
                    type="monotone"
                    dataKey="power"
                    name="Potencia (W)"
                    dot={false}
                    strokeWidth={2}
                    stroke={getColor(0)}
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <p>No hay datos de potencia todavía.</p>
            )}
          </div>

          <div className="stats-card">
            <h3>Estado de carga (SoC)</h3>
            {powerSocData.length ? (
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={powerSocData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                  <XAxis
                    dataKey="idx"
                    tick={{ fontSize: 10 }}
                    label={{ value: "Segmento", position: "insideBottomRight", offset: -4 }}
                  />
                  <YAxis
                    tick={{ fontSize: 10 }}
                    label={{ value: "SoC", angle: -90, position: "insideLeft" }}
                  />
                  <Tooltip />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="soc"
                    name="SoC"
                    dot={false}
                    strokeWidth={2}
                    stroke={getColor(1)}
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <p>No hay datos de SoC todavía.</p>
            )}
          </div>
        </section>

        {/* === Fila 3: Energía acumulada + Comparación vehículos === */}
        <section className="stats-row stats-row-two">
          <div className="stats-card">
            <h3>Índice de energía acumulada</h3>
            {cumulativeEnergyData.length ? (
              <ResponsiveContainer width="100%" height={220}>
                <LineChart
                  data={cumulativeEnergyData}
                  margin={{ top: 10, right: 20, left: 0, bottom: 0 }}
                >
                  <XAxis
                    dataKey="idx"
                    tick={{ fontSize: 10 }}
                    label={{ value: "Segmento", position: "insideBottomRight", offset: -4 }}
                  />
                  <YAxis
                    tick={{ fontSize: 10 }}
                    label={{ value: "Índice (∑ potencia)", angle: -90, position: "insideLeft" }}
                  />
                  <Tooltip />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="energyIndex"
                    name="Índice de energía"
                    dot={false}
                    strokeWidth={2}
                    stroke={getColor(2)}
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <p>No hay datos suficientes para el índice de energía.</p>
            )}
          </div>

          <div className="stats-card">
            <h3>Comparación entre vehículos</h3>
            {comparisonData.length > 1 ? (
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={comparisonData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                  <XAxis dataKey="vehicle" tick={{ fontSize: 10 }} />
                  <YAxis
                    yAxisId="left"
                    tick={{ fontSize: 10 }}
                    label={{ value: "Distancia (km)", angle: -90, position: "insideLeft" }}
                  />
                  <YAxis
                    yAxisId="right"
                    orientation="right"
                    tick={{ fontSize: 10 }}
                    label={{ value: "Duración (min)", angle: 90, position: "insideRight" }}
                  />
                  <Tooltip />
                  <Legend />
                  <Bar
                    yAxisId="left"
                    dataKey="distanceKm"
                    name="Distancia (km)"
                    fill={getColor(3)}
                  />
                  <Bar
                    yAxisId="right"
                    dataKey="durationMin"
                    name="Duración (min)"
                    fill={getColor(4)}
                  />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p>Añade más motos y calcula sus rutas para ver la comparación de distancia y tiempo.</p>
            )}
          </div>
        </section>

        {/* === Fila 4: Puntos de carga (full width) === */}
        <section className="stats-row">
          <div className="stats-card stats-card-full">
            <h3>Puntos de carga</h3>

            {!chargePoints.length ? (
              <p>Esta ruta no realizó recargas de batería.</p>
            ) : (
              <>
                <ul style={{ marginBottom: "0.75rem" }}>
                  <li>
                    <strong>Número de recargas:</strong> {chargeSummary.count}
                  </li>
                  <li>
                    <strong>Energía total recargada:</strong>{" "}
                    {chargeSummary.totalEnergyKwh.toFixed(2)} kWh
                  </li>
                  <li>
                    <strong>Tiempo total en carga:</strong>{" "}
                    {chargeSummary.totalTimeMin.toFixed(1)} min
                  </li>
                  <li>
                    <strong>Costo total de recargas:</strong>{" "}
                    {chargeSummary.totalCost.toFixed(2)}
                  </li>
                </ul>

                {/* Tabla rápida por estación */}
                <div style={{ overflowX: "auto", marginBottom: "0.75rem" }}>
                  <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
                    <thead>
                      <tr>
                        <th style={{ textAlign: "left", padding: "8px 6px", borderBottom: "1px solid rgba(0,0,0,0.08)" }}>
                          #
                        </th>
                        <th style={{ textAlign: "left", padding: "8px 6px", borderBottom: "1px solid rgba(0,0,0,0.08)" }}>
                          Estación
                        </th>
                        <th style={{ textAlign: "right", padding: "8px 6px", borderBottom: "1px solid rgba(0,0,0,0.08)" }}>
                          Energía (kWh)
                        </th>
                        <th style={{ textAlign: "right", padding: "8px 6px", borderBottom: "1px solid rgba(0,0,0,0.08)" }}>
                          Tiempo (min)
                        </th>
                        <th style={{ textAlign: "right", padding: "8px 6px", borderBottom: "1px solid rgba(0,0,0,0.08)" }}>
                          Costo
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {chargeChartData.map((d) => (
                        <tr key={`cp-row-${d.idx}`}>
                          <td style={{ padding: "8px 6px", borderBottom: "1px solid rgba(0,0,0,0.05)" }}>
                            {d.idx}
                          </td>
                          <td style={{ padding: "8px 6px", borderBottom: "1px solid rgba(0,0,0,0.05)" }}>
                            {d.station_name}
                          </td>
                          <td style={{ textAlign: "right", padding: "8px 6px", borderBottom: "1px solid rgba(0,0,0,0.05)" }}>
                            {Number.isFinite(d.energy_kwh) ? d.energy_kwh.toFixed(2) : "—"}
                          </td>
                          <td style={{ textAlign: "right", padding: "8px 6px", borderBottom: "1px solid rgba(0,0,0,0.05)" }}>
                            {Number.isFinite(d.time_min) ? d.time_min.toFixed(1) : "—"}
                          </td>
                          <td style={{ textAlign: "right", padding: "8px 6px", borderBottom: "1px solid rgba(0,0,0,0.05)" }}>
                            {Number.isFinite(d.cost) ? d.cost.toFixed(2) : "—"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Gráfica energía vs tiempo (la que ya tenías) */}
                <ResponsiveContainer width="100%" height={240}>
                  <BarChart data={chargeChartData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                    <XAxis
                      dataKey="idx"
                      tick={{ fontSize: 10 }}
                      label={{ value: "Punto de carga", position: "insideBottomRight", offset: -4 }}
                    />
                    <YAxis
                      yAxisId="left"
                      tick={{ fontSize: 10 }}
                      label={{ value: "Energía (kWh)", angle: -90, position: "insideLeft" }}
                    />
                    <YAxis
                      yAxisId="right"
                      orientation="right"
                      tick={{ fontSize: 10 }}
                      label={{ value: "Tiempo (min)", angle: 90, position: "insideRight" }}
                    />
                    <Tooltip />
                    <Legend />
                    <Bar
                      yAxisId="left"
                      dataKey="energy_kwh"
                      name="Energía recargada (kWh)"
                      fill={getColor(5)}
                    />
                    <Bar
                      yAxisId="right"
                      dataKey="time_min"
                      name="Tiempo de carga (min)"
                      fill={getColor(6)}
                    />
                  </BarChart>
                </ResponsiveContainer>

                {/* Gráfica de costo (solo si hay costo) */}
                {hasChargeCost && (
                  <div style={{ marginTop: 14 }}>
                    <h4 style={{ margin: "6px 0 10px", fontSize: 14 }}>
                      Costo por punto de carga
                    </h4>
                    <ResponsiveContainer width="100%" height={220}>
                      <BarChart
                        data={chargeChartData}
                        margin={{ top: 10, right: 20, left: 0, bottom: 0 }}
                      >
                        <XAxis dataKey="idx" tick={{ fontSize: 10 }} />
                        <YAxis
                          tick={{ fontSize: 10 }}
                          label={{ value: "Costo", angle: -90, position: "insideLeft" }}
                        />
                        <Tooltip />
                        <Legend />
                        <Bar dataKey="cost" name="Costo" fill={getColor(7)} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                )}
              </>
            )}
          </div>
        </section>
      </div>
    </>
  );
}