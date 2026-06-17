"use client";

import * as React from "react";
import dynamic from "next/dynamic";
import type { Feature, FeatureCollection, Geometry } from "geojson";
import "leaflet/dist/leaflet.css";
import { useEffect } from "react";

import { clamp, formatNumber } from "@/lib/utils";

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

const GEOJSON_URL = "/sri-lanka-target-districts-only.geojson";

interface Props {
  predictions?: Record<string, number>;
  height?: number | string;
}

// 🎨 color scale
function getColor(v?: number) {
  if (v === undefined) return "#e2e8f0";

  const t = clamp((v - 4) / 20, 0, 1);

  const colors = [
    "#440154",
    "#3b528b",
    "#21918c",
    "#5ec962",
    "#fde725",
  ];

  const i = Math.floor(t * (colors.length - 1));
  return colors[i];
}

export default function DistrictMap({
  predictions = {},
  height = 420,
}: Props) {

  const setDistrict = (name: string) => {
    console.log("Selected district:", name);
  };

  const [geo, setGeo] = React.useState<FeatureCollection | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  // ✅ SAFE GEO LOAD
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
      const name = feature?.properties?.name;
      const value = name ? predictions[name] : undefined;

      return {
        color: "#334155",
        weight: 1,
        fillColor: getColor(value),
        fillOpacity: value !== undefined ? 0.75 : 0.3,
      };
    },
    [predictions]
  );

  const onEachFeature = React.useCallback(
    (feature: Feature<any>, layer: any) => {
      const name = feature.properties?.name;
      const value = predictions[name];

      layer.bindTooltip(
        value !== undefined
          ? `<b>${name}</b><br/>${formatNumber(value, 2)} MT/Ha`
          : `<b>${name}</b><br/>No prediction`
      );

      layer.on("click", () => {
        if (name) setDistrict(name);
      });
    },
    [predictions]
  );

  if (error) {
    return (
      <div className="h-[420px] grid place-items-center text-sm text-red-500">
        Map failed to load: {error}
      </div>
    );
  }

  if (loading) {
    return (
      <div className="h-[420px] grid place-items-center text-sm text-slate-500">
        Loading map...
      </div>
    );
  }

  return (
    <div className="relative" style={{ height }}>
      <MapContainer
        key="district-map"   // 🔥 CRITICAL FIX
        center={[7.9, 80.7]}
        zoom={7}
        scrollWheelZoom={false}
        style={{ height: "100%", width: "100%" }}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution="© OpenStreetMap"
        />

        {geo && (
          <GeoJSON data={geo} style={style} onEachFeature={onEachFeature} />
        )}
      </MapContainer>

      <div className="absolute bottom-3 right-3 bg-white/90 p-2 text-xs rounded shadow">
        Yield Map (MT/Ha)
      </div>
    </div>
  );
}