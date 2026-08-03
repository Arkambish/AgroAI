"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Lightbulb,
  Sprout,
  Droplets,
  Flame,
  CloudRain,
  CheckCircle2,
  ChevronDown,
  RotateCcw,
  Phone,
} from "lucide-react";
import { clsx } from "clsx";

import { useTranslations, useLocale } from "next-intl";
import { type PredictResponse } from "@/lib/api";
import {
  evaluateAgronomicRules,
  type AgronomicRecommendation,
  type AgronomicRisk,
  type RecommendationCategory,
} from "@/lib/agronomy";
import { useLocalJSON, resetPrediction, PREDICTION_KEY } from "@/lib/use-local-flag";

const CATEGORY_ICON: Record<RecommendationCategory, typeof Sprout> = {
  soil: Sprout,
  water: Droplets,
  heat: Flame,
  humidity: CloudRain,
};

const LEVEL_BADGE_CLASS: Record<"high" | "medium" | "low", string> = {
  high: "bg-red-100 text-red-600",
  medium: "bg-amber-100 text-amber-600",
  low: "bg-emerald-100 text-emerald-600",
};

const RELIABILITY_EMOJI: Record<string, string> = {
  cardHigh: "🟢",
  cardGood: "🟡",
  cardModerate: "🟠",
  cardLow: "🔴",
  cardUnknown: "⚪",
};

function formatValue(unit: string, value: number): string {
  if (unit === "pH") return value.toFixed(1);
  return Math.round(value).toString();
}

export default function RecommendationPage() {
  const t = useTranslations();
  const locale = useLocale();
  const router = useRouter();

  const prediction = useLocalJSON<PredictResponse>(PREDICTION_KEY);

  // Same centralized reset used on Predict/Explain — clears the shared
  // prediction/SHAP state and sends the farmer back to the form to start
  // over.
  const handleNewPrediction = () => {
    resetPrediction();
    router.push(`/${locale}/predict`);
  };

  const { recommendations, risks } = useMemo(
    () =>
      prediction
        ? evaluateAgronomicRules(prediction)
        : { recommendations: [], risks: [] },
    [prediction]
  );

  // Independent per-card "Why am I seeing this?" disclosure state, closed
  // by default so the simple view stays uncluttered.
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const toggleExpanded = (id: string) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  if (!prediction) {
    return (
      <div className="flex min-h-100 flex-col items-center justify-center space-y-4 text-center">
        <div className="rounded-full bg-slate-100 p-6">
          <Lightbulb size={64} className="text-slate-300" />
        </div>

        <h2 className="text-2xl font-bold text-slate-900">
          {t("recommend.noTitle")}
        </h2>

        <p className="max-w-md text-slate-500">
          {t("recommend.noDescription")}
        </p>

        <a
          href={`/${locale}/predict`}
          className="rounded-xl bg-primary px-6 py-3 font-bold text-white shadow-lg transition-transform hover:scale-105"
        >
          {t("recommend.start")}
        </a>
      </div>
    );
  }

  const hasFindings = recommendations.length > 0 || risks.length > 0;

  return (
    <div className="space-y-10">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-start">
        <div className="flex flex-col space-y-2">
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">
            {t("recommend.title")}
          </h1>

          <p className="text-slate-500">{t("recommend.subtitle")}</p>
        </div>

        <button
          type="button"
          onClick={handleNewPrediction}
          className="flex shrink-0 items-center justify-center space-x-2 rounded-2xl border-2 border-slate-200 bg-white px-5 py-3 font-bold text-slate-600 transition-colors hover:border-slate-300 hover:bg-slate-50"
        >
          <RotateCcw size={18} />
          <span>{t("button.newPrediction")}</span>
        </button>
      </div>

      {!hasFindings && (
        <div className="flex items-start gap-4 rounded-3xl border border-emerald-200 bg-emerald-50 p-6 shadow-sm">
          <CheckCircle2 className="mt-0.5 shrink-0 text-emerald-600" size={28} />
          <div>
            <h3 className="text-lg font-bold text-emerald-900">
              {t("recommend.allGoodTitle")}
            </h3>
            <p className="mt-1 text-sm text-emerald-800">
              {t("recommend.allGoodDesc")}
            </p>
          </div>
        </div>
      )}

      {recommendations.length > 0 && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          {recommendations.map((rec) => (
            <RecommendationCard
              key={rec.id}
              rec={rec}
              t={t}
              isExpanded={expanded.has(rec.id)}
              onToggle={() => toggleExpanded(rec.id)}
            />
          ))}
        </div>
      )}

      {recommendations.length > 0 && (
        <div className="rounded-3xl bg-linear-to-br from-emerald-600 to-lime-600 p-8 text-white shadow-xl">
          <h3 className="text-xl font-bold">{t("recommend.ifYouActTitle")}</h3>
          <p className="mt-2 text-emerald-50 opacity-90">
            {t("recommend.ifYouActText")}
          </p>
        </div>
      )}

      {risks.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-xl font-bold text-slate-800">
            {t("recommend.risksTitle")}
          </h2>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            {risks.map((risk) => (
              <RiskCard key={risk.id} risk={risk} t={t} />
            ))}
          </div>
        </div>
      )}

      <div className="rounded-2xl bg-slate-900 p-6 text-white">
        <div className="flex items-center gap-2">
          <Phone size={18} className="text-slate-300" />
          <h4 className="font-bold">{t("recommend.expertTitle")}</h4>
        </div>
        <p className="mt-2 text-sm text-slate-400">
          {t("recommend.expertDesc")}
        </p>
      </div>
    </div>
  );
}

