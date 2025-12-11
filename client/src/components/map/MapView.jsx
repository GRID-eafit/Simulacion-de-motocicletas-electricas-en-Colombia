import React, { useMemo, useState, useEffect } from "react";
import L from "leaflet";
import axios from "axios";
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

function ClickToAdd({ onAdd }) {
  useMapEvents({
    click(e) {
      onAdd([+e.latlng.lng.toFixed(6), +e.latlng.lat.toFixed(6)]);
    },
  });
  return null;
}

// Componente para recentrar el mapa cuando cambia la ciudad
function RecenterOnCity({ center }) {
  const map = useMap();
  useEffect(() => {
    map.setView(center);
  }, [center, map]);
  return null;
}

// Custom icon for charging stations
const chargingIcon = new L.DivIcon({
  className: "charging-station-icon",
  html: `
    <svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 36 36">
      <circle cx="18" cy="18" r="16" fill="#000000ff" stroke="#000000ff" stroke-width="1.5" />
      <path d="M17 6 L9 20 H17 L13 30 L25 14 H17 Z" fill="white" stroke="#ffffffff" stroke-width="1.0" />
    </svg>`,
  iconSize: [32, 32],
  iconAnchor: [16, 16],
});

export default function MapView({
  vehicles,
  activeVehicle,
  routes = {},
  lastPoint,
  handleAddWaypoint,
  removeWaypointAt,
  clearWaypointsActive,
  selectedAlt = {},
  setSelectedAlt = () => {},
  importedGeoJSON,
  drawOnly = false,
  city = "med",
}) {
  // Centro depende de la ciudad
  const center = useMemo(() => {
    if (city === "bog") return [4.711, -74.072];      // Bogotá
    if (city === "amva") return [6.247, -75.565];     // Valle de Aburrá (AMVA)
    return [6.2442, -75.5812];                        // Medellín
  }, [city]);

  // ========= POIs / Charging Stations =========
  const [chargingStations, setChargingStations] = useState([]);

  useEffect(() => {
    async function fetchStations() {
      try {
        const res = await axios.get(`${VITE_API_URL}/estaciones?city=${city}`);
        const data = res.data;

        if (data?.coords && data?.nombre) {
          const merged = data.coords.map((c, i) => ({
            name: data.nombre[i] || `Estación ${i + 1}`,
            coordinates: c,
          }));
          setChargingStations(merged);
        } else {
          console.warn("Formato inesperado de estaciones:", data);
        }
      } catch (err) {
        console.error("Error al cargar estaciones:", err);
      }
    }

    fetchStations();
  }, [city]);

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

        {!drawOnly && <ClickToAdd onAdd={handleAddWaypoint} />}

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
              return {
                color,
                weight: 6,
                opacity: 1.0,
              };
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
                <Marker key={`${v.id}-wp-${idx}`} position={pos} icon={icon} />
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
              sel === 0
                ? info.geometry
                : info.alternatives?.[sel - 1]?.geometry;

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

        {/* Estaciones de carga */}
        {chargingStations.map((station, idx) => (
          <Marker
            key={`station-${idx}`}
            position={[station.coordinates[1], station.coordinates[0]]}
            icon={chargingIcon}
          >
            <Tooltip direction="top" offset={[0, -10]} opacity={1}>
              <span>{station.name}</span>
            </Tooltip>
          </Marker>
        ))}
      </MapContainer>
    </>
  );
}