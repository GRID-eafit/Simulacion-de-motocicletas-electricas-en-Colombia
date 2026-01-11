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