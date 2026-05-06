"use client";

import * as React from "react";
import dynamic from "next/dynamic";
import type { Feature, FeatureCollection, Geometry } from "geojson";
import { useSelection } from "./selection-context";
import { DISTRICTS, DISTRICT_CENTROIDS } from "@/lib/constants";
import type { District } from "@/lib/types";
import { clamp, formatNumber } from "@/lib/utils";

// All Leaflet primitives must be loaded client-only — Leaflet touches `window`.
const MapContainer = dynamic(() => import("react-leaflet").then((m) => m.MapContainer), { ssr: false });
const TileLayer = dynamic(() => import("react-leaflet").then((m) => m.TileLayer), { ssr: false });
const GeoJSON = dynamic(() => import("react-leaflet").then((m) => m.GeoJSON), { ssr: false });

const GEOJSON_URL = "/sri-lanka-target-districts.geojson";

// Viridis colour stops mapped to predicted yield (MT/Ha). 4..24 covers the
// observed yield range for big onion across Yala/Maha seasons.
function yieldToColor(value: number): string {
  if (!Number.isFinite(value)) return "#cbd5e1";
  const t = clamp((value - 4) / 20, 0, 1);
  // 5-stop viridis-ish gradient.
  const stops = [
    [68, 1, 84],     // dark purple
    [59, 82, 139],   // blue-purple
    [33, 144, 141],  // teal
    [94, 201, 98],   // green
    [253, 231, 37],  // yellow
  ] as const;
  const idx = clamp(Math.floor(t * (stops.length - 1)), 0, stops.length - 2);
  const localT = t * (stops.length - 1) - idx;
  const a = stops[idx];
  const b = stops[idx + 1];
  const r = Math.round(a[0] + (b[0] - a[0]) * localT);
  const g = Math.round(a[1] + (b[1] - a[1]) * localT);
  const bb = Math.round(a[2] + (b[2] - a[2]) * localT);
  return `rgb(${r}, ${g}, ${bb})`;
}

type DistrictPredictions = Partial<Record<District, number>>;

interface DistrictMapProps {
  /** Predicted yield per district (MT/Ha). Districts without predictions get a neutral fill. */
  predictions: DistrictPredictions;
  height?: number | string;
}

export function DistrictMap({ predictions, height = 420 }: DistrictMapProps) {
  const { setDistrict } = useSelection();
  const [geo, setGeo] = React.useState<FeatureCollection | null>(null);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    fetch(GEOJSON_URL)
      .then((r) => (r.ok ? r.json() : Promise.reject(r.statusText)))
      .then(setGeo)
      .catch((e) => setError(String(e)));
  }, []);

  const styleFn = React.useCallback(
    (feature?: Feature<Geometry, { name: District }>) => {
      const name = feature?.properties?.name;
      const yieldValue = name ? predictions[name] : undefined;
      return {
        color: "#1e293b",
        weight: 1.2,
        fillColor: yieldValue !== undefined ? yieldToColor(yieldValue) : "#e2e8f0",
        fillOpacity: 0.7,
      };
    },
    [predictions],
  );

  const onEachFeature = React.useCallback(
    (feature: Feature<Geometry, { name: District }>, layer: { bindTooltip: (s: string, opts?: Record<string, unknown>) => void; on: (e: string, h: () => void) => void }) => {
      const name = feature.properties?.name;
      if (!name) return;
      const v = predictions[name];
      const tooltip =
        v !== undefined
          ? `<b>${name}</b><br/>Predicted yield: ${formatNumber(v, 2)} MT/Ha`
          : `<b>${name}</b><br/>No prediction yet`;
      layer.bindTooltip(tooltip, { sticky: true });
      layer.on("click", () => setDistrict(name));
    },
    [predictions, setDistrict],
  );

  return (
    <div className="relative" style={{ height }}>
      {error ? (
        <div className="grid h-full place-items-center rounded-xl bg-slate-100 text-sm text-slate-500 dark:bg-slate-800 dark:text-slate-400">
          Map unavailable: {error}
        </div>
      ) : (
        <MapContainer
          center={[8.0, 80.6]}
          zoom={7}
          scrollWheelZoom={false}
          style={{ height: "100%", width: "100%" }}
        >
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution='© <a href="https://www.openstreetmap.org/copyright">OSM</a>'
          />
          {geo && (
            <GeoJSON
              data={geo}
              style={styleFn as never}
              onEachFeature={onEachFeature as never}
            />
          )}
        </MapContainer>
      )}
      <Legend />
      <DistrictHints predictions={predictions} />
    </div>
  );
}

function Legend() {
  const stops = [4, 9, 14, 19, 24];
  return (
    <div className="absolute bottom-3 right-3 z-[400] rounded-md bg-white/90 p-2 text-xs shadow dark:bg-slate-900/90">
      <div className="mb-1 font-medium">Yield (MT/Ha)</div>
      <div className="flex items-center gap-1">
        {stops.map((v) => (
          <div key={v} className="flex flex-col items-center">
            <span
              className="block h-3 w-6"
              style={{ background: yieldToColor(v) }}
              aria-hidden
            />
            <span className="text-[10px] text-slate-500 dark:text-slate-400">{v}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function DistrictHints({ predictions }: { predictions: DistrictPredictions }) {
  const missing = DISTRICTS.filter((d) => predictions[d] === undefined);
  if (missing.length === 0) return null;
  return (
    <div className="absolute top-3 left-3 z-[400] max-w-[260px] rounded-md bg-white/90 p-2 text-xs text-slate-600 shadow dark:bg-slate-900/90 dark:text-slate-300">
      Click a district or open <span className="font-medium">Predict</span> to populate the
      map. Centroids: {missing.map((d) => `${d} (${DISTRICT_CENTROIDS[d][0].toFixed(1)}, ${DISTRICT_CENTROIDS[d][1].toFixed(1)})`).join(", ")}
    </div>
  );
}

export { yieldToColor };
