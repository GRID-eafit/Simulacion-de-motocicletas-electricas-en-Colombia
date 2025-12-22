"use client";
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
  onGeoLoad = () => {},
  onClearGeo = () => {},
  drawOnly = false,
  routes = {},
  selectedAlt = {},
  routeError = null,
  isLoading = false,
}) {
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
    // fuerza 1 ruta sin alternativas
    setOptions((o) => ({ ...o, alternatives: false, steps: false }));
    computeRoutesManual();
  };

  return (
    <div className="card">
      <h2 className="panel-title">Parámetros</h2>

      {/* Cargar/limpiar capa importada (solo pintar) */}
      <FileLoader onGeojson={onGeoLoad} onClearGeo={onClearGeo} />

      <div className="divider" />

      {/* Gestión de motos */}
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
          Limpiar todo
        </button>
      </div>

      <div className="divider" />

      {/* Calcular rutas (manual) */}
      <button className="btn" onClick={handleCompute} disabled={drawOnly || isLoading}>
        {isLoading ? "Calculando..." : "Calcular rutas"}
      </button>

      {/* Mensaje de error en pantalla */}
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

      {/* Exportaciones */}
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