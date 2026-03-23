import React, { useMemo, useEffect, useCallback } from "react";
import L from "leaflet";
import {
  MapContainer,
  TileLayer,
  Marker,
  Polyline,
  LayersControl,
  GeoJSON,
  useMapEvents,
  Tooltip,
  useMap,
} from "react-leaflet";
import { COLORS } from "../../utils/colors.js";
import { makeColoredIcon } from "../../utils/icons.js";
import CoordsPanel from "./CoordsPanel.jsx";

const VITE_API_URL = import.meta.env.VITE_API_URL;

// ================== CONFIG ICONS ==================
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

// Componente para recentrar el mapa cuando cambia la ciudad
function RecenterOnCity({ center }) {
  const map = useMap();
  useEffect(() => {
    map.setView(center);
  }, [center, map]);
  return null;
}

// Color map for station tipo
const TIPO_COLOR = {
  "Estándar": "#1a1a1a",
  "Alta Capacidad": "#f59e0b",
  "Intercambio": "#2563eb",
};

// Returns a DivIcon with the appropriate color for the station tipo
function makeChargingIcon(tipo) {
  const fill = TIPO_COLOR[tipo] || "#1a1a1a";
  return new L.DivIcon({
    className: "charging-station-icon",
    html: `
      <svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 36 36">
        <circle cx="18" cy="18" r="16" fill="${fill}" stroke="${fill}" stroke-width="1.5" />
        <path d="M17 6 L9 20 H17 L13 30 L25 14 H17 Z" fill="white" stroke="white" stroke-width="1.0" />
      </svg>`,
    iconSize: [32, 32],
    iconAnchor: [16, 16],
  });
}

/**
 * Click handler:
 * - Si stationsMode === "custom": click en mapa agrega estación
 * - Si no: click en mapa agrega waypoint (normal)
 */
function ClickHandler({ disabled, stationsMode, onAddWaypoint, onAddStation }) {
  useMapEvents({
    click(e) {
      if (disabled) return;

      const lng = +e.latlng.lng.toFixed(6);
      const lat = +e.latlng.lat.toFixed(6);

      if (stationsMode === "custom") {
        onAddStation?.([lng, lat]);
      } else {
        onAddWaypoint?.([lng, lat]);
      }
    },
  });
  return null;
}

