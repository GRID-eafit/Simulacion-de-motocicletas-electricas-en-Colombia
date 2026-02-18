// client/src/hooks/useAutoRoutes.js
import { useMemo, useRef, useState, useCallback } from "react";
import * as api from "../services/api.js";

/**
 * Hook SOLO MANUAL:
 * - NO calcula rutas automáticamente.
 * - Solo calcula cuando llamas computeRoutesManual().
 *
 * Incluye:
 * - isLoading
 * - resetRoutes (para borrar líneas cuando el usuario hace "Limpiar todo")
 * - stations (default o custom) se envían al backend SIEMPRE que existan y tengan coords
 * - opciones: city, traffic, charger_power_kw, price_per_kwh
 */
export default function useAutoRoutes({
  vehicles,
  enabled = true,
  city = "med",
  traffic = false,
  stations = null, // { coords: [[lng,lat],...], nombre: [...] } o null
}) {
  const [routes, setRoutes] = useState({});
  const [selectedAlt, setSelectedAlt] = useState({});
  const [routeError, setRouteError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const [options, setOptions] = useState({
    profile: "driving",
    alternatives: false,
    steps: true,
    geometries: "geojson",
    alt_count: 1,
    alt_share: 0.6,
    alt_weight: 1.4,

    // 🔌 Recarga + costo
    charger_power_kw: 3.5,
    price_per_kwh: 0.0,
  });

  const abortRef = useRef(null);
  const genRef = useRef(0);

  const clearRouteError = useCallback(() => setRouteError(null), []);

  const cancelPending = useCallback(() => {
    if (abortRef.current) {
      abortRef.current.abort();
      abortRef.current = null;
    }
    genRef.current += 1;
  }, []);

  // ✅ para "Limpiar todo": borra rutas/líneas ya mismo
  const resetRoutes = useCallback(() => {
    cancelPending();
    setIsLoading(false);
    setRoutes({});
    setSelectedAlt({});
    setRouteError(null);
  }, [cancelPending]);

  // Limpia rutas de vehículos sin suficientes puntos
  const cleanNow = useCallback((vlist) => {
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
  }, []);

  const friendlyMessageFromError = (err) => {
    const raw = String(err?.message || err || "").toLowerCase();

    if (
      raw.includes("routable point") ||
      raw.includes("could not find") ||
      raw.includes("2010")
    ) {
      return (
        "No se pudo calcular la ruta con esos puntos.\n\n" +
        "Elige otros puntos sobre la vía.\n\n" +
        "Sugerencia:\n" +
        "1. Presiona “Limpiar ruta / Limpiar todo”\n" +
        "2. Selecciona nuevos puntos\n" +
        "3. Presiona “Calcular rutas”"
      );
    }

    if (raw.includes("http 400") || raw.includes("http 404") || raw.includes("http 502")) {
      return "No se pudo calcular la ruta.\n\nLimpia la ruta y vuelve a intentarlo.";
    }

    return "Ocurrió un error calculando la ruta.\n\nLimpia la ruta y vuelve a intentarlo.";
  };

  const recompute = useCallback(
    async (vlist) => {
      if (!enabled) return;

      clearRouteError();

      const ready = vlist
        .filter((v) => v.waypoints.length >= 2)
        .map((v) => ({ vehicle_id: v.id, waypoints: v.waypoints }));

      if (ready.length === 0) return;

      // cancela request anterior si existía
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
        charger_power_kw: Number(options?.charger_power_kw ?? 0),
        price_per_kwh: Number(options?.price_per_kwh ?? 0),
      };

      // ✅ SIEMPRE mandamos estaciones si existen y tienen coords (default o custom)
      const stationsPayloadToSend =
        stations && Array.isArray(stations.coords) && stations.coords.length
          ? stations
          : null;

      setIsLoading(true);

      let data = null;
      try {
        data = await api.postRoutesJSON(
          {
            options: safeOptions,
            vehicles: ready,
            ...(stationsPayloadToSend ? { stations: stationsPayloadToSend } : {}),
          },
          { signal: ctrl.signal }
        );
      } catch (err) {
        if (err?.name === "AbortError") return;
        setRouteError(friendlyMessageFromError(err));
        setIsLoading(false);
        return;
      }

      if (!data || localGen !== genRef.current) {
        setIsLoading(false);
        return;
      }

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

      setIsLoading(false);
    },
    [enabled, city, traffic, options, stations, cancelPending, clearRouteError]
  );

  // ESTE es el único que dispara el cálculo (manual)
  const computeRoutesManual = useCallback(() => {
    if (!enabled) return;
    cleanNow(vehicles);
    recompute(vehicles);
  }, [enabled, vehicles, cleanNow, recompute]);

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

    isLoading,
    resetRoutes,
  };
}