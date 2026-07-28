"use client";

import { useId } from "react";
import clsx from "clsx";

/**
 * One row of the reliability chart — deliberately decoupled from
 * `ExplanationItem` (lib/api.ts) so this component stays a pure renderer.
 * The explain page does the SHAP/ERI aggregation and hands over plain
 * numbers.
 */
export interface ReliabilityBarDatum {
  /** Stable key for the row (matches ExplanationItem.name) */
  name: string;
  /** Already-translated display label */
  label: string;
  /** Signed combined SHAP value — sign drives bar color, same as the simple view */
  value: number;
  /** 0-1, bar length relative to the largest factor (same scale as ExplanationItem.magnitude) */
  magnitude: number;
  /** 0-1 Explanation Reliability Index for this feature. Undefined when the
   * backend response has no per_feature_eri for it (e.g. mock data). */
  eri?: number;
}

interface ReliabilityWaterfallProps {
  /** Top-5 rows, already selected/ordered — same selection as the simple view. */
  items: ReliabilityBarDatum[];
  legendLabel: string;
  /** Shown instead of a percentage when a row has no ERI value. */
  unknownLabel: string;
  className?: string;
}

const clamp01 = (v: number) => Math.min(1, Math.max(0, v));

/**
 * Hand-rolled SVG dual-encoding bar chart: bar length = |SHAP value| (same
 * top-5 magnitudes as the existing bars), while opacity + a diagonal hatch
 * overlay encode ERI — solid/full-opacity for a trustworthy explanation,
 * faded and hatched for one that shouldn't be taken at face value even
 * though the bar itself is long.
 */
export default function ReliabilityWaterfall({
  items,
  legendLabel,
  unknownLabel,
  className,
}: ReliabilityWaterfallProps) {
  // Unique per mount so multiple instances (or hot-reload remounts) never
  // collide on the <pattern> id referenced via url(#...).
  const hatchId = `reliability-hatch-${useId().replace(/[^a-zA-Z0-9]/g, "")}`;

  return (
    <div className={clsx("space-y-4", className)}>
      {/* Shared hatch pattern def, referenced by every bar below via url(#id) —
          defined once so it isn't duplicated per row. */}
      <svg width={0} height={0} className="absolute" aria-hidden="true">
        <defs>
          <pattern
            id={hatchId}
            width="6"
            height="6"
            patternTransform="rotate(45)"
            patternUnits="userSpaceOnUse"
          >
            <rect width="6" height="6" fill="transparent" />
            <line x1="0" y1="0" x2="0" y2="6" stroke="#ffffff" strokeWidth="2" />
          </pattern>
        </defs>
      </svg>

      <div className="space-y-3">
        {items.map((item) => {
          const isPositive = item.value >= 0;
          const barWidthPct = Math.max(3, clamp01(item.magnitude) * 100);
          const hasEri = item.eri !== undefined && Number.isFinite(item.eri);
          const eri = hasEri ? clamp01(item.eri as number) : undefined;

          // High ERI -> solid, full-opacity bar. Low ERI -> faded base fill
          // plus a more visible diagonal hatch overlay on top of it.
          const fillOpacity = eri === undefined ? 0.55 : 0.22 + 0.78 * eri;
          const hatchOpacity = eri === undefined ? 0.35 : (1 - eri) * 0.7;

          return (
            <div key={item.name} className="space-y-1">
              <div className="flex items-center justify-between gap-2 text-sm">
                <span className="truncate font-medium text-slate-700">
                  {item.label}
                </span>
                <span className="shrink-0 font-mono text-[11px] tabular-nums text-slate-400">
                  {hasEri ? `ERI ${Math.round((eri as number) * 100)}%` : unknownLabel}
                </span>
              </div>

              <svg
                viewBox="0 0 100 10"
                width="100%"
                height={12}
                preserveAspectRatio="none"
                role="img"
                aria-label={`${item.label}: ${Math.round(clamp01(item.magnitude) * 100)}% magnitude, ${
                  hasEri
                    ? `${Math.round((eri as number) * 100)}% reliability`
                    : "reliability unknown"
                }`}
              >
                <rect x={0} y={0} width={100} height={10} rx={5} fill="#f1f5f9" />
                <rect
                  x={0}
                  y={0}
                  width={barWidthPct}
                  height={10}
                  rx={5}
                  fill={isPositive ? "#10b981" : "#ef4444"}
                  fillOpacity={fillOpacity}
                />
                {barWidthPct > 0 && (
                  <rect
                    x={0}
                    y={0}
                    width={barWidthPct}
                    height={10}
                    rx={5}
                    fill={`url(#${hatchId})`}
                    opacity={hatchOpacity}
                  />
                )}
              </svg>
            </div>
          );
        })}
      </div>

      <p className="flex items-center gap-2 text-[11px] text-slate-400">
        <svg width={28} height={12} viewBox="0 0 28 12" aria-hidden="true" className="shrink-0">
          <rect x={0} y={1} width={28} height={10} rx={5} fill="#94a3b8" fillOpacity={0.3} />
          <rect x={0} y={1} width={28} height={10} rx={5} fill={`url(#${hatchId})`} opacity={0.6} />
        </svg>
        <span>{legendLabel}</span>
      </p>
    </div>
  );
}
