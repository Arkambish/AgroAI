"use client";

import * as React from "react";
import dynamic from "next/dynamic";
import type { Feature, FeatureCollection, Geometry } from "geojson";
import "leaflet/dist/leaflet.css";
import { useEffect } from "react";

import { formatNumber } from "@/lib/utils";
import { getYieldColor, YIELD_CATEGORIES } from "@/lib/api";

const MapContainer = dynamic(
  () => import("react-leaflet").then((m) => m.MapContainer),
  { ssr: false }
);

const TileLayer = dynamic(
  () => import("react-leaflet").then((m) => m.TileLayer),
  { ssr: false }
);

const GeoJSON = dynamic(
  () => import("react-leaflet").then((m) => m.GeoJSON),
  { ssr: false }
);

const MapResizeHandler = dynamic(() => import("./MapResizeHandler"), {
  ssr: false,
});

const GEOJSON_URL = "/sri-lanka-target-districts-only.geojson";

// Floor so the map stays usable when it isn't being stretched to match a
// taller sibling (e.g. stacked single-column mobile layout, where there's no
// row to stretch against).
const MIN_MAP_HEIGHT = "min-h-[420px]";

const ALLOWED_TARGET_KEYS = [
  "matale",
  "anuradhapura",
  "polonnaruwa",
  "kurunegala",
];

interface Props {
  predictions?: Record<string, number>;
  /** Defaults to filling the parent's height (see MIN_MAP_HEIGHT for the
   * floor used when there's no stretched row to fill, e.g. mobile). Pass a
   * fixed number/string only when the caller actually wants that instead. */
  height?: number | string;
  onSelectDistrict?: (districtName: string) => void;
  selectedDistrict?: string | null;
}

function normalizeDistrictKey(value?: string) {
  return value?.toLowerCase().replace(/[^a-z0-9]/g, "") || "";
}

function getFeatureDistrictName(feature?: Feature<Geometry, any>) {
  if (!feature?.properties) return "";

  const raw =
    feature.properties.shapeName ||
    feature.properties.name ||
    feature.properties.district ||
    feature.properties.District ||
    "";

  // Strip trailing "District" suffix if present e.g. "Matale District" -> "Matale"
  return raw.replace(/\s+district$/i, "").trim();
}

