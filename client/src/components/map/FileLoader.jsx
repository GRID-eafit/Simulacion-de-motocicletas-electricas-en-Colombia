import React, { useRef, useState } from "react";

/**
 * Carga .json o .geojson y los normaliza a FeatureCollection (LineString).
 * NO llama ORS: el resultado se pinta como capa importada.
 */
export default function FileLoader({
  onGeojson = () => {},   // (featureCollection) => void
  onClearGeo = () => {},  // () => void
}) {
  const inputRef = useRef(null);
  const [filename, setFilename] = useState("");

  const onPickFile = () => inputRef.current?.click();

  const readAsText = (file) =>
    new Promise((resolve, reject) => {
      const r = new FileReader();
      r.onload = () => resolve(r.result);
      r.onerror = reject;
      r.readAsText(file);
    });

  const to2D = (coords) => {
    if (!Array.isArray(coords)) return [];
    const out = [];
    for (const c of coords) {
      if (!Array.isArray(c) || c.length < 2) continue;
      const lon = Number(c[0]);
      const lat = Number(c[1]);
      if (Number.isFinite(lon) && Number.isFinite(lat)) out.push([lon, lat]);
    }
    return out;
  };

  const fromBikes = (src) => {
    // formato { bikes: [ [ { coords: [...], origen?, destino? ... }, ...], ... ] }
    const features = [];
    (src.bikes || []).forEach((group, gi) => {
      (group || []).forEach((seg, li) => {
        const coords = to2D(seg?.coords || []);
        if (coords.length < 2) return;
        features.push({
          type: "Feature",
          properties: {
            vehicle_id: `moto-${gi + 1}`,
            leg: li + 1,
            origen: seg.origen ?? null,
            destino: seg.destino ?? null,
          },
          geometry: { type: "LineString", coordinates: coords },
        });
      });
    });
    return { type: "FeatureCollection", features };
  };

  const sanitizeFC = (fc) => {
    const features = [];
    (fc.features || []).forEach((feat) => {
      if (feat?.geometry?.type !== "LineString") return;
      const coords = to2D(feat.geometry.coordinates || []);
      if (coords.length < 2) return;
      features.push({
        type: "Feature",
        properties: feat.properties || {},
        geometry: { type: "LineString", coordinates: coords },
      });
    });
    return { type: "FeatureCollection", features };
  };

  const normalizeToFC = (json) => {
    if (json?.type === "FeatureCollection" && Array.isArray(json.features)) {
      return sanitizeFC(json);
    }
    if (Array.isArray(json?.bikes)) {
      return fromBikes(json);
    }
    // formato “app”: { vehicles:[{waypoints:[{coordinates:[lng,lat]}]}] }
    if (Array.isArray(json?.vehicles)) {
      const features = (json.vehicles || [])
        .filter((v) => (v.waypoints || []).length >= 2)
        .map((v) => ({
          type: "Feature",
          properties: { vehicle_id: v.id || v.vehicle_id || "moto" },
          geometry: {
            type: "LineString",
            coordinates: (v.waypoints || []).map((wp) => [wp.coordinates[0], wp.coordinates[1]]),
          },
        }));
      return { type: "FeatureCollection", features };
    }
    throw new Error("Formato no reconocido: usa FeatureCollection, bikes o vehicles.");
  };

  const handleFile = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setFilename(file.name);
    try {
      const txt = await readAsText(file);
      const json = JSON.parse(txt);
      const fc = normalizeToFC(json);
      onGeojson(fc); // solo pintar en el mapa
    } catch (err) {
      console.error(err);
      alert("No se pudo leer el archivo o el formato no es válido.\nDetalle: " + err.message);
    } finally {
      e.target.value = "";
    }
  };

  return (
    <div className="loader">
      <div className="row" style={{ justifyContent: "space-between", alignItems: "center" }}>
        <div>
          {/*<div style={{ fontWeight: 700 }}>Archivo de rutas (pintar)</div>*/}
          <div className="hint" style={{ fontSize: 12, color: "#6b7280" }}>
            Acepta <code>.json</code> o <code>.geojson</code>. Se dibuja sin usar ORS.
          </div>
        </div>
        <div className="row" style={{ gap: 6 }}>
          <button className="btn" onClick={onPickFile}>Cargar</button>
          <button className="btn ghost" onClick={onClearGeo}>Limpiar capa</button>
        </div>
      </div>

      {filename && (
        <div className="small" style={{ marginTop: 4, color: "#374151" }}>
          Último: <strong>{filename}</strong>
        </div>
      )}

      <input
        ref={inputRef}
        type="file"
        accept=".json,.geojson,application/json,application/geo+json"
        style={{ display: "none" }}
        onChange={handleFile}
      />
    </div>
  );
}