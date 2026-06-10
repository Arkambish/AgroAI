"use client";

import { useState } from "react";
import { ComposableMap, Geographies, Geography } from "react-simple-maps";

interface DistrictMapProps {
  predictions?: Record<string, number>;
}

const geoUrl =
  "https://raw.githubusercontent.com/deldersveld/topojson/master/countries/sri-lanka/sri-lanka-districts.json";

// Normalize keys to avoid mismatch between GeoJSON and ML output
const normalize = (str: string) => str.toLowerCase().replace(/\s+/g, "").trim();

export default function DistrictMap({ predictions = {} }: DistrictMapProps) {
  const [tooltip, setTooltip] = useState<{
    name: string;
    val: number;
  } | null>(null);

  // Color based on yield value
  const getYieldColor = (val: number) => {
    if (val > 15) return "#059669";
    if (val > 10) return "#34d399";
    if (val > 0) return "#a7f3d0";
    return "#e2e8f0";
  };

  return (
    <div className="rounded-2xl border bg-white p-6 shadow-md dark:bg-slate-900">
      {/* Header */}
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-lg font-bold text-slate-900 dark:text-white">
          Yield by District
        </h3>

        {tooltip && (
          <span className="rounded-lg bg-slate-100 px-3 py-1 text-sm text-slate-700 dark:bg-slate-800 dark:text-slate-200">
            <strong>{tooltip.name}</strong>:{" "}
            {tooltip.val > 0 ? `${tooltip.val.toFixed(1)} t/ha` : "No data"}
          </span>
        )}
      </div>

      {/* Map */}
      <div className="h-[420px] w-full overflow-hidden">
        <ComposableMap
          projection="geoMercator"
          projectionConfig={{
            center: [80.7, 7.9],
            scale: 2800,
          }}
          style={{ width: "100%", height: "100%" }}
        >
          <Geographies geography={geoUrl}>
            {({ geographies }: { geographies: any[] }) =>
              geographies.map((geo: any) => {
                const rawName = geo.properties.NAME_2 as string;
                const key = normalize(rawName);

                const val = predictions[key] ?? 0;

                return (
                  <Geography
                    key={geo.rsmKey}
                    geography={geo}
                    fill={getYieldColor(val)}
                    stroke="#ffffff"
                    strokeWidth={0.5}
                    style={{
                      default: { outline: "none" },
                      hover: {
                        outline: "none",
                        opacity: 0.8,
                        cursor: "pointer",
                      },
                      pressed: { outline: "none" },
                    }}
                    onMouseEnter={() =>
                      setTooltip({
                        name: rawName,
                        val,
                      })
                    }
                    onMouseLeave={() => setTooltip(null)}
                  />
                );
              })
            }
          </Geographies>
        </ComposableMap>
      </div>

      {/* Legend */}
      <div className="mt-4 flex flex-wrap items-center gap-4 text-xs text-slate-500">
        <span className="font-medium">Yield (t/ha):</span>

        {[
          { color: "#059669", label: "> 15" },
          { color: "#34d399", label: "10 – 15" },
          { color: "#a7f3d0", label: "1 – 10" },
          { color: "#e2e8f0", label: "No data" },
        ].map(({ color, label }) => (
          <span key={label} className="flex items-center gap-1.5">
            <span
              className="inline-block h-3 w-3 rounded-sm"
              style={{ backgroundColor: color }}
            />
            {label}
          </span>
        ))}
      </div>
    </div>
  );
}
