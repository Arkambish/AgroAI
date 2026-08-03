"use client";

import { Info, RotateCcw, SlidersHorizontal } from "lucide-react";
import { useTranslations } from "next-intl";
import { clsx } from "clsx";
import {
  FEATURE_META_BY_NAME,
  formatFeatureValue,
  type FeatureMeta,
} from "@/lib/features";
import type { ContextResponse } from "@/lib/api";

interface Props {
  enabled: boolean;
  onToggle: (enabled: boolean) => void;
  context: ContextResponse | null;
  overrides: Record<string, number>;
  /** Fields the officer actually typed into, vs. auto-filled from `context` */
  touched: Record<string, boolean>;
  errors: Record<string, string>;
  onOverrideChange: (name: string, raw: string) => void;
  onOverrideBlur: (name: string) => void;
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

interface Category {
  key: string;
  labelKey: string;
  features: string[];
}

// Grouped the way an extension officer thinks about a field visit, not by
// the model's internal weather/satellite/soil taxonomy (see lib/features.ts)
// — and limited to the 10 fields a human can actually go measure or read off
// a soil test / satellite readout, not all 32 model inputs.
const CATEGORIES: Category[] = [
  {
    key: "climate",
    labelKey: "categoryClimate",
    features: [
      "season_avg_temp",
      "season_total_rainfall",
      "season_avg_humidity",
      "season_avg_solar_rad",
    ],
  },
  {
    key: "remoteSensing",
    labelKey: "categoryRemoteSensing",
    features: ["season_mean_ndvi", "season_mean_evi"],
  },
  {
    key: "soil",
    labelKey: "categorySoil",
    features: ["soil_ph", "organic_carbon", "clay_pct", "sand_pct"],
  },
];

// Only the fields a farmer/officer wouldn't recognize by name get an
// explanatory tooltip — unit-bearing weather fields are self-explanatory.
const TOOLTIP_KEYS: Record<string, string> = {
  season_mean_ndvi: "tooltipNdvi",
  season_mean_evi: "tooltipEvi",
  soil_ph: "tooltipPh",
  organic_carbon: "tooltipOrganicCarbon",
};

function InfoTooltip({ text }: { text: string }) {
  return (
    <button
      type="button"
      aria-label={text}
      className="group relative inline-flex text-slate-400 outline-none hover:text-slate-600 focus-visible:text-slate-600"
    >
      <Info size={13} />
      <span className="pointer-events-none absolute bottom-full left-1/2 z-10 mb-1.5 w-48 -translate-x-1/2 rounded-lg bg-slate-900 px-2.5 py-1.5 text-[11px] font-medium leading-snug text-white opacity-0 shadow-lg transition-opacity group-hover:opacity-100 group-focus-visible:opacity-100">
        {text}
      </span>
    </button>
  );
}

/**
 * Advanced Agricultural Inputs (Officer Mode) — Tier C, expert override.
 *
 * Collapsed by default (progressive disclosure). The moment it's switched
 * on, every field is pre-filled with the system-estimated value for the
 * current district/season (see the seeding effect in predict/page.tsx) so
 * an extension officer edits real numbers, not a blank form; a farmer never
 * has to open it at all.
 */
export default function AdvancedOverrides({
  enabled,
  onToggle,
  context,
  overrides,
  touched,
  errors,
  onOverrideChange,
  onOverrideBlur,
  onReset,
}: Props) {
  const t = useTranslations("advanced");
  const tf = useTranslations("features");

  const overrideCount = Object.keys(overrides).length;

  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-start space-x-2">
          <SlidersHorizontal className="mt-0.5 shrink-0 text-slate-500" size={20} />
          <div>
            <h3 className="text-lg font-bold text-slate-900">{t("title")}</h3>
            <p className="text-xs text-slate-500">{t("description")}</p>
          </div>
        </div>

        {/* suppressHydrationWarning: autofill/password-manager browser
            extensions stamp fdprocessedid="..." onto every form control they
            scan post-mount, which React otherwise reports as a mismatch even
            though nothing here renders differently server vs. client — see
            LanguageSwitcher.tsx/Navbar.tsx for the same, already-confirmed
            case. */}
        <label className="flex cursor-pointer items-center space-x-2">
          <span className="text-xs font-semibold text-slate-600">
            {t("toggleShow")} · {enabled ? t("on") : t("off")}
          </span>
          <input
            type="checkbox"
            role="switch"
            checked={enabled}
            onChange={(e) => onToggle(e.target.checked)}
            className="peer sr-only"
            suppressHydrationWarning
          />
          <span className="relative h-6 w-11 rounded-full bg-slate-200 transition-colors peer-checked:bg-emerald-600 after:absolute after:left-0.5 after:top-0.5 after:h-5 after:w-5 after:rounded-full after:bg-white after:shadow after:transition-transform peer-checked:after:translate-x-5" />
        </label>
      </div>

      {enabled && (
        <div className="space-y-5 border-t pt-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
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

          {CATEGORIES.map((category) => (
            <div key={category.key} className="space-y-3">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                {t(category.labelKey)}
              </h4>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                {category.features.map((name) => {
                  const meta = FEATURE_META_BY_NAME[name];
                  if (!meta) return null;
                  const contextValue = context?.[name] as number | undefined;
                  const override = overrides[name];
                  const isTouched = Boolean(touched[name]);
                  const error = errors[name];
                  const tooltipKey = TOOLTIP_KEYS[name];

                  return (
                    <div key={name} className="space-y-1.5">
                      <div className="flex items-center justify-between gap-2">
                        <span className="inline-flex items-center gap-1 text-xs font-bold text-slate-700">
                          <label htmlFor={name}>{tf(meta.labelKey)}</label>
                          {tooltipKey && <InfoTooltip text={t(tooltipKey)} />}
                        </span>
                        <span className="text-[11px] text-slate-400">
                          {meta.min} – {meta.max}
                          {meta.unit ? ` ${meta.unit}` : ""}
                        </span>
                      </div>
                      <input
                        id={name}
                        name={name}
                        type="number"
                        inputMode="decimal"
                        min={meta.min}
                        max={meta.max}
                        step={meta.step}
                        value={override ?? ""}
                        placeholder={
                          contextValue !== undefined
                            ? formatFeatureValue(contextValue, meta)
                            : undefined
                        }
                        aria-invalid={Boolean(error)}
                        onChange={(e) => onOverrideChange(name, e.target.value)}
                        onBlur={() => onOverrideBlur(name)}
                        className={clsx(
                          "w-full rounded-xl border bg-slate-50 px-3.5 py-2.5 text-sm font-semibold text-slate-800 outline-none placeholder:font-normal placeholder:text-slate-400 focus:bg-white focus:ring-2",
                          error
                            ? "border-red-300 focus:ring-red-500"
                            : "border-slate-200 focus:ring-emerald-500"
                        )}
                        suppressHydrationWarning
                      />
                      {error ? (
                        <p className="text-[11px] font-medium text-red-600">
                          {error}
                        </p>
                      ) : (
                        <p
                          className={clsx(
                            "text-[11px]",
                            isTouched ? "font-medium text-emerald-600" : "text-slate-400"
                          )}
                        >
                          {isTouched
                            ? t("yourValue")
                            : override !== undefined
                              ? t("systemEstimate")
                              : t("noEstimate")}
                        </p>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
