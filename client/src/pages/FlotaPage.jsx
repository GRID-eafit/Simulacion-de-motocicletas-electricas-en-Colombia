import React, { useState, useMemo } from "react";
import FlotaMapView from "../components/map/FlotaMapView.jsx";
import { postFlota } from "../services/api.js";
import { COLORS } from "../utils/colors.js";

const CHARGING_ROUTE_COLOR = "#7C3AED"; // Purple for all charging routes

export default function FlotillaPage() {
    const [waypoints, setWaypoints] = useState([]);
    const [routeData, setRouteData] = useState(null); // Store full response
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [city, setCity] = useState("med"); // Default city

    // Create vehicles array: one for each waypoint with unique colors
    const vehicles = useMemo(() => {
        return waypoints.map((coord, idx) => ({
            id: `waypoint-${idx}`,
            waypoints: [{ coordinates: coord }],
            color: COLORS[idx % COLORS.length],
        }));
    }, [waypoints]);

    // Create routes from ruta_carga and ruta_nodos
    // These contain waypoint indices [start, end] that we use to slice the complete route
    const routes = useMemo(() => {
        if (!routeData || !routeData.ruta) return {};

        const routesObj = {};
        const completeRoute = routeData.ruta; // Array of [lng, lat] coordinates

        // Add charging routes (all same color)
        // ruta_carga contains index pairs like [[125, 246], [508, 644]]
        if (routeData.ruta_carga && routeData.ruta_carga.length > 0) {
            routeData.ruta_carga.forEach((segment, idx) => {
                const [startIdx, endIdx] = segment;

                // Slice the complete route from startIdx to endIdx (inclusive)
                const segmentCoords = completeRoute.slice(startIdx, endIdx + 1);

                if (segmentCoords.length > 0) {
                    routesObj[`carga-${idx}`] = {
                        geometry: {
                            type: "LineString",
                            coordinates: segmentCoords,
                        },
                        color: CHARGING_ROUTE_COLOR,
                    };
                }
            });
        }

        // Add node routes (different colors)
        // ruta_nodos contains index pairs like [[0, 125], [246, 352], [352, 508]]
        if (routeData.ruta_nodos && routeData.ruta_nodos.length > 0) {
            routeData.ruta_nodos.forEach((segment, idx) => {
                const [startIdx, endIdx] = segment;

                // Slice the complete route from startIdx to endIdx (inclusive)
                const segmentCoords = completeRoute.slice(startIdx, endIdx + 1);

                if (segmentCoords.length > 0) {
                    routesObj[`nodo-${idx}`] = {
                        geometry: {
                            type: "LineString",
                            coordinates: segmentCoords,
                        },
                        color: COLORS[idx % COLORS.length],
                    };
                }
            });
        }

        return routesObj;
    }, [routeData]);

    const handleAddWaypoint = (coord) => {
        setWaypoints((prev) => [...prev, coord]);
        // Clear previous route when modifying points
        setRouteData(null);
        setError(null);
    };

    const removeWaypointAt = (vehicleIdx, wpIdx) => {
        // Remove waypoint at the given index
        setWaypoints((prev) => prev.filter((_, i) => i !== vehicleIdx));
        setRouteData(null);
    };

    const clearAll = () => {
        setWaypoints([]);
        setRouteData(null);
        setError(null);
    };

    const handleCalculate = async () => {
        if (waypoints.length < 2) {
            setError("Selecciona al menos 2 puntos.");
            return;
        }

        setLoading(true);
        setError(null);

        try {
            // Construct payload STRICTLY as { waypoints: [{coordinates: [lng, lat]}, ...] }
            const payload = {
                waypoints: waypoints.map(w => ({ coordinates: w }))
            };

            const result = await postFlota(payload);
            // result contains: { ruta, distancia, duracion, ruta_carga, ruta_nodos }
            setRouteData(result);

        } catch (err) {
            console.error(err);
            setError("Error al calcular ruta de flotilla.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <section className="page">
            <div className="page-main">
                <aside className="sidebar">
                    <div className="card">
                        <h2 className="panel-title">Flotilla</h2>
                        <div className="divider" />

                        <div className="kv">
                            <span className="k">Puntos seleccionados:</span>
                            <span className="v">{waypoints.length}</span>
                        </div>

                        <div className="row" style={{ marginTop: "1rem" }}>
                            <button
                                className="btn"
                                onClick={handleCalculate}
                                disabled={loading || waypoints.length < 2}
                            >
                                {loading ? "Cargando..." : "Calcular Flotilla"}
                            </button>
                        </div>

                        {error && (
                            <div style={{ marginTop: 10, fontSize: 13, color: "#b91c1c" }}>
                                {error}
                            </div>
                        )}

                        <div className="row" style={{ marginTop: "0.5rem" }}>
                            <button
                                className="btn ghost"
                                onClick={clearAll}
                                disabled={loading || waypoints.length === 0}
                            >
                                Limpiar
                            </button>
                        </div>

                        {/* Results section */}
                        {routeData && (
                            <>
                                <div className="divider" />
                                <h3 className="panel-title" style={{ fontSize: "1rem", marginBottom: "0.5rem" }}>Resultados</h3>

                                <div className="kv">
                                    <span className="k">Distancia:</span>
                                    <span className="v">{(routeData.distancia / 1000).toFixed(2)} km</span>
                                </div>

                                <div className="kv">
                                    <span className="k">Duración:</span>
                                    <span className="v">{Math.round(routeData.duracion / 60)} min</span>
                                </div>

                                {routeData.viajes && routeData.viajes.length > 0 && (
                                    <>
                                        <div className="divider" />
                                        <h3 className="panel-title" style={{ fontSize: "1rem", marginBottom: "0.5rem" }}>Orden de visitas</h3>
                                        <div style={{ fontSize: "0.875rem", lineHeight: "1.5" }}>
                                            {routeData.viajes.map((punto, idx) => (
                                                <div key={idx} style={{ marginBottom: "0.25rem" }}>
                                                    <span style={{ fontWeight: "500" }}>{idx + 1}.</span> Punto {punto}
                                                </div>
                                            ))}
                                        </div>
                                    </>
                                )}
                            </>
                        )}

                        <div className="divider" />
                        <div className="small">
                            Selecciona puntos en el mapa para planificar una ruta de flotilla.
                        </div>
                    </div>
                </aside>

                <div className="map-wrapper" style={{ minHeight: "75vh" }}>
                    <FlotaMapView
                        vehicles={vehicles}
                        routes={routes}
                        handleAddWaypoint={handleAddWaypoint}
                        city={city}
                    />
                </div>
            </div>
        </section>
    );
}
