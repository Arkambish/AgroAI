"use client";

import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { Brain, TrendingUp, TrendingDown, AlertTriangle } from "lucide-react";
import { convertSHAPToExplanation, type PredictResponse } from "@/lib/api";
import clsx from "clsx";

export type ExplanationItem = {
  name: string;
  impact: "Positive" | "Negative";
  color?: string;
  raw: number;
};

export default function ExplainPage() {
  const t = useTranslations("explain");

  const [prediction, setPrediction] = useState<PredictResponse | null>(null);
  const [explanations, setExplanations] = useState<ExplanationItem[]>([]);

  useEffect(() => {
    const lastPrediction = localStorage.getItem("last_prediction");

    if (!lastPrediction) return;

    try {
      const parsed: PredictResponse = JSON.parse(lastPrediction);

      setPrediction(parsed);

      if (parsed?.shap_values) {
        setExplanations(convertSHAPToExplanation(parsed.shap_values));
      }
    } catch (err) {
      console.error("Failed to load prediction:", err);
    }
  }, []);

  if (!prediction) {
    return (
      <div className="flex min-h-[400px] flex-col items-center justify-center space-y-4 text-center">
        <div className="rounded-full bg-slate-100 p-6 dark:bg-slate-800">
          <Brain size={64} className="text-slate-300" />
        </div>

        <h2 className="text-2xl font-bold text-slate-900 dark:text-white">
          {t("noPrediction")}
        </h2>

        <p className="max-w-md text-slate-500">
          {t("noDescription")}
        </p>

        <a
          href="/predict"
          className="rounded-xl bg-primary px-6 py-3 font-bold text-white shadow-lg transition-transform hover:scale-105"
        >
          {t("goPredict")}
        </a>
      </div>
    );
  }

  return (
    <div className="space-y-10">

      {/* Header */}
      <div className="flex flex-col space-y-2">
        <h1 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
          {t("title")}
        </h1>

        <p className="text-slate-500 dark:text-slate-400">
          {t("subtitle")} {prediction.predicted_yield_MT_per_Ha} MT/Ha
        </p>
      </div>

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-2">

        {/* Left */}
        <section className="space-y-6">
          <h2 className="text-xl font-bold text-slate-800 dark:text-slate-200">
            {t("keyFactors")}
          </h2>

          <div className="grid gap-4">
            {explanations.map((item, index) => (
              <div
                key={index}
                className="flex justify-between rounded-xl border bg-white p-4 dark:bg-slate-900"
              >
                <div>
                  <p className="font-bold">{item.name}</p>
                  <p className={clsx(item.color)}>
                    {item.impact} {t("relative")}
                  </p>
                </div>

                <div className="flex items-center">
                  {item.impact === "Positive" ? (
                    <TrendingUp className="text-emerald-500" />
                  ) : (
                    <TrendingDown className="text-red-500" />
                  )}
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Right */}
        <section className="space-y-6">
          <h2 className="text-xl font-bold text-slate-800 dark:text-slate-200">
            {t("summary")}
          </h2>

          <div className="rounded-xl border bg-white p-6 dark:bg-slate-900">

            <p>
              {t("basedOn")}{" "}
              <b>{prediction.district}</b>{" "}
              {t("expected")}{" "}
              <b>{prediction.predicted_yield_MT_per_Ha} MT/Ha</b>
            </p>

            <ul className="mt-4 list-disc pl-6">
              {explanations.map((item, i) => (
                <li key={i}>
                  <b>{item.name}</b>{" "}
                  {item.impact === "Positive"
                    ? t("positive")
                    : t("negative")}
                </li>
              ))}
            </ul>

            <div className="mt-6 rounded bg-amber-50 p-4 dark:bg-amber-900/10">
              <AlertTriangle className="text-amber-500" />
              <p className="mt-2 font-bold">
                {t("keyInsight")}
              </p>
            </div>

          </div>
        </section>

      </div>
    </div>
  );
}