"use client";
import React, { useEffect, useState } from "react";
import FileLoader from "./FileLoader.jsx";
import {
  buildVehiclesJSON,
  buildRoutesFeatureCollection,
} from "../../utils/exporters.js";

export default function ControlsPanel({
  options,
  setOptions,
  vehicles,
  activeVehicle,
  setActiveVehicle,
  addVehicle,
  removeVehicle,
  undoWaypoint,
  clearAll,
  totalSummary,
  computeRoutesManual,
  setVehicles,
  onGeoLoad = () => { },
  onClearGeo = () => { },
  drawOnly = false,
  routes = {},
  selectedAlt = {},
  routeError = null,
  isLoading = false,

  // (vienen desde MapPage)
  stationsMode = "default", // "default" | "custom"
  setStationsMode = () => { },
  stationsPayload = null, // { coords: [[lng,lat]], nombre: [...] } o null
  setStationsPayload = () => { },
  stationsLoading = false,
  resetStationsToDefault = () => { },
  customStationTipo = "Estándar",
  setCustomStationTipo = () => { },
}) {
  // ============================
  // Export
  // ============================
  const exportJSON = () => {
    const payload = buildVehiclesJSON(vehicles, {
      ...options,
      alternatives: false,
      steps: false,
    });

    const blob = new Blob([JSON.stringify(payload, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "vehicles_request.json";
    a.click();
    URL.revokeObjectURL(url);
  };

  const exportRoutesGeoJSON = () => {
    const fc = buildRoutesFeatureCollection(routes, selectedAlt);
    const blob = new Blob([JSON.stringify(fc, null, 2)], {
      type: "application/geo+json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "routes.geojson";
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleCompute = () => {
    setOptions((o) => ({ ...o, alternatives: false, steps: false }));
    computeRoutesManual();
  };

  // ============================
  // Input UX (sin “0” pegajoso)
  // ============================
  const [priceInput, setPriceInput] = useState(
    options?.price_per_kwh ? String(options.price_per_kwh) : ""
  );
  const [powerInput, setPowerInput] = useState(
    options?.charger_power_kw != null ? String(options.charger_power_kw) : "3.5"
  );

  // Sync cuando cambian options desde afuera
  useEffect(() => {
    setPriceInput(options?.price_per_kwh ? String(options.price_per_kwh) : "");
  }, [options?.price_per_kwh]);

  useEffect(() => {
    setPowerInput(
      options?.charger_power_kw != null ? String(options.charger_power_kw) : "3.5"
    );
  }, [options?.charger_power_kw]);

  const clampNumber = (val, { min = -Infinity, max = Infinity } = {}) => {
    const n = Number(val);
    if (!Number.isFinite(n)) return null;
    return Math.min(max, Math.max(min, n));
  };

  const onBlurPrice = () => {
    const v = clampNumber(priceInput, { min: 0, max: 999999999 });
    setOptions((o) => ({ ...o, price_per_kwh: v ?? 0 }));
    setPriceInput(v ? String(v) : ""); // si es 0 → deja vacío visualmente
  };

  const onBlurPower = () => {
    const v = clampNumber(powerInput, { min: 0, max: 1000 });
    setOptions((o) => ({ ...o, charger_power_kw: v ?? 0 }));
    setPowerInput(v != null ? String(v) : "3.5");
  };

  // ============================
  // estaciones default/custom
  // ============================
  const onUseDefaultStations = async () => {
    setStationsMode("default");
    await resetStationsToDefault();
  };

  const onUseCustomStations = () => {
    setStationsMode("custom");

    // Inicializa para editar si no existe
    if (!stationsPayload?.coords) {
      setStationsPayload({ coords: [], nombre: [] });
      return;
    }

    // Normaliza nombres si faltan
    if (!stationsPayload?.nombre) {
      setStationsPayload({
        coords: stationsPayload.coords || [],
        nombre: (stationsPayload.coords || []).map((_, i) => `Estación ${i + 1}`),
      });
    }
  };

  // salir de edición sin perder estaciones custom
  const onFinishCustomStations = () => {
    // OJO: no resetea payload, solo cambia el modo para volver a waypoints
    setStationsMode("default");
  };

  // limpiar estaciones (reemplaza "Restaurar")
  const onClearStations = () => {
    // Borra todas las estaciones visibles
    setStationsPayload({ coords: [], nombre: [] });
    // Vuelve a modo ruta para poder poner waypoints normal
    setStationsMode("default");
  };

  const inputStyle = {
    width: "100%",
    padding: "10px 12px",
    borderRadius: 10,
    border: "1px solid rgba(0,0,0,0.10)",
    background: "rgba(255,255,255,0.85)",
    outline: "none",
    fontSize: 13,
  };

  return (
    <div className="card">
      <h2 className="panel-title">Parámetros</h2>

      <FileLoader onGeojson={onGeoLoad} onClearGeo={onClearGeo} />

      <div className="divider" />

      {/* 🔌 Recarga y costo */}
      <div className="kv">
        <span className="k">Potencia de recarga (kW)</span>
        <input
          className="input"
          style={inputStyle}
          type="number"
          step="0.1"
          min="0"
          placeholder="Ej: 3.5"
          value={powerInput}
          onChange={(e) => setPowerInput(e.target.value)}
          onBlur={onBlurPower}
          onFocus={(e) => e.target.select()}
          disabled={drawOnly}
        />
      </div>

      <div className="kv">
        <span className="k">Precio por kWh</span>
        <input
          className="input"
          style={inputStyle}
          type="number"
          step="0.01"
          min="0"
          placeholder="Ej: 900"
          value={priceInput}
          onChange={(e) => setPriceInput(e.target.value)}
          onBlur={onBlurPrice}
          onFocus={(e) => e.target.select()}
          disabled={drawOnly}
        />
      </div>

      <div className="small" style={{ marginTop: 6 }}>
        * Tiempo de carga (lineal):{" "}
        <strong>tiempo = energía recargada / kW</strong>.<br />
        * Costo: <strong>energía recargada × precio/kWh</strong>.
      </div>

      <div className="divider" />

      {/* ⚡ Estaciones */}
      <div style={{ marginBottom: 8 }}>
        <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 6 }}>
          Estaciones de carga
        </div>

        <div className="row" style={{ flexWrap: "wrap", gap: 8 }}>
          <button
            className={`btn small ${stationsMode === "default" ? "" : "ghost"}`}
            onClick={onUseDefaultStations}
            disabled={drawOnly || stationsLoading}
            type="button"
          >
            {stationsLoading && stationsMode === "default"
              ? "Cargando..."
              : "Usar estaciones estandar"}
          </button>

          <button
            className={`btn small ${stationsMode === "custom" ? "" : "ghost"}`}
            onClick={onUseCustomStations}
            disabled={drawOnly}
            type="button"
            title="En modo custom: click en mapa agrega estación. Click en estación la borra."
          >
            Ingresar estaciones
          </button>

          {/* NUEVO */}
          {stationsMode === "custom" && (
            <button
              className="btn small"
              onClick={onFinishCustomStations}
              disabled={drawOnly}
              type="button"
              title="Vuelves a poner waypoints sin perder las estaciones personalizadas"
            >
              Listo (volver a ruta)
            </button>
          )}

          {/*  antes decía "Restaurar" */}
          <button
            className="btn small ghost"
            onClick={onClearStations}
            disabled={drawOnly || stationsLoading}
            type="button"
            title="Borra todas las estaciones del mapa"
          >
            Limpiar estaciones
          </button>
        </div>

        <div className="small" style={{ marginTop: 6 }}>
          Modo actual:{" "}
          <strong>
            {stationsMode === "default"
              ? "Ruta (waypoints)"
              : "Edición (custom)"}
          </strong>
          {stationsMode === "custom" ? (
            <>
              {" "}
              · Click en mapa = <strong>agregar estación</strong> · Click en
              estación = <strong>borrar</strong>
              <br />
              <span style={{ opacity: 0.85 }}>
                Cuando termines, usa <strong>“Listo (volver a ruta)”</strong>{" "}
                para poner waypoints.
              </span>
            </>
          ) : null}
        </div>

        {/* Selector de tipo para estaciones custom */}
        {stationsMode === "custom" && (
          <div className="kv" style={{ marginTop: 10 }}>
            <span className="k">Tipo de estación a insertar</span>
            <select
              className="select"
              value={customStationTipo}
              onChange={(e) => setCustomStationTipo(e.target.value)}
              style={{ marginTop: 4 }}
            >
              <option value="Estándar">● Estándar (negra)</option>
              <option value="Alta Capacidad">● Alta Capacidad (amarilla)</option>
              <option value="Intercambio">● Intercambio (azul)</option>
            </select>
          </div>
        )}
      </div>

      <div className="divider" />

      {/* Gestión motos */}
      <div className="row">
        <button className="btn" onClick={addVehicle} disabled={drawOnly}>
          + Agregar moto
        </button>
        <button
          className="btn ghost"
          onClick={removeVehicle}
          disabled={drawOnly || vehicles.length === 1}
        >
          − Quitar activa
        </button>
      </div>

      <div className="kv">
        <span className="k">Moto activa</span>
        <select
          className="select"
          value={activeVehicle}
          onChange={(e) => setActiveVehicle(Number(e.target.value))}
          disabled={drawOnly}
        >
          {vehicles.map((v, idx) => (
            <option key={v.id} value={idx}>
              {v.id}
            </option>
          ))}
        </select>
      </div>

      <div className="row">
        <button className="btn ghost" onClick={undoWaypoint} disabled={drawOnly}>
          Deshacer punto
        </button>
        <button className="btn ghost" onClick={clearAll} disabled={drawOnly}>
          Limpiar rutas
        </button>
      </div>

      <div className="divider" />

      {/* Manual */}
      <button
        className="btn"
        onClick={handleCompute}
        disabled={drawOnly || isLoading}
      >
        {isLoading ? "Calculando..." : "Calcular rutas"}
      </button>

      {!!routeError && (
        <div style={{ marginTop: 10, fontSize: 13, color: "#b91c1c" }}>
          {routeError}
        </div>
      )}

      <div className="small" style={{ marginTop: 8 }}>
        Total: <strong>{totalSummary.distance_km} km</strong> ·{" "}
        <strong>{totalSummary.duration_min} min</strong>
      </div>

      <div className="divider" />

      <button className="btn ghost" onClick={exportJSON}>
        Exportar JSON (entrada)
      </button>

      <button
        className="btn ghost"
        onClick={exportRoutesGeoJSON}
        disabled={!Object.keys(routes || {}).length}
      >
        Exportar GeoJSON (rutas)
      </button>
    </div>
  );
}
