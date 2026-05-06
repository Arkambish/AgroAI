"use client";

// Wrapper around react-plotly.js that registers plotly.js-dist-min lazily and only
// renders client-side. Avoids "window is not defined" SSR errors and keeps the
// initial bundle small.

import * as React from "react";
import dynamic from "next/dynamic";
import type { Data, Layout, Config } from "plotly.js-dist-min";

const Plot = dynamic(
  async () => {
    const PlotlyMod = (await import("plotly.js-dist-min")).default;
    const factory = (await import("react-plotly.js/factory")).default;
    return factory(PlotlyMod);
  },
  { ssr: false, loading: () => <div className="h-full w-full animate-pulse rounded bg-slate-100 dark:bg-slate-800" /> },
);

export interface PlotlyChartProps {
  data: Data[];
  layout?: Partial<Layout>;
  config?: Partial<Config>;
  className?: string;
  style?: React.CSSProperties;
}

const baseLayout: Partial<Layout> = {
  margin: { l: 50, r: 20, t: 30, b: 50 },
  paper_bgcolor: "rgba(0,0,0,0)",
  plot_bgcolor: "rgba(0,0,0,0)",
  font: { family: "var(--font-geist-sans), system-ui, sans-serif", size: 12 },
  hoverlabel: { bgcolor: "white" },
};

const baseConfig: Partial<Config> = {
  displaylogo: false,
  responsive: true,
};

export function PlotlyChart({ data, layout, config, className, style }: PlotlyChartProps) {
  return (
    <Plot
      data={data}
      layout={{ ...baseLayout, ...layout }}
      config={{ ...baseConfig, ...config }}
      className={className}
      style={{ width: "100%", height: "100%", ...style }}
      useResizeHandler
    />
  );
}
