// client/src/services/api.js

// 1) Base URL del backend: viene de .env o cae por defecto a localhost (modo dev)
// IMPORTANTE: en Vite, import.meta.env.* solo existe si empieza por VITE_
const RAW_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

// Limpia posibles slashes sobrantes al final, tipo "http://ip:8000/"
const API_BASE = String(RAW_BASE).replace(/\/+$/, "");

// 2) Endpoints centralizados
export const API_ROUTES = {
  routes: `${API_BASE}/routes`,
  estaciones: `${API_BASE}/estaciones`,
  flota: `${API_BASE}/flota`,
  health: `${API_BASE}/health`,
};

// Helper opcional para debug
export const getApiBase = () => API_BASE;

// 3) Función para /routes
// body esperado (ej):
// {
//   options: { ... , charger_power_kw, price_per_kwh, city, traffic },
//   vehicles: [{ vehicle_id, waypoints: [{coordinates:[lng,lat]}] }],
//   stations: { coords: [[lng,lat],...], nombre: ["A", ...] }   // opcional
// }
export async function postRoutesJSON(body, opts = {}) {
  const res = await fetch(API_ROUTES.routes, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal: opts.signal,
  });

  if (!res.ok) {
    const txt = await res.text();
    throw new Error(`HTTP ${res.status} - ${txt}`);
  }

  return res.json();
}

/**
 * Envia lista de waypoints al backend /flota
 * @param {{ waypoints: { coordinates: [number, number] }[] }} body
 * @returns {Promise<{
 *   ruta: [number, number][],
 *   distancia: number,
 *   duracion: number,
 *   ruta_carga: [number, number][],
 *   ruta_nodos: [number, number][],
 *   viajes: number[]
 * }>}
 * Note: ruta_carga and ruta_nodos contain index pairs [startIdx, endIdx] 
 * that reference positions in the 'ruta' array for slicing route segments.
 * viajes contains the order of waypoint visits.
 */
export async function postFlota(body, opts = {}) {
  const res = await fetch(API_ROUTES.flota, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal: opts.signal,
  });

  if (!res.ok) {
    const txt = await res.text();
    throw new Error(`HTTP ${res.status} - ${txt}`);
  }

  return res.json(); // Returns { ruta, distancia, duracion, ruta_carga, ruta_nodos }
}

// 4) (Opcional) Ejemplo para /estaciones si lo usas desde aquí
export async function getStations(city, opts = {}) {
  const url = `${API_ROUTES.estaciones}?city=${encodeURIComponent(city)}`;
  const res = await fetch(url, {
    method: "GET",
    signal: opts.signal,
  });

  if (!res.ok) {
    const txt = await res.text();
    throw new Error(`HTTP ${res.status} - ${txt}`);
  }

  return res.json();
}