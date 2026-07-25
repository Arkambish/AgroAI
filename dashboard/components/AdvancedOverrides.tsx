"use client";

import { SlidersHorizontal, RotateCcw } from "lucide-react";
import { useTranslations } from "next-intl";
import { clsx } from "clsx";
import { EDITABLE_FEATURES, type FeatureMeta } from "@/lib/features";
import type { ContextResponse } from "@/lib/api";

interface Props {
  enabled: boolean;
  onToggle: (enabled: boolean) => void;
  context: ContextResponse | null;
  overrides: Record<string, number>;
  errors: Record<string, string>;
  onOverrideChange: (name: string, raw: string) => void;
  onReset: () => void;
}

/** Validate one override against its metadata range. Returns an i18n key + params. */
export function validateOverride(
  meta: FeatureMeta,
  value: number
): { key: string; min: number; max: number } | null {
  const min = meta.min ?? -Infinity;
  const max = meta.max ?? Infinity;
  if (!Number.isFinite(value) || value < min || value > max) {
    return { key: "outOfRange", min, max };
  }
  return null;
}

/**
 * Tier C — expert override.
 *
 * Collapsed by default (progressive disclosure). An extension officer with a
 * soil test or a fresh NDVI reading can correct any auto-filled value; a farmer
 * never has to open it.
 */
export default function AdvancedOverrides({
  enabled,
  onToggle,
  context,
  overrides,
  errors,
  onOverrideChange,
  onReset,
}: Props) {
  const t = useTranslations("form");
  const tf = useTranslations("features");

  const overrideCount = Object.keys(overrides).length;

  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center space-x-2">
          <SlidersHorizontal className="text-slate-500" size={20} />
          <div>
            <h3 className="text-lg font-bold text-slate-900">
              {t("advancedTitle")}
            </h3>
            <p className="text-xs text-slate-500">{t("advancedHelp")}</p>
          </div>
        </div>

        <label className="flex cursor-pointer items-center space-x-2">
          <span className="text-xs font-semibold text-slate-600">
            {enabled ? t("on") : t("off")}
          </span>
          <input
            type="checkbox"
            role="switch"
            checked={enabled}
            onChange={(e) => onToggle(e.target.checked)}
            className="peer sr-only"
          />
          <span className="relative h-6 w-11 rounded-full bg-slate-200 transition-colors peer-checked:bg-emerald-600 after:absolute after:left-0.5 after:top-0.5 after:h-5 after:w-5 after:rounded-full after:bg-white after:shadow after:transition-transform peer-checked:after:translate-x-5" />
        </label>
      </div>

      {enabled && (
        <>
          <div className="flex items-center justify-between border-t pt-4">
            <p className="text-xs text-slate-500">
              {overrideCount > 0
                ? t("overrideCount", { count: overrideCount })
                : t("noOverrides")}
            </p>
            <button
              type="button"
              onClick={onReset}
              disabled={overrideCount === 0}
              className="inline-flex items-center space-x-1.5 rounded-lg px-2.5 py-1.5 text-xs font-semibold text-slate-600 transition-colors hover:bg-slate-100 disabled:opacity-40"
            >
              <RotateCcw size={13} />
              <span>{t("resetDefaults")}</span>
            </button>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            {EDITABLE_FEATURES.map((meta) => {
              const contextValue = context?.[meta.name] as number | undefined;
              const current =
                overrides[meta.name] ??
                (contextValue !== undefined
                  ? Number(contextValue.toFixed(meta.decimals))
                  : "");
              const error = errors[meta.name];

              return (
                <div key={meta.name} className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <label
                      htmlFor={meta.name}
                      className="text-xs font-bold text-slate-700"
                    >
                      {tf(meta.labelKey)}
                    </label>
                    <span className="text-[11px] text-slate-400">
                      {meta.min} – {meta.max}
                      {meta.unit ? ` ${meta.unit}` : ""}
                    </span>
                  </div>
                  <input
                    id={meta.name}
                    name={meta.name}
                    type="number"
                    inputMode="decimal"
                    min={meta.min}
                    max={meta.max}
                    step={meta.step}
                    value={current}
                    aria-invalid={Boolean(error)}
                    onChange={(e) => onOverrideChange(meta.name, e.target.value)}
                    className={clsx(
                      "w-full rounded-xl border bg-slate-50 px-3.5 py-2.5 text-sm font-semibold text-slate-800 outline-none focus:bg-white focus:ring-2",
                      error
                        ? "border-red-300 focus:ring-red-500"
                        : "border-slate-200 focus:ring-emerald-500"
                    )}
                  />
                  {error && (
                    <p className="text-[11px] font-medium text-red-600">
                      {error}
                    </p>
                  )}
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}