export default function DistrictMap({
  predictions = {},
  height,
  onSelectDistrict,
  selectedDistrict,
}: Props) {
  const [geo, setGeo] = React.useState<FeatureCollection | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  const normalizedPredictions = React.useMemo(() => {
    const normalized: Record<string, number> = {};

    Object.entries(predictions).forEach(([key, value]) => {
      const normalizedKey = normalizeDistrictKey(key);
      if (normalizedKey) {
        normalized[normalizedKey] = value;
      }
    });

    return normalized;
  }, [predictions]);

  // Filter GeoJSON to highlight ONLY the 4 target districts
  const filteredGeoData = React.useMemo(() => {
    if (!geo) return null;

    const filteredFeatures = geo.features.filter((feature) => {
      const name = getFeatureDistrictName(feature);
      const key = normalizeDistrictKey(name);
      return ALLOWED_TARGET_KEYS.includes(key);
    });

    return {
      ...geo,
      features: filteredFeatures,
    };
  }, [geo]);

  // Safe GeoJSON loading
  useEffect(() => {
    let ignore = false;

    fetch(GEOJSON_URL)
      .then((r) => {
        if (!r.ok) throw new Error("GeoJSON failed to load");
        return r.json();
      })
      .then((data) => {
        if (!ignore) {
          setGeo(data);
          setLoading(false);
        }
      })
      .catch((e) => {
        if (!ignore) {
          setError(String(e));
          setLoading(false);
        }
      });

    return () => {
      ignore = true;
    };
  }, []);

  const style = React.useCallback(
    (feature?: Feature<Geometry, any>) => {
      const name = getFeatureDistrictName(feature);
      const normalizedName = normalizeDistrictKey(name);
      const isTarget = ALLOWED_TARGET_KEYS.includes(normalizedName);

      if (!isTarget) {
        return {
          color: "transparent",
          weight: 0,
          fillColor: "transparent",
          fillOpacity: 0,
        };
      }

      const value = normalizedPredictions[normalizedName];
      const isSelected =
        selectedDistrict &&
        normalizeDistrictKey(selectedDistrict) === normalizedName;

      return {
        color: isSelected ? "#0f172a" : "#334155",
        weight: isSelected ? 3 : 1.5,
        fillColor: getYieldColor(value),
        fillOpacity: isSelected ? 0.9 : 0.75,
      };
    },
    [normalizedPredictions, selectedDistrict]
  );

  const onEachFeature = React.useCallback(
    (feature: Feature<any>, layer: any) => {
      const name = getFeatureDistrictName(feature);
      const normalizedName = normalizeDistrictKey(name);

      if (!ALLOWED_TARGET_KEYS.includes(normalizedName)) {
        return;
      }

      const value = normalizedPredictions[normalizedName];

      layer.bindTooltip(
        `<div class="font-sans text-xs font-semibold px-1 py-0.5">
          <div class="text-sm font-bold text-slate-900">${name}</div>
          <div class="text-emerald-700 font-extrabold mt-0.5">${
            value !== undefined
              ? `${formatNumber(value, 2)} MT/Ha`
              : "No prediction"
          }</div>
        </div>`,
        { sticky: true, className: "rounded-lg shadow-md border-0 bg-white" }
      );

      layer.on("click", () => {
        if (name && onSelectDistrict) {
          onSelectDistrict(name);
        }
      });
    },
    [normalizedPredictions, onSelectDistrict]
  );

  if (error) {
    return (
      <div
        className={`h-full ${MIN_MAP_HEIGHT} grid place-items-center rounded-2xl border border-red-200 bg-red-50 text-sm text-red-600`}
      >
        Map failed to load: {error}
      </div>
    );
  }

  if (loading) {
    return (
      <div
        className={`h-full ${MIN_MAP_HEIGHT} grid place-items-center rounded-2xl border bg-slate-50 text-sm text-slate-500`}
      >
        Loading target district map...
      </div>
    );
  }

  return (
    <div
      // isolate: Leaflet's own CSS gives its panes/controls z-index up to
      // 1000 (leaflet/dist/leaflet.css) with no stacking context of their
      // own, so without this they compete directly against the app shell
      // (e.g. Navbar.tsx's sticky z-50) instead of staying scoped to the
      // map — isolate confines all of Leaflet's z-index values inside this
      // element, so the whole map can never render above anything outside it.
      //
      // Height: fills the parent (matching the left column via the grid's
      // default row-stretch in page.tsx) rather than a fixed pixel value, so
      // there's no leftover gap below the map. MIN_MAP_HEIGHT is the floor
      // for layouts with no row to stretch against (e.g. stacked mobile). A
      // caller-supplied `height` still wins when explicitly passed.
      className={`relative isolate overflow-hidden rounded-3xl border border-slate-200 shadow-xl ${
        height === undefined ? `h-full ${MIN_MAP_HEIGHT}` : ""
      }`}
      style={height !== undefined ? { height } : undefined}
    >
      <MapContainer
        key="district-map"
        center={[8.0, 80.6]}
        zoom={7.2}
        scrollWheelZoom={false}
        style={{ height: "100%", width: "100%" }}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution="© OpenStreetMap"
        />

        {filteredGeoData && (
          <GeoJSON
            data={filteredGeoData}
            style={style}
            onEachFeature={onEachFeature}
          />
        )}

        <MapResizeHandler />
      </MapContainer>

      {/* Map Legend */}
      <div className="absolute bottom-4 right-4 z-1000 rounded-2xl bg-white/95 p-3 shadow-lg backdrop-blur border border-slate-100">
        <p className="text-xs font-bold text-slate-700 mb-2">
          Yield Scale (MT/Ha)
        </p>
        <div className="flex flex-col space-y-1.5 text-[11px]">
          {YIELD_CATEGORIES.map((cat) => (
            <div key={cat.label} className="flex items-center space-x-2">
              <span
                className="h-3 w-3 rounded-full shadow-sm"
                style={{ backgroundColor: cat.color }}
              />
              <span className="font-semibold text-slate-700">{cat.label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
