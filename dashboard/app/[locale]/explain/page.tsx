"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { useTranslations, useLocale } from "next-intl";
import { Brain, ChevronDown, AlertTriangle, RotateCcw } from "lucide-react";
import {
  convertSHAPToExplanation,
  type ExplanationItem,
  type PredictResponse,
} from "@/lib/api";
import { useLocalJSON, resetPrediction, PREDICTION_KEY } from "@/lib/use-local-flag";
import clsx from "clsx";
import { type ReliabilityBarDatum } from "@/components/charts/ReliabilityWaterfall";

export type { ExplanationItem };

// Purely decorative — keyed by the same internal feature names as
// `features.*` in messages/*.json (see featureDisplayKey in lib/api.ts).
// Falls back to a generic chart icon for anything not listed.
const FEATURE_EMOJI: Record<string, string> = {
  rainfall: "🌧️",
  temperature: "🌡️",
  humidity: "💧",
  soil_ph: "🧪",
  soil_moisture: "💦",
  ndvi: "🌿",
  solar_radiation: "☀️",
  evi: "🌱",
  clay: "🟤",
  sand: "🏖️",
  organic_carbon: "🍂",
  drought: "🏜️",
  prev_yield: "🌾",
  temp_x_humidity: "🌡️",
  rainfall_x_ndvi: "🌧️",
  ndvi_x_lst: "🌡️",
  other: "📊",
};

/** 0-1 relative magnitude (already scaled to the largest of the top-5
 * factors) → a plain-language category, so the card shows "High/Medium/Low"
 * instead of a raw SHAP number. */
function effectTier(magnitude: number): "high" | "medium" | "low" {
  if (magnitude >= 0.66) return "high";
  if (magnitude >= 0.33) return "medium";
  return "low";
}

/** Same 4-tier scheme as requested for the per-card reliability readout —
 * distinct from (and more granular than) the 3-tier badge shown next to the
 * page title, which keeps its own existing thresholds/labels. */
function reliabilityTier(eri: number | undefined): {
  emoji: string;
  key: "cardHigh" | "cardGood" | "cardModerate" | "cardLow" | "cardUnknown";
} {
  if (eri === undefined) return { emoji: "⚪", key: "cardUnknown" };
  const pct = eri * 100;
  if (pct >= 90) return { emoji: "🟢", key: "cardHigh" };
  if (pct >= 70) return { emoji: "🟡", key: "cardGood" };
  if (pct >= 50) return { emoji: "🟠", key: "cardModerate" };
  return { emoji: "🔴", key: "cardLow" };
}

