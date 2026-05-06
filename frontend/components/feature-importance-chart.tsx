"use client";

import * as React from "react";
import { PlotlyChart } from "./plotly-chart";
import type { FeatureImportanceEntry } from "@/lib/types";
import { FEATURE_META } from "@/lib/constants";

interface FeatureImportanceChartProps {
  entries: FeatureImportanceEntry[];
  height?: number | string;
}

export function FeatureImportanceChart({ entries, height = 480 }: FeatureImportanceChartProps) {
  // Sort ascending so the highest bars sit on top in horizontal layout.
  const sorted = [...entries].sort((a, b) => a.mean_abs_shap - b.mean_abs_shap);
  const labels = sorted.map((e) => FEATURE_META[e.name]?.label ?? e.name);

  const data = [
    {
      type: "bar" as const,
      orientation: "h" as const,
      x: sorted.map((e) => e.mean_abs_shap),
      y: labels,
      marker: { color: "#10b981" },
      hovertemplate: "%{y}<br>mean |SHAP| = %{x:.4f}<extra></extra>",
    },
  ];

  return (
    <div style={{ height }}>
      <PlotlyChart
        data={data}
        layout={{
          margin: { l: 180, r: 30, t: 20, b: 40 },
          xaxis: { title: { text: "Mean |SHAP value|" } },
          yaxis: { automargin: true },
        }}
      />
    </div>
  );
}
