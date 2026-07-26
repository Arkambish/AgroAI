"use client";

import { useMemo } from "react";
import { useRouter } from "next/navigation";
import { useTranslations, useLocale } from "next-intl";
import { Brain, TrendingUp, TrendingDown, AlertTriangle, RotateCcw } from "lucide-react";
import {
  convertSHAPToExplanation,
  type ExplanationItem,
  type PredictResponse,
} from "@/lib/api";
import { useLocalJSON, resetPrediction, PREDICTION_KEY } from "@/lib/use-local-flag";
import clsx from "clsx";

export type { ExplanationItem };

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
              // converts directly to kg/Ha for a number a farmer can picture.
              const kgPerHa = Math.round(Math.abs(item.raw) * 1000);
              const isPositive = item.impact === "Positive";

              return (
                <div
                  key={item.name}
                  className="rounded-xl border bg-white p-4 shadow-sm"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="font-bold text-slate-900">
                        {t(`features.${item.name}`)}
                      </p>
                      <p className={clsx("text-sm", item.color)}>
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
                    </div>

                    {isPositive ? (
                      <TrendingUp className="shrink-0 text-emerald-500" />
                    ) : (
                      <TrendingDown className="shrink-0 text-red-500" />
                    )}
                  </div>

                  {/* Diverging bar: extends right (emerald) from center for a
                      positive contribution, left (red) for negative — so the
                      direction is visible at a glance, not just the color. */}
                  <div className="mt-3">
                    <div className="flex items-center justify-between text-[11px] text-slate-400">
                      <span>{t("relative")}</span>
                      <span className="font-mono tabular-nums">
                        {item.raw > 0 ? "+" : ""}
                        {item.raw.toFixed(3)}
                      </span>
                    </div>
                    <div className="relative mt-1 h-2 w-full overflow-hidden rounded-full bg-slate-100">
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
