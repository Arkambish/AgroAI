"use client";

import { useEffect, useState } from "react";
import {
  Lightbulb,
  CheckCircle2,
  ShieldAlert,
  Zap,
  ArrowUpRight,
} from "lucide-react";

import { useTranslations } from "next-intl";
import { convertSHAPToExplanation, type PredictResponse } from "@/lib/api";
import { clsx } from "clsx";

export default function RecommendationPage() {
  const t = useTranslations();

  const [prediction, setPrediction] = useState<PredictResponse | null>(null);
  const [explanations, setExplanations] = useState<any[]>([]);

  useEffect(() => {
    const lastPrediction = localStorage.getItem("last_prediction");

    if (lastPrediction) {
      const parsed = JSON.parse(lastPrediction);
      setPrediction(parsed);
      setExplanations(convertSHAPToExplanation(parsed.shap_values));
    }
  }, []);

  // --------------------------
  // EMPTY STATE
  // --------------------------
  if (!prediction) {
    return (
      <div className="flex min-h-[400px] flex-col items-center justify-center space-y-4 text-center">
        <div className="rounded-full bg-slate-100 p-6">
          <Lightbulb size={64} className="text-slate-300" />
        </div>

        <h2 className="text-2xl font-bold text-slate-900">
          {t("recommend.noTitle") || "No Recommendations Yet"}
        </h2>

        <p className="max-w-md text-slate-500">
          {t("recommend.noDescription") ||
            "Please make a prediction first to see personalized agricultural advice."}
        </p>

        <a
          href="/predict"
          className="rounded-xl bg-primary px-6 py-3 font-bold text-white shadow-lg transition-transform hover:scale-105"
        >
          {t("recommend.start") || "Start Now"}
        </a>
      </div>
    );
  }

  // --------------------------
  // STRATEGIES LOGIC
  // --------------------------
  const getStrategies = () => {
    const strategies: any[] = [];
    const negativeFactors = explanations.filter(
      (e) => e.impact === "Negative",
    );

    if (negativeFactors.some((e) => e.name.toLowerCase().includes("rainfall"))) {
      strategies.push({
        title: t("recommend.irrigationTitle"),
        description: t("recommend.irrigationDesc"),
        icon: Zap,
      });
    }

    if (negativeFactors.some((e) => e.name.toLowerCase().includes("temp"))) {
      strategies.push({
        title: t("recommend.heatTitle"),
        description: t("recommend.heatDesc"),
        icon: ShieldAlert,
      });
    }

    if (negativeFactors.some((e) => e.name.toLowerCase().includes("soil ph"))) {
      strategies.push({
        title: t("recommend.phTitle"),
        description: t("recommend.phDesc"),
        icon: CheckCircle2,
      });
    }

    if (strategies.length < 3) {
      strategies.push({
        title: t("recommend.nutrientTitle"),
        description: t("recommend.nutrientDesc"),
        icon: CheckCircle2,
      });

      strategies.push({
        title: t("recommend.pestTitle"),
        description: t("recommend.pestDesc"),
        icon: ShieldAlert,
      });
    }

    return strategies;
  };

  // --------------------------
  // UI
  // --------------------------
  return (
    <div className="space-y-10">
      {/* Header */}
      <div className="flex flex-col space-y-2">
        <h1 className="text-3xl font-bold tracking-tight text-slate-900">
          {t("recommend.title")}
        </h1>

        <p className="text-slate-500">
          {t("recommend.subtitle")}
        </p>
      </div>

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
        {/* LEFT */}
        <div className="lg:col-span-2 space-y-6">
          <h2 className="text-xl font-bold text-slate-800">
            {t("recommend.strategyTitle")}
          </h2>

          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
            {getStrategies().map((strategy, index) => (
              <div
                key={index}
                className="rounded-3xl border bg-white p-6 shadow-md"
              >
                <div className="mb-4 inline-flex rounded-2xl bg-lime-100 p-4 text-lime-600">
                  <strategy.icon size={28} />
                </div>

                <h3 className="text-xl font-bold text-slate-900">
                  {strategy.title}
                </h3>

                <p className="mt-2 text-slate-600">
                  {strategy.description}
                </p>

                <button className="mt-6 flex items-center space-x-1 font-bold text-primary hover:underline">
                  <span>{t("recommend.learnHow")}</span>
                  <ArrowUpRight size={16} />
                </button>
              </div>
            ))}
          </div>

          {/* WHAT IF */}
          <div className="rounded-3xl bg-gradient-to-br from-emerald-600 to-lime-600 p-8 text-white shadow-xl">
            <h3 className="text-2xl font-bold">
              {t("recommend.whatIfTitle")}
            </h3>

            <p className="mt-2 text-emerald-50 opacity-90">
              {t("recommend.whatIfText", {
                current: prediction.predicted_yield_MT_per_Ha,
                improved: (prediction.predicted_yield_MT_per_Ha * 1.15).toFixed(1),
              })}
            </p>
          </div>
        </div>

        {/* RIGHT */}
        <div className="space-y-6">
          <h2 className="text-xl font-bold text-slate-800">
            {t("recommend.riskTitle")}
          </h2>

          {[
            {
              title: t("recommend.heatRisk"),
              risk: "Moderate",
              action: t("recommend.heatAction"),
            },
            {
              title: t("recommend.soilRisk"),
              risk: "Low",
              action: t("recommend.soilAction"),
            },
            {
              title: t("recommend.pestRisk"),
              risk: "High",
              action: t("recommend.pestAction"),
            },
          ].map((risk, index) => (
            <div
              key={index}
              className="rounded-2xl border bg-white p-5 shadow-sm"
            >
              <div className="flex items-center justify-between">
                <h4 className="font-bold text-slate-900">
                  {risk.title}
                </h4>

                <span
                  className={clsx(
                    "rounded-full px-2 py-1 text-[10px] font-bold uppercase",
                    risk.risk === "High"
                      ? "bg-red-100 text-red-600"
                      : risk.risk === "Moderate"
                        ? "bg-amber-100 text-amber-600"
                        : "bg-emerald-100 text-emerald-600",
                  )}
                >
                  {risk.risk}
                </span>
              </div>

              <p className="mt-2 text-sm text-slate-500">
                <span className="font-bold">{t("recommend.action")}:</span>{" "}
                {risk.action}
              </p>
            </div>
          ))}

          <div className="rounded-2xl bg-slate-900 p-6 text-white">
            <h4 className="font-bold">{t("recommend.expertTitle")}</h4>

            <p className="mt-2 text-sm text-slate-400">
              {t("recommend.expertDesc")}
            </p>

            <button className="mt-4 w-full rounded-xl bg-emerald-600 py-3 font-bold text-white">
              {t("recommend.findOfficer")}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}