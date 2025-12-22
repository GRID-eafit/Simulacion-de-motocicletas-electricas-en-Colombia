import { useEffect, useMemo, useRef, useState } from "react";
import * as api from "../services/api.js";

/**
 * Hook para calcular rutas cuando el usuario lo pide (manual),
 * y opcionalmente en automático si enabled=true (tú ahora lo estás usando manual).
 */
export default function useAutoRoutes({
  vehicles,
  enabled = true,
  city = "med",
  traffic = false,
}) {
  const [routes, setRoutes] = useState({});
  const [selectedAlt, setSelectedAlt] = useState({});
  const [routeError, setRouteError] = useState(null);

  const [options, setOptions] = useState({
    profile: "driving",
    alternatives: false,
    steps: true,
    geometries: "geojson",
    alt_count: 1,
    alt_share: 0.6,
    alt_weight: 1.4,
  });

  const debounceTimer = useRef(null);
  const abortRef = useRef(null);
  const genRef = useRef(0);

  const clearRouteError = () => setRouteError(null);

  // Cancela peticiones pendientes
  const cancelPending = () => {
    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current);
      debounceTimer.current = null;
    }
    if (abortRef.current) {
      abortRef.current.abort();
      abortRef.current = null;
    }
    genRef.current += 1;
  };

  // Limpia rutas de vehículos sin suficientes puntos
  const cleanNow = (vlist) => {
    setRoutes((prev) => {
      const next = { ...prev };
      vlist.forEach((v) => {
        if (v.waypoints.length < 2 && next[v.id]) delete next[v.id];
      });
      return next;
    });

    setSelectedAlt((prev) => {
      const next = { ...prev };
      vlist.forEach((v) => {
        if (v.waypoints.length < 2 && next[v.id] !== undefined) delete next[v.id];
      });
      return next;
    });
  };

  const friendlyMessageFromError = (err) => {
    const raw = String(err?.message || err || "");

    // Si viene el error del backend (FastAPI/ORS) suele traer texto con "Could not find routable point"
    if (
      raw.toLowerCase().includes("routable point") ||
      raw.toLowerCase().includes("could not find") ||
      raw.includes("2010") // ORS code típico
    ) {
      return "No se pudo calcular la ruta con esos puntos. Elige otros puntos e intenta de nuevo.\n\n" +
        "Sugerencia: dale al botón “Limpiar ruta / Limpiar todo”, vuelve a seleccionar puntos válidos sobre la vía y luego presiona “Calcular rutas”.";
    }

    // Si es un 404/400 genérico desde tu throw de api.js
    if (raw.includes("HTTP 404") || raw.includes("HTTP 400") || raw.includes("HTTP 502")) {
      return "No se pudo calcular la ruta con esos puntos. Elige otros puntos e intenta de nuevo.\n\n" +
        "Sugerencia: dale al botón “Limpiar ruta / Limpiar todo”, vuelve a seleccionar puntos y luego presiona “Calcular rutas”.";
    }

    // fallback
    return "Ocurrió un error calculando la ruta.\n\n" +
      "Dale al botón “Limpiar ruta / Limpiar todo” y vuelve a intentar con otros puntos.";
  };

  const recompute = async (vlist) => {
    if (!enabled) return;

    clearRouteError();

    const ready = vlist
      .filter((v) => v.waypoints.length >= 2)
      .map((v) => ({ vehicle_id: v.id, waypoints: v.waypoints }));

    if (ready.length === 0) return;

    cancelPending();

    const localGen = ++genRef.current;
    const ctrl = new AbortController();
    abortRef.current = ctrl;

    const safeOptions = {
      ...options,
      alternatives: false,
      steps: true,
      city,
      traffic,
    };

    let data = null;
    try {
      data = await api.postRoutesJSON(
        { options: safeOptions, vehicles: ready },
        { signal: ctrl.signal }
      );
    } catch (err) {
      if (err?.name === "AbortError") return;
      setRouteError(friendlyMessageFromError(err));
      return;
    }

    if (!data) return;
    if (localGen !== genRef.current) return;

    const map = {};
    (data.routes || []).forEach((r) => {
      map[r.vehicle_id] = r;
    });

    setRoutes((prev) => {
      const keep = {};
      ready.forEach((r) => {
        if (prev[r.vehicle_id]) keep[r.vehicle_id] = prev[r.vehicle_id];
      });
      return { ...keep, ...map };
    });

    setSelectedAlt((prev) => {
      const next = { ...prev };
      ready.forEach((r) => {
        if (next[r.vehicle_id] == null) next[r.vehicle_id] = 0;
      });
      return next;
    });
  };

  useEffect(() => {
    if (!enabled) {
      cancelPending();
      setRoutes({});
      setSelectedAlt({});
      clearRouteError();
      return;
    }

    // Si tú ya lo tienes manual, igual esto no molestará si enabled=false.
    cleanNow(vehicles);

    if (debounceTimer.current) clearTimeout(debounceTimer.current);
    debounceTimer.current = setTimeout(() => recompute(vehicles), 250);

    return () => clearTimeout(debounceTimer.current);
  }, [vehicles, options, enabled, city, traffic]);

  const computeRoutesManual = () => {
    if (enabled) {
      cleanNow(vehicles);
      recompute(vehicles);
    }
  };

  // Resumen total
  const totalSummary = useMemo(() => {
    const list = Object.values(routes);
    const dist = list.reduce((s, r) => s + (r?.summary?.distance || 0), 0);
    const dur = list.reduce((s, r) => s + (r?.summary?.duration || 0), 0);

    return {
      distance_km: (dist / 1000).toFixed(2),
      duration_min: (dur / 60).toFixed(1),
    };
  }, [routes]);

  return {
    options,
    setOptions,
    routes,
    selectedAlt,
    setSelectedAlt,
    totalSummary,
    computeRoutesManual,

    routeError,
    clearRouteError,
  };
}