"use client";

import * as React from "react";
import { PlotlyChart } from "./plotly-chart";
import type { District } from "@/lib/types";
import { DISTRICTS } from "@/lib/constants";

export interface SeasonalRow {
  district: District;
  yala?: number;
  maha?: number;
}

interface SeasonalComparisonChartProps {
  rows: SeasonalRow[];
  height?: number | string;
}

export function SeasonalComparisonChart({ rows, height = 320 }: SeasonalComparisonChartProps) {
  const ordered = DISTRICTS.map((d) => rows.find((r) => r.district === d) ?? { district: d });

  const numOrNull = (n: number | undefined): number | null =>
    typeof n === "number" && Number.isFinite(n) ? n : null;

  const data = [
    {
      type: "bar" as const,
      name: "Yala",
      x: ordered.map((r) => r.district),
      y: ordered.map((r) => numOrNull(r.yala)),
      marker: { color: "#ffb347" },
      hovertemplate: "%{x} · Yala<br>%{y:.2f} MT/Ha<extra></extra>",
    },
    {
      type: "bar" as const,
      name: "Maha",
      x: ordered.map((r) => r.district),
      y: ordered.map((r) => numOrNull(r.maha)),
      marker: { color: "#87ceeb" },
      hovertemplate: "%{x} · Maha<br>%{y:.2f} MT/Ha<extra></extra>",
    },
  ];

  return (
    <div style={{ height }}>
      <PlotlyChart
        data={data}
        layout={{
          barmode: "group",
          showlegend: true,
          legend: { orientation: "h", y: -0.18 },
          xaxis: { title: { text: "" } },
          yaxis: { title: { text: "Predicted yield (MT/Ha)" }, rangemode: "tozero" },
        }}
      />
    </div>
  );
}
