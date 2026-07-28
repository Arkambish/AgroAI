"use client";

import {
  ArrowRight,
  CheckCircle2,
  History,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  Database,
} from "lucide-react";
import { useTranslations } from "next-intl";
import { clsx } from "clsx";
import type { BaselineResponse, PredictResponse } from "@/lib/api";

interface Props {
  result: PredictResponse;
  baseline: BaselineResponse | null;
  locale: string;
}

/**
 * Honest result presentation.
 *
 * Leads with the interval rather than the point estimate: on the real-data
 * model the 90% conformal half-width is ±7.45 MT/Ha against a ~16 MT/Ha mean,
 * so a single confident-looking number misrepresents the model. The interval
 * method, the model R² and the data provenance are all shown rather than hidden.
 */
export default function PredictionResultCard({
  result,
  baseline,
  locale,
}: Props) {
  const t = useTranslations("predict");
  const tDistricts = useTranslations("districts");
  const tSeasons = useTranslations("seasons");

  const districtKey = result.district?.toLowerCase() ?? "";
  const seasonKey = result.season?.toLowerCase() ?? "";
  const districtName = tDistricts.has(districtKey)
    ? tDistricts(districtKey)
    : result.district;
  const seasonName = tSeasons.has(seasonKey)
    ? tSeasons(seasonKey)
    : result.season;

  const point = result.predicted_yield_MT_per_Ha;
  const completeness = result.data_completeness;

  // Describe how the interval was actually produced — a calibrated conformal
  // band and a crude ±15% heuristic used to render identically.
  const intervalNote = (() => {
    const method = result.interval_method ?? "";
    if (method.startsWith("conformal")) {
      const pct = method.replace("conformal_", "").replace("pct", "");
      return t("intervalConformal", { pct });
    }
    if (method === "gaussian_1.96rmse") return t("intervalGaussian");
    if (method === "heuristic_15pct") return t("intervalHeuristic");
    return null;
  })();

  const r2 = result.model_r2;
  // Reliability is a property of the model, not of this one prediction — the
  // backend derives it from the global R². Label it as such.
  const reliability = (() => {
    if (r2 === null || r2 === undefined) return "unknown";
    if (r2 >= 0.7) return "high";
    if (r2 >= 0.5) return "medium";
    return "low";
  })();

  const delta =
    baseline && baseline.mean > 0
      ? ((point - baseline.mean) / baseline.mean) * 100
      : null;
  const isDown = delta !== null && delta < 0;

  return (
    <div className="space-y-6">
      {/* Interval first, point estimate second. */}
      <div className="overflow-hidden rounded-3xl border border-emerald-200 bg-gradient-to-br from-emerald-50 via-white to-emerald-100/60 p-8 shadow-xl">
        <p className="text-xs font-bold uppercase tracking-wider text-emerald-700">
          {t("expectedRange")}
        </p>

        <h2 className="mt-2 flex flex-wrap items-baseline gap-x-3 text-4xl font-black text-emerald-950">
          <span className="tabular-nums">
            {result.confidence_lower.toFixed(1)}
          </span>
          <span className="text-2xl font-medium text-emerald-700">–</span>
          <span className="tabular-nums">
            {result.confidence_upper.toFixed(1)}
          </span>
          <span className="text-lg font-medium text-emerald-800">MT/Ha</span>
        </h2>

        <p className="mt-3 flex items-center gap-2 text-sm font-semibold text-emerald-900">
          <TrendingUp size={16} />
          {t("mostLikely", { value: point.toFixed(2) })}
        </p>

        {intervalNote && (
          <p className="mt-4 border-t border-emerald-100 pt-3 text-xs leading-relaxed text-emerald-800/80">
            {intervalNote}
          </p>
        )}

        <div className="mt-3 flex flex-wrap items-center justify-between gap-2 text-xs font-semibold text-emerald-900">
          <span>
            {districtName} · {seasonName} {result.year}
          </span>
          <span>{t("modelLabel", { model: result.model })}</span>
        </div>
      </div>

      {/* Model reliability — global, not per-prediction. */}
      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-md">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center space-x-3">
            <div
              className={clsx(
                "h-3.5 w-3.5 rounded-full shadow-sm",
                reliability === "high" && "bg-emerald-500",
                reliability === "medium" && "bg-amber-500",
                (reliability === "low" || reliability === "unknown") &&
                  "bg-red-500",
              )}
            />
            <span className="text-base font-bold text-slate-900">
              {t("modelReliability")}
            </span>
          </div>
          <span className="rounded-lg bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">
            {r2 !== null && r2 !== undefined
              ? t("r2Value", { value: r2.toFixed(3) })
              : t("r2Unknown")}
          </span>
        </div>
        <p className="mt-3 text-xs leading-relaxed text-slate-500">
          {t(`reliabilityNote.${reliability}`)}
        </p>
      </div>

      {/* Real per-district baseline — replaces the hardcoded 13.5 MT/Ha. */}
      {baseline && (
        <div className="grid grid-cols-2 gap-4">
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-xs font-bold text-slate-500">
              {t("districtAverage")}
            </p>
            <div className="mt-2 flex items-center space-x-2">
              <History size={18} className="text-slate-400" />
              <span className="text-lg font-bold text-slate-900 tabular-nums">
                {baseline.mean.toFixed(2)} MT/Ha
              </span>
            </div>
            {/* <p className="mt-1.5 text-[11px] text-slate-400">
              {t("baselineYears", { n: baseline.n_years })}
            </p> */}
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-xs font-bold text-slate-500">{t("change")}</p>
            <div className="mt-2 flex items-center space-x-2">
              {isDown ? (
                <TrendingDown size={18} className="text-red-500" />
              ) : (
                <TrendingUp size={18} className="text-emerald-500" />
              )}
              <span
                className={clsx(
                  "text-lg font-bold tabular-nums",
                  isDown ? "text-red-600" : "text-emerald-600",
                )}
              >
                {delta !== null
                  ? `${delta >= 0 ? "+" : ""}${delta.toFixed(1)}%`
                  : "—"}
              </span>
            </div>
            {/* <p className="mt-1.5 text-[11px] text-slate-400">
              {t("vsDistrictAverage")}
            </p> */}
          </div>
        </div>
      )}

      {/* Data sources used for prediction */}
      {/* {completeness && (
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center space-x-2">
            <Database size={16} className="text-emerald-600" />
            <p className="text-xs font-bold text-slate-700">
              {t("dataSourcesTitle")}
            </p>
          </div>

          <p className="mt-2 text-xs leading-relaxed text-slate-600">
            {t("dataSourcesBody")}
          </p>

          <div className="mt-3 space-y-1.5 text-xs text-slate-600">
            <p>✓ Weather information</p>
            <p>✓ Satellite vegetation data</p>
            <p>✓ Soil characteristics</p>
            <p>✓ Historical harvest records</p>
          </div>
        </div>
      )} */}
      <div className="space-y-3 rounded-2xl bg-slate-900 p-6 text-white shadow-xl">
        <h4 className="flex items-center space-x-2 font-bold text-emerald-400">
          <CheckCircle2 size={20} />
          <span>{t("success")}</span>
        </h4>
        <p className="text-xs leading-relaxed text-slate-300">
          {t("successDescription")}
        </p>
        <a
          href={`/${locale}/explain`}
          className="mt-2 inline-flex items-center space-x-2 text-sm font-bold text-emerald-400 transition-colors hover:text-emerald-300"
        >
          <span>{t("whyPrediction")}</span>
          <ArrowRight size={16} />
        </a>
      </div>
    </div>
  );
}
