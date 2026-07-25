"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Lightbulb,
  CheckCircle2,
  ShieldAlert,
  Zap,
  Droplets,
  Sparkles,
  RotateCw,
} from "lucide-react";

import { useTranslations, useLocale } from "next-intl";
import {
  convertSHAPToExplanation,
  getBaseline,
  getRecommendation,
  type BaselineResponse,
  type ExplanationItem,
  type PredictResponse,
} from "@/lib/api";
import { useLocalJSON } from "@/lib/use-local-flag";
import { clsx } from "clsx";

type RiskLevel = "High" | "Moderate" | "Low";

export default function RecommendationPage() {
  const t = useTranslations();
  const locale = useLocale();

  const prediction = useLocalJSON<PredictResponse>("last_prediction");
  const explanations = useMemo<ExplanationItem[]>(
    () => convertSHAPToExplanation(prediction?.shap_values ?? {}),
    [prediction]
  );
  const [baseline, setBaseline] = useState<BaselineResponse | null>(null);

  const [aiRecommendation, setAiRecommendation] = useState<string | null>(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiError, setAiError] = useState(false);
  // Bumped by the retry button to re-run the fetch effect without changing
  // any of district/season/year/locale.
  const [aiRetryToken, setAiRetryToken] = useState(0);

  const predDistrict = prediction?.district;
  const predSeason = prediction?.season;
  const predYear = prediction?.year;

  useEffect(() => {
    if (!predDistrict || !predSeason) return;
    let active = true;

    getBaseline(predDistrict, predSeason)
      .then((data) => {
        if (active) setBaseline(data);
      })
      .catch(() => {
        if (active) setBaseline(null);
      });

    return () => {
      active = false;
    };
  }, [predDistrict, predSeason]);

  // Re-fetches whenever the underlying prediction or the UI language
  // changes — a language switch needs a fresh call anyway, since the
  // recommendation text itself is generated in that language, not
  // translated client-side.
  useEffect(() => {
    if (!predDistrict || !predSeason || predYear === undefined) return;
    let active = true;

    setAiLoading(true);
    setAiError(false);

    getRecommendation({
      district: predDistrict,
      season: predSeason,
      year: predYear,
      locale,
    })
      .then((data) => {
        if (!active) return;
        setAiRecommendation(data.recommendation);
      })
      .catch((err) => {
        console.error("Recommendation request failed:", err);
        if (active) setAiError(true);
      })
      .finally(() => {
        if (active) setAiLoading(false);
      });

    return () => {
      active = false;
    };
  }, [predDistrict, predSeason, predYear, locale, aiRetryToken]);

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

  // Factors that pulled the prediction down, strongest first.
  const negatives = explanations.filter((e) => e.impact === "Negative");
  // `name` is the translation key emitted by convertSHAPToExplanation, so these
  // match exactly. (This previously tested "soil ph" with a space against a
  // value of "soil_ph", so the pH strategy could never fire.)
  const hasNegative = (...keys: string[]) =>
    negatives.some((e) => keys.includes(e.name));
  // Severity follows the strongest related negative factor. A risk with no
  // related factor pulling the prediction down stays Low.
  const severityOf = (...keys: string[]): RiskLevel => {
    const worst = Math.max(
      0,
      ...negatives.filter((e) => keys.includes(e.name)).map((e) => e.magnitude)
    );
    if (worst >= 0.6) return "High";
    if (worst >= 0.25) return "Moderate";
    return "Low";
  };

  const getStrategies = () => {
    const strategies = [];

    if (hasNegative("rainfall", "drought", "rainfall_x_ndvi")) {
      strategies.push({
        key: "irrigation",
        title: t("recommend.irrigationTitle"),
        description: t("recommend.irrigationDesc"),
        icon: Droplets,
      });
    }

    if (hasNegative("temperature", "temp_x_humidity")) {
      strategies.push({
        key: "heat",
        title: t("recommend.heatTitle"),
        description: t("recommend.heatDesc"),
        icon: ShieldAlert,
      });
    }

    if (hasNegative("soil_ph")) {
      strategies.push({
        key: "ph",
        title: t("recommend.phTitle"),
        description: t("recommend.phDesc"),
        icon: Zap,
      });
    }

    if (strategies.length < 3) {
      strategies.push(
        {
          key: "nutrient",
          title: t("recommend.nutrientTitle"),
          description: t("recommend.nutrientDesc"),
          icon: CheckCircle2,
        },
        {
          key: "pest",
          title: t("recommend.pestTitle"),
          description: t("recommend.pestDesc"),
          icon: ShieldAlert,
        }
      );
    }

    return strategies;
  };

  // Risk levels now follow the SHAP factors instead of being literals.
  const risks: { key: string; title: string; risk: RiskLevel; action: string }[] =
    [
      {
        key: "heat",
        title: t("recommend.heatRisk"),
        risk: severityOf("temperature", "temp_x_humidity"),
        action: t("recommend.heatAction"),
      },
      {
        key: "soil",
        title: t("recommend.soilRisk"),
        risk: severityOf("rainfall", "drought", "rainfall_x_ndvi"),
        action: t("recommend.soilAction"),
      },
      {
        key: "pest",
        title: t("recommend.pestRisk"),
        risk: severityOf("humidity", "ndvi", "evi"),
        action: t("recommend.pestAction"),
      },
    ];

  const riskLabel = (risk: RiskLevel) =>
    ({
      High: t("recommend.riskHigh"),
      Moderate: t("recommend.riskModerate"),
      Low: t("recommend.riskLow"),
    })[risk];

  return (
    <div className="space-y-10">
      <div className="flex flex-col space-y-2">
        <h1 className="text-3xl font-bold tracking-tight text-slate-900">
          {t("recommend.title")}
        </h1>

        <p className="text-slate-500">{t("recommend.subtitle")}</p>
      </div>

      <div className="rounded-3xl bg-linear-to-br from-emerald-600 to-lime-600 p-8 text-white shadow-xl">
        <div className="mb-3 inline-flex items-center gap-2 rounded-full bg-white/15 px-3 py-1 text-xs font-bold uppercase tracking-wide">
          <Sparkles size={14} />
          <span>{t("recommend.aiTitle")}</span>
        </div>

        {aiLoading && (
          <div className="flex items-center gap-3 text-emerald-50">
            <div className="h-5 w-5 animate-spin rounded-full border-2 border-white/40 border-t-white" />
            <span>{t("recommend.aiLoading")}</span>
          </div>
        )}

        {!aiLoading && aiError && (
          <div className="flex flex-wrap items-center gap-4">
            <p className="text-emerald-50">{t("recommend.aiError")}</p>
            <button
              type="button"
              onClick={() => setAiRetryToken((n) => n + 1)}
              className="flex items-center gap-2 rounded-xl bg-white/15 px-4 py-2 text-sm font-bold transition-colors hover:bg-white/25"
            >
              <RotateCw size={14} />
              {t("recommend.aiRetry")}
            </button>
          </div>
        )}

        {!aiLoading && !aiError && aiRecommendation && (
          <p className="text-lg leading-relaxed text-emerald-50">
            {aiRecommendation}
          </p>
        )}
      </div>

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <h2 className="text-xl font-bold text-slate-800">
            {t("recommend.strategyTitle")}
          </h2>

          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
            {getStrategies().map((strategy) => (
              <div
                key={strategy.key}
                className="rounded-3xl border bg-white p-6 shadow-md"
              >
                <div className="mb-4 inline-flex rounded-2xl bg-lime-100 p-4 text-lime-600">
                  <strategy.icon size={28} />
                </div>

                <h3 className="text-xl font-bold text-slate-900">
                  {strategy.title}
                </h3>

                <p className="mt-2 text-slate-600">{strategy.description}</p>
              </div>
            ))}
          </div>

          {/* Compared against the district's best recorded season rather than
              an invented +15% "simulation". */}
          {baseline && (
            <div className="rounded-3xl bg-linear-to-br from-emerald-600 to-lime-600 p-8 text-white shadow-xl">
              <h3 className="text-2xl font-bold">
                {t("recommend.whatIfTitle")}
              </h3>

              <p className="mt-2 text-emerald-50 opacity-90">
                {t("recommend.whatIfText", {
                  current: prediction.predicted_yield_MT_per_Ha,
                  best: baseline.max.toFixed(1),
                })}
              </p>
            </div>
          )}
        </div>

        <div className="space-y-6">
          <h2 className="text-xl font-bold text-slate-800">
            {t("recommend.riskTitle")}
          </h2>

          {risks.map((risk) => (
            <div
              key={risk.key}
              className="rounded-2xl border bg-white p-5 shadow-sm"
            >
              <div className="flex items-center justify-between">
                <h4 className="font-bold text-slate-900">{risk.title}</h4>

                <span
                  className={clsx(
                    "rounded-full px-2 py-1 text-[10px] font-bold uppercase",
                    risk.risk === "High" && "bg-red-100 text-red-600",
                    risk.risk === "Moderate" && "bg-amber-100 text-amber-600",
                    risk.risk === "Low" && "bg-emerald-100 text-emerald-600"
                  )}
                >
                  {riskLabel(risk.risk)}
                </span>
              </div>

              <p className="mt-2 text-sm text-slate-500">
                <span className="font-bold">{t("recommend.action")}:</span>{" "}
                {risk.action}
              </p>
            </div>
          ))}

          <p className="text-[11px] leading-relaxed text-slate-400">
            {t("recommend.riskBasis")}
          </p>

          <div className="rounded-2xl bg-slate-900 p-6 text-white">
            <h4 className="font-bold">{t("recommend.expertTitle")}</h4>

            <p className="mt-2 text-sm text-slate-400">
              {t("recommend.expertDesc")}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