export default function MapView({
  vehicles,
  activeVehicle,
  routes = {},
  lastPoint,
  handleAddWaypoint,
  removeWaypointAt,
  clearWaypointsActive,
  selectedAlt = {},
  setSelectedAlt = () => { },
  importedGeoJSON,
  drawOnly = false,
  city = "med",

  stationsMode = "default", // "default" | "custom"
  stationsPayload = null, // { coords: [[lng,lat]], nombre: [string], tipo: [string] }
  setStationsPayload = () => { },
  customStationTipo = "Estándar", // tipo to use when adding custom stations
}) {
  // Centro depende de la ciudad
  const center = useMemo(() => {
    if (city === "bog") return [4.711, -74.072]; // Bogotá
    if (city === "amva") return [6.247, -75.565]; // Valle de Aburrá (AMVA)
    return [6.2442, -75.5812]; // Medellín
  }, [city]);

  // ============================
  // Stations view-model
  // ============================
  const chargingStations = useMemo(() => {
    const coords = stationsPayload?.coords || [];
    const names = stationsPayload?.nombre || [];
    const tipos = stationsPayload?.tipo || [];

    return coords.map((c, i) => ({
      name: names[i] || `Estación ${i + 1}`,
      tipo: tipos[i] || "Estándar",
      coordinates: c, // [lng, lat]
      idx: i,
    }));
  }, [stationsPayload]);

  // Helper seguro: permite setStationsPayload(fn) o setStationsPayload(obj)
  const safeSetStations = useCallback(
    (updater) => {
      setStationsPayload((prev) => {
        const current =
          prev && typeof prev === "object" ? prev : { coords: [], nombre: [] };
        if (typeof updater === "function") return updater(current);
        return updater;
      });
    },
    [setStationsPayload]
  );

  const addStation = useCallback(
    (lngLat) => {
      safeSetStations((prev) => {
        const prevCoords = Array.isArray(prev?.coords) ? prev.coords : [];
        const prevNames = Array.isArray(prev?.nombre) ? prev.nombre : [];
        const prevTipos = Array.isArray(prev?.tipo) ? prev.tipo : [];

        const nextCoords = [...prevCoords, lngLat];
        const nextNames = [...prevNames, `Estación ${nextCoords.length}`];
        const nextTipos = [...prevTipos, customStationTipo];

        return { coords: nextCoords, nombre: nextNames, tipo: nextTipos };
      });
    },
    [safeSetStations, customStationTipo]
  );

  const removeStation = useCallback(
    (stationIdx) => {
      safeSetStations((prev) => {
        const prevCoords = Array.isArray(prev?.coords) ? prev.coords : [];
        const prevNames = Array.isArray(prev?.nombre) ? prev.nombre : [];
        const prevTipos = Array.isArray(prev?.tipo) ? prev.tipo : [];

        const nextCoords = prevCoords.filter((_, i) => i !== stationIdx);
        const nextNames = prevNames.filter((_, i) => i !== stationIdx);
        const nextTipos = prevTipos.filter((_, i) => i !== stationIdx);

        // Normaliza nombres para que queden Estación 1..N
        const normalizedNames = nextCoords.map((_, i) => {
          const n = nextNames[i];
          return n && String(n).trim().length ? n : `Estación ${i + 1}`;
        });

        return { coords: nextCoords, nombre: normalizedNames, tipo: nextTipos };
      });
    },
    [safeSetStations]
  );

  // ============================================

  const importedColorMap = useMemo(() => {
    const map = new Map();
    if (importedGeoJSON?.features?.length) {
      let idx = 0;
      for (const f of importedGeoJSON.features) {
        const vid =
          (f.properties && f.properties.vehicle_id) ||
          (f.properties && f.properties.id) ||
          "otros";
        if (!map.has(vid)) {
          map.set(vid, COLORS[idx % COLORS.length]);
          idx++;
        }
      }
    }
    return map;
  }, [importedGeoJSON?.features?.length]);

  const markerIcons = useMemo(
    () =>
      vehicles.map((_, i) => ({
        start: makeColoredIcon(COLORS[i % COLORS.length], i + 1, "start"),
        end: makeColoredIcon(COLORS[i % COLORS.length], i + 1, "end"),
        normal: makeColoredIcon(COLORS[i % COLORS.length], i + 1, "normal"),
      })),
    [vehicles.length]
  );

  const activeId = vehicles[activeVehicle]?.id;
  const activeRouteInfo = routes[activeId];
  const selectedAltIndex = selectedAlt?.[activeId] ?? 0;

  return (
    <>
      {!drawOnly && (
        <CoordsPanel
          activeVehicleObj={vehicles[activeVehicle]}
          lastPoint={lastPoint}
          removeWaypointAt={removeWaypointAt}
          clearWaypointsActive={clearWaypointsActive}
          activeRouteInfo={activeRouteInfo}
          selectedAltIndex={selectedAltIndex}
          onChangeSelectedAlt={(i) =>
            setSelectedAlt((s) => ({ ...s, [activeId]: i }))
          }
        />
      )}

      <MapContainer
        center={center}
        zoom={14}
        className="map-root"
        zoomControl
        preferCanvas
      >
        <RecenterOnCity center={center} />

        <LayersControl position="topright">
          <LayersControl.BaseLayer checked name="CARTO (proxy)">
            <TileLayer
              url={`${VITE_API_URL}/tiles/carto/{z}/{x}/{y}.png`}
              attribution="© OpenStreetMap contributors · © CARTO"
              detectRetina
              maxZoom={18}
            />
          </LayersControl.BaseLayer>
        </LayersControl>

        {/* ✅ Click handler: waypoint o estación según modo */}
        {!drawOnly && (
          <ClickHandler
            disabled={false}
            stationsMode={stationsMode}
            onAddWaypoint={handleAddWaypoint}
            onAddStation={addStation}
          />
        )}

        {/* Capa importada */}
        {importedGeoJSON?.features?.length > 0 && (
          <GeoJSON
            key="imported"
            data={importedGeoJSON}
            style={(feat) => {
              const vid =
                (feat.properties && feat.properties.vehicle_id) ||
                (feat.properties && feat.properties.id) ||
                "otros";
              const color = importedColorMap.get(vid) || "#6b7280";
              return { color, weight: 6, opacity: 1.0 };
            }}
          />
        )}

        {/* Waypoints */}
        {!drawOnly &&
          vehicles.map((v, vi) =>
            v.waypoints.map((wp, idx) => {
              const pos = [wp.coordinates[1], wp.coordinates[0]];
              const icon =
                idx === 0
                  ? markerIcons[vi].start
                  : idx === v.waypoints.length - 1
                    ? markerIcons[vi].end
                    : markerIcons[vi].normal;

              return (
                <Marker
                  key={`${v.id}-wp-${idx}`}
                  position={pos}
                  icon={icon}
                />
              );
            })
          )}

        {/* Polilíneas de rutas */}
        {!drawOnly &&
          vehicles.map((v, idx) => {
            const info = routes[v.id];
            if (!info) return null;

            const sel = selectedAlt?.[v.id] ?? 0;
            const chosen =
              sel === 0 ? info.geometry : info.alternatives?.[sel - 1]?.geometry;
            if (!chosen?.coordinates?.length) return null;

            const coords = chosen.coordinates.map(([lng, lat]) => [lat, lng]);

            return (
              <Polyline
                key={`route-${v.id}`}
                positions={coords}
                pathOptions={{ color: COLORS[idx], weight: 5, opacity: 0.9 }}
              />
            );
          })}

        {/* Recargas realizadas */}
        {!drawOnly &&
          Object.entries(routes).map(([vehicleId, routeData]) => {
            if (!routeData?.charge_points?.length) return null;

            return routeData.charge_points.map((cp, i) => {
              const [lon, lat] = cp.start_coords;
              return (
                <Marker
                  key={`charge-${vehicleId}-${i}`}
                  position={[lat, lon]}
                  icon={makeColoredIcon("#7a318dff", i + 1, "normal")}
                />
              );
            });
          })}

        {/* Estaciones de carga (default o custom) */}
        {chargingStations.map((station) => (
          <Marker
            key={`station-${station.idx}`}
            position={[station.coordinates[1], station.coordinates[0]]}
            icon={makeChargingIcon(station.tipo)}
            eventHandlers={
              stationsMode === "custom"
                ? {
                  click: (ev) => {
                    // evita que el click se interprete como click en mapa
                    ev?.originalEvent?.stopPropagation?.();
                    removeStation(station.idx);
                  },
                }
                : undefined
            }
          >
            <Tooltip direction="top" offset={[0, -10]} opacity={1}>
              <span>
                {station.name}
                {station.tipo ? ` · ${station.tipo}` : ""}
                {stationsMode === "custom" ? " (click para borrar)" : ""}
              </span>
            </Tooltip>
          </Marker>
        ))}
      </MapContainer>
    </>
  );
}