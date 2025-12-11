"use client"
import FileLoader from "./FileLoader.jsx"
import { buildVehiclesJSON, buildRoutesFeatureCollection } from "../../utils/exporters.js"

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
  // pueden no venir aún; damos valores por defecto seguros
  onGeoLoad = () => {},
  onClearGeo = () => {},
  drawOnly = false,
  routes = {},
  selectedAlt = {},
}) {
  // Exporta el JSON de entrada (siempre 1 ruta, sin pasos)
  const exportJSON = () => {
    const payload = buildVehiclesJSON(vehicles, {
      ...options,
      alternatives: false, // forzado
      steps: false, // forzado
    })
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = "vehicles_request.json"
    a.click()
    URL.revokeObjectURL(url)
  }

  // Exporta el GeoJSON de las rutas calculadas (si existen)
  const exportRoutesGeoJSON = () => {
    const fc = buildRoutesFeatureCollection(routes, selectedAlt)
    const blob = new Blob([JSON.stringify(fc, null, 2)], { type: "application/geo+json" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = "routes.geojson"
    a.click()
    URL.revokeObjectURL(url)
  }

  // Calcular siempre 1 ruta sin pasos
  const handleCompute = () => {
    setOptions((o) => ({ ...o, alternatives: false, steps: false }))
    computeRoutesManual()
  }

  return (
    <div className="card">
      <h2 className="panel-title">Parámetros</h2>

      {/* Cargar/limpiar capa importada (solo pintar) */}
      <FileLoader onGeojson={onGeoLoad} onClearGeo={onClearGeo} />
      <div className="small" style={{ color: drawOnly ? "#047857" : "#6b7280", marginTop: 4 }}>
        {/*Modo: <strong>{drawOnly ? "Dibujar archivo (sin ORS)" : "Manual + ORS"}</strong>*/}
      </div>

      
      {/*<div className="kv">
        <span className="k">Perfil</span>
        <span className="v">Moto eléctrica · conducción</span>
      </div>*/}

      <div className="divider" />

      {/* Gestión de motos (deshabilitado si hay archivo cargado) */}
      <div className="row">
        <button className="btn" onClick={addVehicle} disabled={drawOnly}>
          + Agregar moto
        </button>
        <button className="btn ghost" onClick={removeVehicle} disabled={drawOnly || vehicles.length === 1}>
          − Quitar activa
        </button>
      </div>

      <div className="row">
        <span className="k">Moto activa</span>
        <select
          className="select"
          value={activeVehicle}
          onChange={(e) => setActiveVehicle(Number.parseInt(e.target.value, 10))}
          disabled={drawOnly}
        >
          {vehicles.map((v, i) => (
            <option key={v.id} value={i}>
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

      <button className="btn primary" onClick={handleCompute} disabled={drawOnly}>
        Calcular rutas
      </button>

      <div className="total" style={{ marginTop: 8 }}>
        <span>Total:</span>
        <strong>
          {totalSummary.distance_km} km · {totalSummary.duration_min} min
        </strong>
      </div>

      <div className="divider" />

      {/* Exportaciones */}
      <div className="row" style={{ justifyContent: "space-between", gap: 8 }}>
        <button className="btn" onClick={exportJSON} disabled={drawOnly}>
          Exportar JSON (entrada)
        </button>

        <button className="btn ghost" onClick={exportRoutesGeoJSON} disabled={Object.keys(routes || {}).length === 0}>
          Exportar GeoJSON (rutas)
        </button>
      </div>
    </div>
  )
}