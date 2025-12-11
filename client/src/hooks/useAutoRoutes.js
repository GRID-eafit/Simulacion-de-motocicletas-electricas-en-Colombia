import { useEffect, useMemo, useRef, useState } from "react";
import * as api from "../services/api.js";

/**
 * Hook para calcular rutas automáticamente cuando cambian:
 * - vehículos
 * - opciones
 * - ciudad (med | bog | amva)
 * - tráfico (true | false)
 */
export default function useAutoRoutes({
  vehicles,
  enabled = true,
  city = "med",
  traffic = false, // 👈 nuevo parámetro
}) {
  const [routes, setRoutes] = useState({});
  const [selectedAlt, setSelectedAlt] = useState({});
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
        if (v.waypoints.length < 2 && next[v.id] !== undefined)
          delete next[v.id];
      });
      return next;
    });
  };

  const recompute = async (vlist) => {
    if (!enabled) return;

    const ready = vlist
      .filter((v) => v.waypoints.length >= 2)
      .map((v) => ({ vehicle_id: v.id, waypoints: v.waypoints }));

    if (ready.length === 0) return;

    cancelPending();

    const localGen = ++genRef.current;
    const ctrl = new AbortController();
    abortRef.current = ctrl;

    // 👇 Enviar ciudad + tráfico al backend
    const safeOptions = {
      ...options,
      alternatives: false,
      steps: true,
      city,
      traffic, // 👈 enviar estado de tráfico
    };

    const data = await api
      .postRoutesJSON(
        { options: safeOptions, vehicles: ready },
        { signal: ctrl.signal }
      )
      .catch((err) => {
        if (err?.name === "AbortError") return null;
        throw err;
      });

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
      return;
    }

    cleanNow(vehicles);

    if (debounceTimer.current) clearTimeout(debounceTimer.current);

    debounceTimer.current = setTimeout(() => recompute(vehicles), 250);

    return () => clearTimeout(debounceTimer.current);
  }, [vehicles, options, enabled, city, traffic]); // 👈 recalcular también si cambia tráfico

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
  };
}