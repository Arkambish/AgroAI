"use client";

import * as React from "react";
import { PlotlyChart } from "./plotly-chart";
import type { ModelComparisonRow } from "@/lib/types";
import { TARGET_R2 } from "@/lib/constants";

const ML_NAMES = new Set(["RandomForest", "XGBoost", "SVR"]);
const HYBRID_NAME = "CNN_LSTM_Hybrid";

function colourFor(name: string): string {
  if (ML_NAMES.has(name)) return "#1e88e5"; // ML — blue
  if (name === HYBRID_NAME) return "#e53935"; // Hybrid — red
  return "#fb8c00"; // DL — orange
}

interface ModelComparisonChartProps {
  rows: ModelComparisonRow[];
  height?: number | string;
}

export function ModelComparisonChart({ rows, height = 360 }: ModelComparisonChartProps) {
  const sorted = [...rows].sort((a, b) => b.R2 - a.R2);
  const x = sorted.map((r) => r.Model);
  const colours = sorted.map((r) => colourFor(r.Model));

  const data = [
    {
      type: "bar" as const,
      name: "RMSE (MT/Ha)",
      x,
      y: sorted.map((r) => r.RMSE),
      yaxis: "y1",
      marker: { color: colours, opacity: 0.9 },
      hovertemplate: "%{x}<br>RMSE = %{y:.3f}<extra></extra>",
    },
    {
      type: "scatter" as const,
      mode: "lines+markers" as const,
      name: "R²",
      x,
      y: sorted.map((r) => r.R2),
      yaxis: "y2",
      line: { color: "#10b981", width: 2 },
      marker: { color: "#10b981", size: 9 },
      hovertemplate: "%{x}<br>R² = %{y:.3f}<extra></extra>",
    },
  ];

  return (
    <div style={{ height }}>
      <PlotlyChart
        data={data}
        layout={{
          margin: { l: 60, r: 60, t: 30, b: 80 },
          showlegend: true,
          legend: { orientation: "h", y: -0.32 },
          xaxis: { tickangle: -25 },
          yaxis: { title: { text: "RMSE (MT/Ha)" }, rangemode: "tozero" },
          yaxis2: {
            title: { text: "R²" },
            overlaying: "y",
            side: "right",
            range: [Math.min(0, ...sorted.map((r) => r.R2)) - 0.05, 1.0],
          },
          shapes: [
            {
              type: "line",
              xref: "paper",
              yref: "y2",
              x0: 0,
              x1: 1,
              y0: TARGET_R2,
              y1: TARGET_R2,
              line: { color: "#dc2626", width: 1.5, dash: "dash" },
            },
          ],
          annotations: [
            {
              xref: "paper",
              yref: "y2",
              x: 0.99,
              y: TARGET_R2,
              text: `Target R² = ${TARGET_R2}`,
              showarrow: false,
              xanchor: "right",
              yanchor: "bottom",
              font: { color: "#dc2626", size: 10 },
            },
          ],
        }}
      />
    </div>
  );
}
