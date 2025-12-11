import React, { useState } from "react";
import ControlsPanel from "../components/map/ControlsPanel.jsx";
import MapView from "../components/map/MapView.jsx";
import useVehicles from "../hooks/useVehicles.js";
import useAutoRoutes from "../hooks/useAutoRoutes.js";
import StatsPanel from "../components/map/StatsPanel.jsx";

export default function MapPage() {
  const {
    vehicles,
    setVehicles,
    activeVehicle,
    setActiveVehicle,
    lastPoint,
    setLastPoint,
    addVehicle,
    removeVehicle,
    handleAddWaypoint,
    undoWaypoint,
    clearAll,
    removeWaypointAt,
    clearWaypointsActive,
  } = useVehicles();

  // Capa importada (solo pintar) y modo dibujo
  const [importedGeoJSON, setImportedGeoJSON] = useState(null);
  const [drawOnly, setDrawOnly] = useState(false);

  // Ciudad activa del mapa: Medellín, Bogotá o AMVA
  const [city, setCity] = useState("med"); // "med" | "bog" | "amva"

  // NUEVO: estado de tráfico
  const [traffic, setTraffic] = useState(false); // booleano a enviar al back

  // cuando hay archivo cargado, no se calculan rutas
  const vehiclesForRouting = drawOnly ? [] : vehicles;

  // Hook de rutas, recibe también la ciudad y el tráfico
  const {
    options,
    setOptions,
    routes,
    selectedAlt,
    setSelectedAlt,
    totalSummary,
    computeRoutesManual,
  } = useAutoRoutes({
    vehicles: vehiclesForRouting,
    enabled: !drawOnly,
    city,
    traffic, 
  });

  const handleGeoLoad = (fc) => {
    setImportedGeoJSON(fc);
    setDrawOnly(true);
  };

  const handleClearGeo = () => {
    setImportedGeoJSON(null);
    setDrawOnly(false);
  };

  // Cuando cambias de ciudad, se limpian rutas, waypoints y geoJSON
  const handleChangeCity = (newCity) => {
    if (newCity === city) return;

    // Limpiar todo el estado relacionado con la ruta actual
    clearAll();
    setImportedGeoJSON(null);
    setDrawOnly(false);
    setLastPoint(null);

    // Cambiar ciudad
    setCity(newCity);
  };

  return (
    <section className="page">
      {/* bloque superior: sidebar + mapa */}
      <div className="page-main">
        <aside className="sidebar">

          {/* ============================
              Selector de ciudad
             ============================ */}
          <div style={{ marginBottom: "1rem" }}>
            <label style={{ fontSize: "0.9rem", fontWeight: 600 }}>
              Ciudad del mapa:
            </label>

            <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.25rem" }}>
              <button
                type="button"
                className={`btn small ${city === "med" ? "" : "ghost"}`}
                onClick={() => handleChangeCity("med")}
              >
                Medellín
              </button>

              <button
                type="button"
                className={`btn small ${city === "bog" ? "" : "ghost"}`}
                onClick={() => handleChangeCity("bog")}
              >
                Bogotá
              </button>

              <button
                type="button"
                className={`btn small ${city === "amva" ? "" : "ghost"}`}
                onClick={() => handleChangeCity("amva")}
              >
                AMVA
              </button>
            </div>
          </div>

          {/* ============================
              Selector de TRÁFICO (NUEVO)
             ============================ */}
          <div style={{ marginBottom: "1.2rem" }}>
            <label style={{ fontSize: "0.9rem", fontWeight: 600 }}>
              Condición de tráfico:
            </label>

            <button
              type="button"
              className={`btn small ${traffic ? "" : "ghost"}`}
              onClick={() => setTraffic(!traffic)}
            >
              {traffic ? "Con tráfico" : "Sin tráfico"}
            </button>
          </div>

          {/* ============================
              Panel de controles
             ============================ */}
          <ControlsPanel
            options={options}
            setOptions={setOptions}
            vehicles={vehicles}
            activeVehicle={activeVehicle}
            setActiveVehicle={setActiveVehicle}
            addVehicle={addVehicle}
            removeVehicle={removeVehicle}
            undoWaypoint={undoWaypoint}
            clearAll={clearAll}
            totalSummary={totalSummary}
            computeRoutesManual={computeRoutesManual}
            setVehicles={setVehicles}
            onGeoLoad={handleGeoLoad}
            onClearGeo={handleClearGeo}
            drawOnly={drawOnly}
            routes={routes}
            selectedAlt={selectedAlt}
          />
        </aside>

        {/* ============================
            MAPA
           ============================ */}
        <div className="map-wrapper">
          <MapView
            vehicles={vehicles}
            activeVehicle={activeVehicle}
            routes={routes}
            lastPoint={lastPoint}
            handleAddWaypoint={handleAddWaypoint}
            removeWaypointAt={removeWaypointAt}
            clearWaypointsActive={clearWaypointsActive}
            selectedAlt={selectedAlt}
            setSelectedAlt={setSelectedAlt}
            importedGeoJSON={importedGeoJSON}
            drawOnly={drawOnly}
            city={city}
          />
        </div>
      </div>

      {/* ============================
          bloque inferior: estadísticas
         ============================ */}
      <section className="stats-section">
        <StatsPanel
          routes={routes}
          totalSummary={totalSummary}
          vehicles={vehicles}
          activeVehicle={activeVehicle}
        />
      </section>
    </section>
  );
}