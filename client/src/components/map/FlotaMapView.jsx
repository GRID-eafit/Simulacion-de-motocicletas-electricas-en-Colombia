import React, { useMemo, useEffect } from "react";
import L from "leaflet";
import {
    MapContainer,
    TileLayer,
    Marker,
    Polyline,
    LayersControl,
    useMapEvents,
    useMap,
} from "react-leaflet";
import { COLORS } from "../../utils/colors.js";
import { makeColoredIcon } from "../../utils/icons.js";

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

/**
 * Click handler for adding waypoints
 */
function ClickHandler({ onAddWaypoint }) {
    useMapEvents({
        click(e) {
            const lng = +e.latlng.lng.toFixed(6);
            const lat = +e.latlng.lat.toFixed(6);
            onAddWaypoint?.([lng, lat]);
        },
    });
    return null;
}

/**
 * FlotaMapView - Simplified map view for the Flota/Flotilla page
 * This component is independent from the main MapView to allow
 * custom modifications without affecting other functionalities.
 */
export default function FlotaMapView({
    vehicles = [],
    routes = {},
    handleAddWaypoint,
    city = "med",
}) {
    // Centro depende de la ciudad
    const center = useMemo(() => {
        if (city === "bog") return [4.711, -74.072]; // Bogotá
        if (city === "amva") return [6.247, -75.565]; // Valle de Aburrá (AMVA)
        return [6.2442, -75.5812]; // Medellín
    }, [city]);

    // Create marker icons for each vehicle with unique colors and numbers
    const markerIcons = useMemo(
        () =>
            vehicles.map((v, i) => {
                const color = v.color || COLORS[i % COLORS.length];
                return {
                    start: makeColoredIcon(color, i + 1, "start"),
                    end: makeColoredIcon(color, i + 1, "end"),
                    normal: makeColoredIcon(color, i + 1, "normal"),
                };
            }),
        [vehicles]
    );

    return (
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

            {/* Click handler for adding waypoints */}
            <ClickHandler onAddWaypoint={handleAddWaypoint} />

            {/* Waypoint markers */}
            {vehicles.map((v, vi) =>
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

            {/* Route polylines */}
            {Object.entries(routes).map(([routeId, routeInfo]) => {
                if (!routeInfo?.geometry?.coordinates?.length) return null;

                const coords = routeInfo.geometry.coordinates.map(([lng, lat]) => [lat, lng]);
                const color = routeInfo.color || COLORS[0];

                return (
                    <Polyline
                        key={`route-${routeId}`}
                        positions={coords}
                        pathOptions={{ color, weight: 5, opacity: 0.9 }}
                    />
                );
            })}
        </MapContainer>
    );
}