function RecommendationCard({
  rec,
  t,
  isExpanded,
  onToggle,
}: {
  rec: AgronomicRecommendation;
  t: ReturnType<typeof useTranslations>;
  isExpanded: boolean;
  onToggle: () => void;
}) {
  const Icon = CATEGORY_ICON[rec.category];
  const current = formatValue(rec.unit, rec.currentValue);
  const [min, max] = rec.recommendedRange;

  return (
    <div className="space-y-4 rounded-3xl border bg-white p-6 shadow-md">
      <div className="flex items-center gap-3">
        <div className="inline-flex rounded-2xl bg-lime-100 p-3 text-lime-600">
          <Icon size={24} />
        </div>
        <h3 className="text-lg font-bold text-slate-900">
          {t(`recommend.rules.${rec.id}.title`)}
        </h3>
      </div>

      <div>
        <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">
          {t("recommend.impactLabel")}
        </p>
        <p className="mt-0.5 text-sm font-bold text-red-600">
          {t("recommend.impactReduced")}
        </p>
      </div>

      <div>
        <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">
          {t("recommend.reasonLabel")}
        </p>
        <p className="mt-0.5 text-sm text-slate-700">
          {t(`recommend.rules.${rec.id}.reason`, {
            current,
            min: formatValue(rec.unit, min),
            max: formatValue(rec.unit, max),
          })}
        </p>
      </div>

      <div>
        <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">
          {t("recommend.actionLabel")}
        </p>
        <p className="mt-0.5 text-sm font-bold text-slate-900">
          {t(`recommend.rules.${rec.id}.action`)}
        </p>
      </div>

      {/* <div>
        <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">
          {t("recommend.reliabilityLabel")}
        </p>
        <p className="mt-0.5 flex items-center gap-1.5 text-sm font-bold text-slate-800">
          <span aria-hidden="true">{RELIABILITY_EMOJI[rec.reliabilityTier]}</span>
          <span>{t(`explain.reliability.${rec.reliabilityTier}`)}</span>
          {rec.reliability !== undefined && (
            <span className="font-semibold text-slate-500">
              {Math.round(rec.reliability * 100)}%
            </span>
          )}
        </p>
      </div> */}

      <button
        type="button"
        onClick={onToggle}
        aria-expanded={isExpanded}
        className="flex items-center gap-1 border-t border-dashed border-slate-100 pt-3 text-[11px] font-semibold text-slate-400 transition-colors hover:text-slate-600"
      >
        <ChevronDown
          size={12}
          className={clsx("transition-transform", isExpanded && "rotate-180")}
        />
        <span>{t("recommend.whyToggle")}</span>
      </button>

      {isExpanded && (
        <div className="space-y-2 rounded-lg bg-slate-50 p-3 text-xs text-slate-600">
          <div>
            <span className="font-semibold text-slate-500">
              {t("recommend.whyFeature")}:
            </span>{" "}
            {t(`features.${rec.valueFeature}`)}
          </div>
          <div>
            <span className="font-semibold text-slate-500">
              {t("recommend.whyShap")}:
            </span>{" "}
            {t("recommend.whyShapNegative")}
          </div>
          <div>
            <span className="font-semibold text-slate-500">
              {t("recommend.whyCurrentValue")}:
            </span>{" "}
            {current} {rec.unit}
          </div>
          <div>
            <span className="font-semibold text-slate-500">
              {t("recommend.whyRecommendedRange")}:
            </span>{" "}
            {formatValue(rec.unit, min)} – {formatValue(rec.unit, max)} {rec.unit}
          </div>
          <div>
            <span className="font-semibold text-slate-500">
              {t("recommend.whySource")}:
            </span>{" "}
            {rec.source}
          </div>
        </div>
      )}
    </div>
  );
}

function RiskCard({
  risk,
  t,
}: {
  risk: AgronomicRisk;
  t: ReturnType<typeof useTranslations>;
}) {
  const Icon = CATEGORY_ICON[risk.category];

  return (
    <div className="space-y-3 rounded-2xl border bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <Icon size={20} className="text-amber-500" />
          <h4 className="font-bold text-slate-900">
            {t(`recommend.rules.${risk.id}.title`)}
          </h4>
        </div>

        <span
          className={clsx(
            "rounded-full px-2 py-1 text-[10px] font-bold uppercase",
            LEVEL_BADGE_CLASS[risk.level]
          )}
        >
          {t(`recommend.level.${risk.level}`)}
        </span>
      </div>

      <p className="text-sm text-slate-600">
        {t(`recommend.rules.${risk.id}.reason`, {
          current: formatValue(risk.unit, risk.currentValue),
        })}
      </p>

      <p className="text-sm text-slate-500">
        <span className="font-bold text-slate-700">
          {t("recommend.riskActionLabel")}:
        </span>{" "}
        {t(`recommend.rules.${risk.id}.action`)}
      </p>
    </div>
  );
}