export default function ExplainPage() {
  const t = useTranslations("explain");
  const tButton = useTranslations("button");
  const locale = useLocale();
  const router = useRouter();

  const prediction = useLocalJSON<PredictResponse>(PREDICTION_KEY);

  // Same centralized reset used on the Predict tab — clears the shared
  // prediction/SHAP state (this page will fall back to its own
  // "no prediction" placeholder below) and sends the farmer back to the
  // form to start over.
  const handleNewPrediction = () => {
    resetPrediction();
    router.push(`/${locale}/predict`);
  };
  const explanations = useMemo<ExplanationItem[]>(
    () =>
      prediction?.shap_values
        ? convertSHAPToExplanation(prediction.shap_values)
        : [],
    [prediction]
  );

  // Same top-5 selection as the bars above, with a per-row ERI attached: each
  // displayed factor can fold in several raw model features (e.g. NDVI's 3
  // variants), so its reliability is the |SHAP|-weighted average of
  // per_feature_eri across just those raw features — the same weighting the
  // backend uses to roll per-feature ERI up into one prediction-level score.
  const reliabilityItems = useMemo<ReliabilityBarDatum[]>(() => {
    if (!prediction?.shap_values) return [];
    const shapValues = prediction.shap_values;
    const perFeatureEri = prediction.per_feature_eri;

    return explanations.map((item) => {
      const rawFeatures = item.feature.split(", ");
      let weightedEriSum = 0;
      let absShapSum = 0;
      for (const raw of rawFeatures) {
        const absShap = Math.abs(shapValues[raw] ?? 0);
        const eriForRaw = perFeatureEri?.[raw];
        absShapSum += absShap;
        if (eriForRaw !== undefined) {
          weightedEriSum += absShap * eriForRaw;
        }
      }
      return {
        name: item.name,
        label: t(`features.${item.name}`),
        value: item.raw,
        magnitude: item.magnitude,
        eri: absShapSum > 0 ? weightedEriSum / absShapSum : undefined,
      };
    });
  }, [explanations, prediction, t]);

  // Per-card reliability lookup — same values as reliabilityItems, keyed by
  // name for O(1) access while rendering the simple-view cards below.
  const eriByName = useMemo(
    () => new Map(reliabilityItems.map((r) => [r.name, r.eri])),
    [reliabilityItems]
  );

  // Which cards' "Technical details" drawer is open — independent per card,
  // closed by default so the simple view stays uncluttered.
  const [expandedTechnical, setExpandedTechnical] = useState<Set<string>>(
    new Set()
  );
  const toggleTechnical = (name: string) => {
    setExpandedTechnical((prev) => {
      const next = new Set(prev);
      if (next.has(name)) {
        next.delete(name);
      } else {
        next.add(name);
      }
      return next;
    });
  };

  const eriScore = prediction?.eri;
  const eriLevel =
    eriScore === undefined
      ? undefined
      : eriScore < 0.4
        ? "levelLow"
        : eriScore < 0.7
          ? "levelMedium"
          : "levelHigh";

  if (!prediction) {
    return (
      <div className="flex min-h-100 flex-col items-center justify-center space-y-4 text-center">
        <div className="rounded-full bg-slate-100 p-6">
          <Brain size={64} className="text-slate-300" />
        </div>

        <h2 className="text-2xl font-bold text-slate-900">
          {t("noPrediction")}
        </h2>

        <p className="max-w-md text-slate-500">{t("noDescription")}</p>

        <a
          href={`/${locale}/predict`}
          className="rounded-xl bg-primary px-6 py-3 font-bold text-white shadow-lg transition-transform hover:scale-105"
        >
          {t("goPredict")}
        </a>
      </div>
    );
  }

  // The strongest factor drives the key insight — previously the box rendered
  // its heading with no body text at all.
  const top = explanations[0];

  return (
    <div className="space-y-10">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-start">
        <div className="flex flex-col space-y-2">
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">
            {t("title")}
          </h1>

          <p className="text-slate-500">
            {t("subtitle")} — {prediction.predicted_yield_MT_per_Ha} MT/Ha
          </p>

          {/* Overall Explanation Reliability Index for this prediction — see
              src/xai/eri.py. Shown regardless of which view (below) is active. */}
          <span
            className={clsx(
              "inline-flex w-fit items-center rounded-full px-3 py-1 text-xs font-semibold",
              eriLevel === "levelHigh" && "bg-emerald-100 text-emerald-700",
              eriLevel === "levelMedium" && "bg-amber-100 text-amber-700",
              eriLevel === "levelLow" && "bg-red-100 text-red-700",
              eriLevel === undefined && "bg-slate-100 text-slate-500"
            )}
          >
            {eriScore !== undefined && eriLevel
              ? t("reliability.badge", {
                  value: Math.round(eriScore * 100),
                  level: t(`reliability.${eriLevel}`),
                })
              : t("reliability.badgeUnknown")}
          </span>
        </div>

        <button
          type="button"
          onClick={handleNewPrediction}
          className="flex shrink-0 items-center justify-center space-x-2 rounded-2xl border-2 border-slate-200 bg-white px-5 py-3 font-bold text-slate-600 transition-colors hover:border-slate-300 hover:bg-slate-50"
        >
          <RotateCcw size={18} />
          <span>{tButton("newPrediction")}</span>
        </button>
      </div>

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-2">
        <section className="space-y-6">
          <h2 className="text-xl font-bold text-slate-800">
            {t("keyFactors")}
          </h2>

          <div className="grid gap-4">
            {explanations.map((item) => {
              // SHAP contribution is in the model's own units (MT/Ha), so it
              // converts directly to kg/Ha for a number a farmer can picture
              // — used only inside the technical details drawer now.
              const kgPerHa = Math.round(Math.abs(item.raw) * 1000);
              const isPositive = item.impact === "Positive";
              const tier = effectTier(item.magnitude);
              const eri = eriByName.get(item.name);
              const reliability = reliabilityTier(eri);
              const isExpanded = expandedTechnical.has(item.name);

              return (
                <div
                  key={item.name}
                  className="rounded-xl border bg-white p-4 shadow-sm"
                >
                  <div className="flex items-center gap-2">
                    <span className="text-xl" aria-hidden="true">
                      {FEATURE_EMOJI[item.name] ?? FEATURE_EMOJI.other}
                    </span>
                    <p className="font-bold text-slate-900">
                      {t(`features.${item.name}`)}
                    </p>
                  </div>

                  {/* Farmer-facing summary: what happened, how much, how much
                      to trust it — no raw SHAP numbers here (see requirement
                      to move those into "Technical details" below). */}
                  <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-3">
                    <div>
                      <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">
                        {t("impactLabel")}
                      </p>
                      <p
                        className={clsx(
                          "mt-0.5 text-sm font-bold",
                          isPositive ? "text-emerald-600" : "text-red-600"
                        )}
                      >
                        {isPositive
                          ? t("impactPositive")
                          : t("impactNegative")}
                      </p>
                    </div>

                    <div>
                      <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">
                        {t("effectLabel")}
                      </p>
                      <p className="mt-0.5 text-sm font-bold text-slate-800">
                        {t(`effect.${tier}`)}
                      </p>
                    </div>

                    <div>
                      <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">
                        {t("reliability.cardLabel")}
                      </p>
                      <p className="mt-0.5 flex items-center gap-1.5 text-sm font-bold text-slate-800">
                        <span aria-hidden="true">{reliability.emoji}</span>
                        <span>{t(`reliability.${reliability.key}`)}</span>
                      </p>
                      {eri !== undefined && (
                        <p className="text-xs font-semibold text-slate-500">
                          {Math.round(eri * 100)}%
                        </p>
                      )}
                    </div>
                  </div>

                  <button
                    type="button"
                    onClick={() => toggleTechnical(item.name)}
                    aria-expanded={isExpanded}
                    className="mt-3 flex items-center gap-1 border-t border-dashed border-slate-100 pt-3 text-[11px] font-semibold text-slate-400 transition-colors hover:text-slate-600"
                  >
                    <ChevronDown
                      size={12}
                      className={clsx(
                        "transition-transform",
                        isExpanded && "rotate-180"
                      )}
                    />
                    <span>{t("technicalDetails")}</span>
                  </button>

                  {isExpanded && (
                    <div className="mt-2 space-y-3 rounded-lg bg-slate-50 p-3 text-xs text-slate-600">
                      <p>
                        {isPositive
                          ? t("perFactorPositive", {
                              feature: t(`features.${item.name}`),
                              amount: kgPerHa,
                            })
                          : t("perFactorNegative", {
                              feature: t(`features.${item.name}`),
                              amount: kgPerHa,
                            })}
                      </p>

                      {/* Diverging bar: extends right (emerald) from center
                          for a positive contribution, left (red) for
                          negative — the exact SHAP value + visualization
                          this card used to show up-front. */}
                      <div>
                        <div className="flex items-center justify-between text-[11px] text-slate-400">
                          <span>{t("relative")}</span>
                          <span className="font-mono tabular-nums">
                            {item.raw > 0 ? "+" : ""}
                            {item.raw.toFixed(3)}
                          </span>
                        </div>
                        <div className="relative mt-1 h-2 w-full overflow-hidden rounded-full bg-slate-200">
                          <div className="absolute inset-y-0 left-1/2 w-px bg-slate-300" />
                          {isPositive ? (
                            <div
                              className="absolute inset-y-0 left-1/2 rounded-r-full bg-emerald-500"
                              style={{
                                width: `${Math.max(2, item.magnitude * 50).toFixed(1)}%`,
                              }}
                            />
                          ) : (
                            <div
                              className="absolute inset-y-0 right-1/2 rounded-l-full bg-red-500"
                              style={{
                                width: `${Math.max(2, item.magnitude * 50).toFixed(1)}%`,
                              }}
                            />
                          )}
                        </div>
                      </div>

                      {eri !== undefined && (
                        <div className="flex items-center justify-between">
                          <span>{t("reliability.cardLabel")}</span>
                          <span className="font-mono tabular-nums">
                            {(eri * 100).toFixed(1)}%
                          </span>
                        </div>
                      )}

                      <div>
                        <span className="font-semibold text-slate-500">
                          {t("technicalFeatures")}:
                        </span>{" "}
                        <span className="font-mono">{item.feature}</span>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </section>

        <section className="space-y-6">
          <h2 className="text-xl font-bold text-slate-800">{t("summary")}</h2>

          <div className="rounded-xl border bg-white p-6 shadow-sm">
            <p className="text-slate-700">
              {t("basedOn")} <b>{prediction.district}</b> {t("expected")}{" "}
              <b>{prediction.predicted_yield_MT_per_Ha} MT/Ha</b>
            </p>

            <ul className="mt-4 list-disc space-y-1.5 pl-6 text-slate-700">
              {explanations.map((item) => (
                <li key={item.name}>
                  <b>{t(`features.${item.name}`)}</b>{" "}
                  {item.impact === "Positive" ? t("positive") : t("negative")}
                </li>
              ))}
            </ul>

            {top && (
              <div className="mt-6 rounded-xl bg-amber-50 p-4">
                <AlertTriangle className="text-amber-500" size={20} />
                <p className="mt-2 font-bold text-amber-900">
                  {t("keyInsight")}
                </p>
                <p className="mt-1 text-sm leading-relaxed text-amber-800">
                  {top.impact === "Positive"
                    ? t("insightPositive", {
                        feature: t(`features.${top.name}`),
                      })
                    : t("insightNegative", {
                        feature: t(`features.${top.name}`),
                      })}
                </p>
              </div>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
