import { useMemo, useRef, useState } from "react";
import * as api from "../services/api.js";

/**
 * Hook para calcular rutas SOLO de forma manual
 * (evita llamadas automáticas a ORS)
 */
export default function useAutoRoutes({
  vehicles,
  enabled = true,
  city = "med",
  traffic = false,
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

  const abortRef = useRef(null);

  const cancelPending = () => {
    if (abortRef.current) {
      abortRef.current.abort();
      abortRef.current = null;
    }
  };

  const computeRoutesManual = async () => {
    if (!enabled) return;

    const ready = vehicles
      .filter((v) => v.waypoints.length >= 2)
      .map((v) => ({ vehicle_id: v.id, waypoints: v.waypoints }));

    if (ready.length === 0) return;

    cancelPending();

    const ctrl = new AbortController();
    abortRef.current = ctrl;

    const safeOptions = {
      ...options,
      alternatives: false,
      steps: true,
      city,
      traffic,
    };

    try {
      const data = await api.postRoutesJSON(
        { options: safeOptions, vehicles: ready },
        { signal: ctrl.signal }
      );

      const map = {};
      (data.routes || []).forEach((r) => {
        map[r.vehicle_id] = r;
      });

      setRoutes(map);

      setSelectedAlt((prev) => {
        const next = { ...prev };
        ready.forEach((r) => {
          if (next[r.vehicle_id] == null) next[r.vehicle_id] = 0;
        });
        return next;
      });
    } catch (err) {
      if (err?.name !== "AbortError") {
        console.error("Error calculando rutas:", err);
      }
    }
  };

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