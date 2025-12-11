import React from "react";
export default function CoordsPanel({ activeVehicleObj, lastPoint, removeWaypointAt, clearWaypointsActive }) {
  const fmt = (n) => (typeof n === "number" ? n.toFixed(6) : n);
  return (
    <div className="coords-panel">
      <div className="coords-header">Coordenadas — {activeVehicleObj.id}</div>
      {lastPoint && (
        <div className="coords-last">
          <div className="coords-last-title">Último punto agregado</div>
          <code>{fmt(lastPoint.lng)}, {fmt(lastPoint.lat)}</code>
        </div>
      )}
      <div className="coords-list-title">Waypoints</div>
      <div className="coords-list">
        {activeVehicleObj.waypoints.length === 0 && (
          <div className="coords-empty">Haz clic en el mapa para agregar puntos.</div>
        )}
        {activeVehicleObj.waypoints.map((wp, idx, arr) => {
          const [lng, lat] = wp.coordinates;
          const label = idx === 0 ? "Inicio" : idx === arr.length - 1 ? "Destino" : "Punto";
          return (
            <div className="coords-item" key={`wp-${idx}`}>
              <span className="coords-index">{idx + 1}.</span>
              <span className={`badge badge-${label === "Inicio" ? "start" : label === "Destino" ? "end" : "mid"}`}>{label}</span>
              <code className="coords-code">{fmt(lng)}, {fmt(lat)}</code>
              <button className="coords-x" title="Eliminar" onClick={() => removeWaypointAt(idx)}>×</button>
            </div>
          );
        })}
      </div>
      <div className="coords-actions">
        <button onClick={clearWaypointsActive}>Borrar todos</button>
      </div>
    </div>
  );
}