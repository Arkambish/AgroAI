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

/** 4-tier scheme for the per-card "Confidence" readout — distinct from (and
 * more granular than) the 3-tier scheme used once, up top, for the overall
 * prediction-level reliability. Keeping two different words ("Confidence"
 * per card vs. "Explanation reliability" once at the top) for two genuinely
 * different numbers (per-feature ERI vs. the prediction-level aggregate) is
 * what stops the page from reading as the same phrase repeated everywhere. */
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

/** Same 3-tier thresholds as the old top-of-page badge (0.4 / 0.7), just
 * resolved into the pieces the new summary card actually renders: an emoji,
 * a "{level} confidence" phrase, and a one-line plain-language note. */
function summaryReliability(
  eriLevel: "levelHigh" | "levelMedium" | "levelLow" | undefined
): {
  emoji: string;
  confidenceKey: "confidenceHigh" | "confidenceMedium" | "confidenceLow" | "confidenceUnknown";
  noteKey: "levelHigh" | "levelMedium" | "levelLow" | "unknown";
} {
  if (eriLevel === "levelHigh") {
    return { emoji: "🟢", confidenceKey: "confidenceHigh", noteKey: "levelHigh" };
  }
  if (eriLevel === "levelMedium") {
    return { emoji: "🟡", confidenceKey: "confidenceMedium", noteKey: "levelMedium" };
  }
  if (eriLevel === "levelLow") {
    return { emoji: "🔴", confidenceKey: "confidenceLow", noteKey: "levelLow" };
  }
  return { emoji: "⚪", confidenceKey: "confidenceUnknown", noteKey: "unknown" };
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

  // Per-row ERI: each displayed factor can fold in several raw model
  // features (e.g. NDVI's 3 variants), so its reliability is the
  // |SHAP|-weighted average of per_feature_eri across just those raw
  // features — the same weighting the backend uses to roll per-feature ERI
  // up into one prediction-level score.
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
  // name for O(1) access while rendering the cards below.
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
  const summary = summaryReliability(eriLevel);

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

  // The strongest factor drives the key insight — the one thing a farmer
  // takes away, rather than a restatement of every factor already shown as
  // its own card above.
  const top = explanations[0];

  return (
    <div className="space-y-8">
      {/* 1. Prediction summary card — expected yield + the ONE place overall
          explanation reliability is shown on this page. Everything below
          this uses the word "Confidence" instead, so the same phrase isn't
          repeated card after card. */}
      <div className="overflow-hidden rounded-3xl border border-emerald-200 bg-gradient-to-br from-emerald-50 via-white to-emerald-100/60 p-6 shadow-lg sm:p-8">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="flex items-center gap-2.5">
            <Brain className="text-emerald-700" size={24} />
            <h1 className="text-2xl font-bold text-slate-900 sm:text-3xl">
              {t("title")}
            </h1>
          </div>

          <button
            type="button"
            onClick={handleNewPrediction}
            className="flex shrink-0 items-center justify-center space-x-2 rounded-2xl border-2 border-white/80 bg-white/70 px-4 py-2.5 text-sm font-bold text-slate-600 backdrop-blur transition-colors hover:border-slate-200 hover:bg-white"
          >
            <RotateCcw size={16} />
            <span>{tButton("newPrediction")}</span>
          </button>
        </div>

        <p className="mt-3 text-lg font-semibold text-emerald-950">
          {t("summaryYield", { value: prediction.predicted_yield_MT_per_Ha })}
        </p>

        <div className="mt-5 rounded-2xl border border-emerald-100 bg-white/70 p-4">
          <p className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wide text-slate-500">
            <Brain size={13} />
            <span>{t("reliability.summaryLabel")}</span>
          </p>
          <div className="mt-1.5 flex flex-wrap items-baseline gap-x-2 gap-y-1">
            <span className="flex items-center gap-2 text-lg font-bold text-slate-900">
              <span aria-hidden="true">{summary.emoji}</span>
              <span>{t(`reliability.${summary.confidenceKey}`)}</span>
            </span>
            {eriScore !== undefined && (
              <span className="text-sm font-semibold text-slate-500">
                {Math.round(eriScore * 100)}%
              </span>
            )}
          </div>
          <p className="mt-2 text-xs leading-relaxed text-slate-600">
            {t(`reliability.summaryNote.${summary.noteKey}`)}
          </p>
        </div>
      </div>

      {/* 2. Main factors — one compact, farmer-friendly card per factor.
          This is the single place impact/effect/confidence per factor is
          shown; nothing above or below restates it. */}
      <section className="space-y-4">
        <h2 className="text-xl font-bold text-slate-800">
          {t("keyFactors")}
        </h2>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {explanations.map((item) => {
            // SHAP contribution is in the model's own units (MT/Ha), so it
            // converts directly to kg/Ha for a number a farmer can picture
            // — used only inside the technical details drawer.
            const kgPerHa = Math.round(Math.abs(item.raw) * 1000);
            const isPositive = item.impact === "Positive";
            const tier = effectTier(item.magnitude);
            const eri = eriByName.get(item.name);
            const reliability = reliabilityTier(eri);
            const isExpanded = expandedTechnical.has(item.name);

            return (
              <div
                key={item.name}
                className="space-y-4 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
              >
                <div className="flex items-center gap-3">
                  <span className="text-3xl" aria-hidden="true">
                    {FEATURE_EMOJI[item.name] ?? FEATURE_EMOJI.other}
                  </span>
                  <p className="text-base font-bold text-slate-900">
                    {t(`features.${item.name}`)}
                  </p>
                </div>

                {/* Stacked label/value rows — a card a farmer can read top
                    to bottom, not a technical grid of columns. No raw SHAP
                    numbers here; those only appear once expanded below. */}
                <div className="space-y-3">
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
                  className="flex items-center gap-1 border-t border-dashed border-slate-100 pt-3 text-[11px] font-semibold text-slate-400 transition-colors hover:text-slate-600"
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
                  <div className="space-y-3 rounded-lg bg-slate-50 p-3 text-xs text-slate-600">
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
                        negative — the raw SHAP value this card keeps
                        hidden until expanded. */}
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

      {/* 3. Key Insight — one simple conclusion, not another list of every
          factor already shown as its own card above. */}
      {top && (
        <div className="rounded-2xl border border-amber-200 bg-amber-50 p-6 shadow-sm">
          <div className="flex items-center gap-2">
            <AlertTriangle className="text-amber-500" size={20} />
            <p className="font-bold text-amber-900">{t("keyInsight")}</p>
          </div>
          <p className="mt-2 text-sm leading-relaxed text-amber-800">
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
  );
}
