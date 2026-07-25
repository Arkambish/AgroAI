"use client";

import { useState } from "react";
import { ChevronDown, Database, Satellite } from "lucide-react";
import { useTranslations } from "next-intl";
import { clsx } from "clsx";
import {
  FEATURE_GROUPS,
  SOURCE_STYLES,
  formatFeatureValue,
  type FeatureSource,
} from "@/lib/features";
import type { ContextResponse } from "@/lib/api";

interface Props {
  context: ContextResponse | null;
  /** Populated after a prediction — where each value actually came from */
  featureSources?: Record<string, FeatureSource>;
  /** Populated after a prediction — the values actually fed to the model */
  resolved?: Record<string, number>;
  /** Advanced-mode overrides, shown as user-supplied */
  overrides: Record<string, number>;
  loading: boolean;
  error: string | null;
}

/**
 * Tier B — the ~28 features the system supplies.
 *
 * Read-only by design: these are NASA POWER, MODIS and SoilGrids products that
 * no farmer can measure. Displaying them with their provenance makes the
 * multi-source pipeline visible, which a form of blank number boxes never did.
 */
export default function KnownDataPanel({
  context,
  featureSources,
  resolved,
  overrides,
  loading,
  error,
}: Props) {
  const t = useTranslations("form");
  const tf = useTranslations("features");
  const tg = useTranslations("featureGroups");
  const [open, setOpen] = useState<string | null>("weather");

  const provenance = (() => {
    if (!context) return null;
    if (context.source === "exact") {
      return t("provenanceExact", { year: context.year });
    }
    return t("provenanceAverage", {
      years: context.n_years ?? 0,
      district: context.district,
      season: context.season,
    });
  })();

  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b pb-3">
        <div className="flex items-center space-x-2">
          <Satellite className="text-sky-600" size={20} />
          <h3 className="text-lg font-bold text-slate-900">
            {t("knownSectionTitle")}
          </h3>
        </div>
        {provenance && (
          <span className="rounded-full bg-sky-100 px-2.5 py-0.5 text-xs font-semibold text-sky-800">
            {provenance}
          </span>
        )}
      </div>

      <p className="text-sm text-slate-500">{t("knownSectionHelp")}</p>

      {error && (
        <p className="rounded-xl bg-amber-50 px-4 py-3 text-sm text-amber-800">
          {error}
        </p>
      )}

      <div className="space-y-2">
        {FEATURE_GROUPS.map((group) => {
          const isOpen = open === group.key;
          return (
            <div
              key={group.key}
              className="overflow-hidden rounded-2xl border border-slate-200"
            >
              <button
                type="button"
                aria-expanded={isOpen}
                onClick={() => setOpen(isOpen ? null : group.key)}
                className="flex w-full items-center justify-between bg-slate-50 px-4 py-3 text-left transition-colors hover:bg-slate-100"
              >
                <div className="flex items-center space-x-2.5">
                  <Database size={15} className="text-slate-400" />
                  <span className="text-sm font-bold text-slate-800">
                    {tg(group.labelKey)}
                  </span>
                  <span className="rounded-full bg-white px-2 py-0.5 text-[10px] font-semibold text-slate-500 ring-1 ring-slate-200">
                    {group.sourceBadge}
                  </span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-xs text-slate-400">
                    {group.features.length}
                  </span>
                  <ChevronDown
                    size={16}
                    className={clsx(
                      "text-slate-400 transition-transform",
                      isOpen && "rotate-180"
                    )}
                  />
                </div>
              </button>

              {isOpen && (
                <dl className="divide-y divide-slate-100">
                  {group.features.map((meta) => {
                    const overridden = overrides[meta.name] !== undefined;
                    const source: FeatureSource | undefined = overridden
                      ? "user"
                      : featureSources?.[meta.name];

                    // Show what the model actually used, in priority order:
                    // an unsent override → the last prediction's resolved value
                    // → the area's context value. Otherwise a "You" badge can
                    // sit next to a value the farmer never entered.
                    let value: number | undefined;
                    if (overridden) {
                      value = overrides[meta.name];
                    } else if (resolved?.[meta.name] !== undefined) {
                      value = resolved[meta.name];
                    } else {
                      value = context?.[meta.name] as number | undefined;
                    }
                    const isUserValue = overridden || source === "user";

                    return (
                      <div
                        key={meta.name}
                        className="flex items-center justify-between gap-3 px-4 py-2.5"
                      >
                        <dt className="text-xs text-slate-600">
                          {tf(meta.labelKey)}
                        </dt>
                        <dd className="flex items-center gap-2">
                          {source && (
                            <span
                              className={clsx(
                                "rounded px-1.5 py-0.5 text-[10px] font-semibold",
                                SOURCE_STYLES[source]
                              )}
                            >
                              {t(`source.${source}`)}
                            </span>
                          )}
                          <span
                            className={clsx(
                              "font-mono text-xs font-semibold tabular-nums",
                              isUserValue ? "text-emerald-700" : "text-slate-800"
                            )}
                          >
                            {loading && !context
                              ? "…"
                              : formatFeatureValue(value, meta)}
                          </span>
                        </dd>
                      </div>
                    );
                  })}
                </dl>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
