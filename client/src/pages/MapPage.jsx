import React, { useEffect, useState } from "react";
import ControlsPanel from "../components/map/ControlsPanel.jsx";
import MapView from "../components/map/MapView.jsx";
import useVehicles from "../hooks/useVehicles.js";
import useAutoRoutes from "../hooks/useAutoRoutes.js";
import StatsPanel from "../components/map/StatsPanel.jsx";

function FloatingToast({ open, title, message, onClose }) {
  if (!open) return null;

  return (
    <div
      style={{
        position: "fixed",
        top: 56,
        left: "50%",
        transform: "translateX(-50%)",
        zIndex: 9999,
        width: "min(560px, calc(100vw - 32px))",

        background: "rgba(248, 250, 252, 0.98)",
        color: "#0f172a",
        borderRadius: 16,
        padding: 16,

        boxShadow:
          "0 10px 25px rgba(0,0,0,0.08), 0 4px 10px rgba(0,0,0,0.06)",
        border: "1px solid rgba(0,0,0,0.06)",
        backdropFilter: "blur(6px)",
      }}
      role="alert"
      aria-live="polite"
    >
      <div style={{ display: "flex", gap: 14, alignItems: "flex-start" }}>
        {/* Icono */}
        <div
          style={{
            width: 42,
            height: 42,
            borderRadius: 12,
            display: "grid",
            placeItems: "center",
            background: "rgba(0,0,0,0.08)",
            color: "#000000",
            fontSize: 20,
            flexShrink: 0,
          }}
        >
          ⚠️
        </div>

        {/* Texto */}
        <div style={{ flex: 1 }}>
          <div
            style={{
              fontWeight: 700,
              fontSize: 15,
              marginBottom: 4,
            }}
          >
            {title}
          </div>

          <div
            style={{
              fontSize: 13.5,
              lineHeight: 1.45,
              color: "#334155",
              whiteSpace: "pre-line",
            }}
          >
            {message}
          </div>

          {/* Acción */}
          <div
            style={{
              display: "flex",
              justifyContent: "flex-end",
              marginTop: 12,
            }}
          >
            <button
              type="button"
              onClick={onClose}
              style={{
                background: "#000000",
                color: "#ffffff",
                border: "none",
                borderRadius: 10,
                padding: "8px 16px",
                fontSize: 13,
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              Entendido
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

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

  const [importedGeoJSON, setImportedGeoJSON] = useState(null);
  const [drawOnly, setDrawOnly] = useState(false);

  const [city, setCity] = useState("med");
  const [traffic, setTraffic] = useState(false);

  const [toastOpen, setToastOpen] = useState(false);

  const vehiclesForRouting = drawOnly ? [] : vehicles;

  const {
    options,
    setOptions,
    routes,
    selectedAlt,
    setSelectedAlt,
    totalSummary,
    computeRoutesManual,

    routeError,
    clearRouteError,
  } = useAutoRoutes({
    vehicles: vehiclesForRouting,
    enabled: !drawOnly, // si lo estás usando manual, esto puede seguir así
    city,
    traffic,
  });

  // Si llega un error, abrimos el toast
  useEffect(() => {
    if (routeError) setToastOpen(true);
  }, [routeError]);

  // Auto-cierre del toast
  useEffect(() => {
    if (!toastOpen) return;
    const t = setTimeout(() => {
      setToastOpen(false);
      clearRouteError();
    }, 7000);
    return () => clearTimeout(t);
  }, [toastOpen, clearRouteError]);

  const handleGeoLoad = (fc) => {
    setImportedGeoJSON(fc);
    setDrawOnly(true);
  };

  const handleClearGeo = () => {
    setImportedGeoJSON(null);
    setDrawOnly(false);
  };

  const handleChangeCity = (newCity) => {
    if (newCity === city) return;

    clearAll();
    setImportedGeoJSON(null);
    setDrawOnly(false);
    setLastPoint(null);

    // también cerrar toast al cambiar ciudad
    setToastOpen(false);
    clearRouteError();

    setCity(newCity);
  };

  return (
    <section className="page">
      <FloatingToast
        open={toastOpen && Boolean(routeError)}
        title="No se pudo calcular la ruta"
        message={
          routeError ||
          "No se pudo calcular la ruta con esos puntos. Elige otros puntos e intenta de nuevo."
        }
        onClose={() => {
          setToastOpen(false);
          clearRouteError();
        }}
      />

      <div className="page-main">
        <aside className="sidebar">
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

          <ControlsPanel
            options={options}
            setOptions={setOptions}
            vehicles={vehicles}
            activeVehicle={activeVehicle}
            setActiveVehicle={setActiveVehicle}
            addVehicle={addVehicle}
            removeVehicle={removeVehicle}
            undoWaypoint={undoWaypoint}
            clearAll={() => {
              setToastOpen(false);
              clearRouteError();
              clearAll();
            }}
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