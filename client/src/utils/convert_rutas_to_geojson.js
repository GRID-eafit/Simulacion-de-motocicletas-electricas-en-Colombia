#!/usr/bin/env node
/**
 * Conversor flexible a GeoJSON + saneo 3D→2D.
 *
 * - Si recibe { bikes: [...] } => genera FeatureCollection con LineString por segmento.
 * - Si recibe GeoJSON FeatureCollection => lo sanea a 2D (opcionalmente preserva 3D con --keep3d).
 *
 * Uso:
 *   node convert_rutas_to_geojson.js --in rutas_example.json --out rutas_example.geojson
 *   node convert_rutas_to_geojson.js --in rutas.geojson --out rutas_2d.geojson
 *   node convert_rutas_to_geojson.js --in rutas.geojson --out rutas_keep3d.geojson --keep3d
 */

import fs from "node:fs";
import path from "node:path";

// ---------------- CLI args ----------------
const args = process.argv.slice(2);
function getArg(name, def = undefined) {
  const i = args.findIndex(a => a === name || a.startsWith(`${name}=`));
  if (i === -1) return def;
  const a = args[i];
  if (a.includes("=")) return a.split("=")[1];
  // next token as value
  const next = args[i + 1];
  if (!next || next.startsWith("--")) return true; // boolean flag
  return next;
}
const inputPath  = getArg("--in", "rutas_example.json");
const outputPath = getArg("--out", "rutas_example.geojson");
const keep3d     = !!getArg("--keep3d", false);

// --------------- helpers -----------------
const readJSON = (p) => JSON.parse(fs.readFileSync(p, "utf8"));
const writeJSON = (p, data) => fs.writeFileSync(p, JSON.stringify(data, null, 2), "utf8");

function to2D(coords) {
  // coords: [[lon,lat], [lon,lat,alt], ...]
  // Devuelve: [[lon,lat], ...]
  if (!Array.isArray(coords)) return [];
  const out = [];
  for (const c of coords) {
    if (!Array.isArray(c) || c.length < 2) continue;
    const lon = Number(c[0]);
    const lat = Number(c[1]);
    if (Number.isFinite(lon) && Number.isFinite(lat)) {
      out.push([lon, lat]);
    }
  }
  return out;
}

function maybe2D(coords) {
  // Si keep3d=false => fuerza 2D, si keep3d=true => deja como viene.
  if (keep3d) return coords;
  return to2D(coords);
}

function isFeatureCollection(obj) {
  return obj && obj.type === "FeatureCollection" && Array.isArray(obj.features);
}

function fromBikesToFC(src) {
  // src: { bikes: [ [ { coords:[ [lon,lat,alt?], ...], origen?, destino?, ... }, ... ], ... ] }
  if (!src.bikes || !Array.isArray(src.bikes)) {
    throw new Error("El archivo no tiene el formato esperado: se esperaba una propiedad 'bikes' (array).");
  }
  const features = [];
  src.bikes.forEach((bikeGroup, gi) => {
    if (!Array.isArray(bikeGroup)) return;
    bikeGroup.forEach((segmento, li) => {
      const coords = segmento?.coords;
      if (!Array.isArray(coords) || coords.length < 2) return;

      const processedCoords = maybe2D(coords);
      if (processedCoords.length < 2) return;

      // properties: preserva lo útil y añade identificador de moto/segmento
      const props = {
        vehicle_id: `moto-${gi + 1}`,
        leg: li + 1,
      };
      // copia propiedades útiles si existen
      ["origen", "destino", "promedio_velocidad", "pendiente_media"].forEach(k => {
        if (segmento?.[k] !== undefined) props[k] = segmento[k];
      });

      features.push({
        type: "Feature",
        properties: props,
        geometry: {
          type: "LineString",
          coordinates: processedCoords,
        },
      });
    });
  });

  return { type: "FeatureCollection", features };
}

function sanitizeFeatureCollection(fc) {
  // Recorre features y fuerza LineString a 2D (si no --keep3d).
  const out = { type: "FeatureCollection", features: [] };
  for (const feat of fc.features || []) {
    if (!feat || typeof feat !== "object") continue;
    const geom = feat.geometry || {};
    if (geom.type === "LineString") {
      const coords = Array.isArray(geom.coordinates) ? geom.coordinates : [];
      const processedCoords = maybe2D(coords);
      if (processedCoords.length < 2) continue;
      out.features.push({
        type: "Feature",
        properties: feat.properties || {},
        geometry: { type: "LineString", coordinates: processedCoords },
      });
    } else {
      // opcional: si quieres pasar otros tipos tal cual (Point/Polygon), coméntalo o adáptalo
      // out.features.push(feat);
      // En este proyecto solo esperamos LineString, así que se omiten otros tipos.
      continue;
    }
  }
  return out;
}

// ----------------- main -------------------
try {
  console.log(`Leyendo: ${path.resolve(inputPath)}`);
  const src = readJSON(inputPath);

  let fc;
  if (isFeatureCollection(src)) {
    console.log("Detectado FeatureCollection → saneando a 2D...");
    fc = sanitizeFeatureCollection(src);
  } else if (Array.isArray(src.bikes)) {
    console.log("Detectado formato bikes → convirtiendo a FeatureCollection...");
    fc = fromBikesToFC(src);
  } else {
    throw new Error("No se reconoce el formato de entrada. Use un GeoJSON FeatureCollection o un JSON con 'bikes'.");
  }

  writeJSON(outputPath, fc);
  console.log(`Archivo convertido: ${path.resolve(outputPath)}`);
  console.log(`Features: ${fc.features.length}`);
  if (!keep3d) console.log("   Coordenadas: forzadas a 2D ✔");
  else console.log("   Coordenadas: se han mantenido como 3D (si venían así) ⚠");

} catch (err) {
  console.error("Error:", err.message);
  process.exit(1);
}