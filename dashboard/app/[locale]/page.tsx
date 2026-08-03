"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import {
  Calendar,
  TrendingUp,
  MapPin,
  BarChart3,
  ArrowRight,
  Sparkles,
} from "lucide-react";
import StatCard from "@/components/StatCard";
import DistrictMap from "@/components/DistrictMap";
import Link from "next/link";
import { motion } from "framer-motion";
import { useTranslations } from "next-intl";
import {
  predictYieldsForAllDistricts,
  TARGET_DISTRICTS,
  type BatchPredictionResult,
  getYieldCategory,
} from "@/lib/api";

export default function Home() {
  const t = useTranslations();
  const params = useParams();
  const locale = params.locale as string;

  const [batchResult, setBatchResult] = useState<BatchPredictionResult | null>(
    null
  );
  const [selectedDistrict, setSelectedDistrict] = useState<string | null>(
    "Matale"
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const container = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
      },
    },
  };
  const item = {
    hidden: { y: 20, opacity: 0 },
    show: { y: 0, opacity: 1 },
  };

  useEffect(() => {
    let mounted = true;

    const fetchMultiDistrictData = async () => {
      setLoading(true);
      setError(null);

      try {
        // Yala is the only season this dashboard offers (Maha was retired),
        // so it's hardcoded rather than read from the districts catalog.
        const season = "Yala";
        // Always the current year unless the user explicitly picks another
        // (there's no year selector on this page yet) — NOT the dataset's
        // last year, which for the synthetic variant is 2023.
        const requestYear = new Date().getFullYear();

        // TEMP DEBUG — remove once district/year propagation is verified.
        console.log("[Home] requesting predictions", {
          districts: TARGET_DISTRICTS,
          season,
          year: requestYear,
        });

        const result = await predictYieldsForAllDistricts(
          season,
          requestYear,
          {},
          TARGET_DISTRICTS
        );

        if (mounted) {
          setBatchResult(result);
          if (result.bestDistrict) {
            setSelectedDistrict(result.bestDistrict);
          }
        }
      } catch (err) {
        if (mounted) {
          setError(
            err instanceof Error
              ? err.message
              : "Unable to load multi-district yield predictions."
          );
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };

    fetchMultiDistrictData();

    return () => {
      mounted = false;
    };
  }, []);

  const districtPredictions = batchResult?.districtYields || {};

  const currentYear = new Date().getFullYear();
  const seasonValue = loading
    ? t("dashboard.loadingValue")
    : batchResult
    ? `${t("seasons.yala")} ${currentYear}`
    : error
    ? t("dashboard.unavailable")
    : "--";

  const averageYieldValue = loading
    ? t("dashboard.loadingValue")
    : batchResult
    ? `${batchResult.averageYield.toFixed(2)} MT/Ha`
    : error
    ? t("dashboard.unavailable")
    : "--";

  const translateDistrict = (name: string) =>
    t.has(`districts.${name.toLowerCase()}`)
      ? t(`districts.${name.toLowerCase()}`)
      : name;

  const bestDistrictValue = loading
    ? t("dashboard.loadingValue")
    : batchResult
    ? translateDistrict(batchResult.bestDistrict)
    : error
    ? t("dashboard.unavailable")
    : "--";

  const highestYieldValue = loading
    ? t("dashboard.loadingValue")
    : batchResult
    ? `${batchResult.highestYield.toFixed(2)} MT/Ha`
    : error
    ? t("dashboard.unavailable")
    : "--";

  const selectedPrediction =
    selectedDistrict && batchResult?.predictions[selectedDistrict]
      ? batchResult.predictions[selectedDistrict]
      : null;

  return (
    <div className="space-y-10">
      {error && (
        <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Top Section: Intro Left, Map Right. Grid rows stretch to the
          tallest column by default, so the map (styled h-full in
          DistrictMap.tsx) fills exactly the left column's height with no
          leftover gap beneath it — see DistrictMap.tsx for the mobile-only
          min-height floor used when there's no row to stretch against. */}
      <div className="grid grid-cols-1 gap-8 lg:grid-cols-2 lg:items-stretch">
        {/* Intro & Target District Overview - Left */}
        <div className="space-y-6 flex flex-col justify-between">
          <section className="relative overflow-hidden rounded-3xl bg-white p-8 text-emerald-950 shadow-xl border border-emerald-50">
            <div className="relative z-10">
              <div className="inline-flex items-center space-x-2 rounded-full bg-emerald-100/80 px-3 py-1 text-xs font-bold text-emerald-800 mb-4">
                <Sparkles size={14} />
                <span>{t("dashboard.badge")}</span>
              </div>

              <h1 className="text-4xl font-extrabold tracking-tight md:text-5xl">
                {t("title.home")
                  .split("AgriSense")
                  .map((part, index, arr) => (
                    <span key={`${part}-${index}`}>
                      {part}
                      {index < arr.length - 1 && (
                        <span className="text-emerald-600">AgriSense</span>
                      )}
                    </span>
                  ))}
              </h1>

              <p className="mt-4 text-base text-slate-600 leading-relaxed">
                {t("title.description")}
              </p>

              <div className="mt-6 flex flex-wrap gap-4">
                <Link
                  href={`/${locale}/predict`}
                  className="flex items-center space-x-2 rounded-xl bg-emerald-600 px-6 py-3 font-bold text-white shadow-lg transition-transform hover:scale-105 hover:bg-emerald-700"
                >
                  <span>{t("button.start")}</span>
                  <ArrowRight size={20} />
                </Link>
              </div>
            </div>
            <div className="absolute -right-20 -top-20 h-64 w-64 rounded-full bg-emerald-400 opacity-15 blur-3xl" />
            <div className="absolute -bottom-20 right-20 h-64 w-64 rounded-full bg-lime-300 opacity-20 blur-3xl" />
          </section>

          {/* Selected District Details Card */}
          {selectedPrediction ? (
            <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-md transition-all">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
                    {t("dashboard.districtFocus")}
                  </span>
                  <h3 className="text-2xl font-black text-slate-900">
                    {translateDistrict(selectedPrediction.district)}
                  </h3>
                </div>
                <div
                  className={`rounded-xl px-3 py-1 text-xs font-bold text-white ${
                    getYieldCategory(
                      selectedPrediction.predicted_yield_MT_per_Ha
                    ).bgClass
                  }`}
                >
                  {t(
                    `yieldCategory.${
                      getYieldCategory(
                        selectedPrediction.predicted_yield_MT_per_Ha
                      ).key
                    }`
                  )}{" "}
                  {t("dashboard.yieldSuffix")}
                </div>
              </div>

              <div className="mt-4 grid grid-cols-2 gap-4">
                <div className="rounded-2xl bg-emerald-50/70 p-4 border border-emerald-100">
                  <p className="text-xs font-semibold text-emerald-700">
                    {t("dashboard.predictedYield")}
                  </p>
                  <p className="mt-1 text-2xl font-black text-emerald-900">
                    {selectedPrediction.predicted_yield_MT_per_Ha.toFixed(2)}{" "}
                    <span className="text-xs font-normal">MT/Ha</span>
                  </p>
                </div>
                <div className="rounded-2xl bg-slate-50 p-4 border border-slate-100">
                  <p className="text-xs font-semibold text-slate-500">
                    {t("dashboard.confidenceRange")}
                  </p>
                  <p className="mt-1 text-sm font-bold text-slate-800">
                    {selectedPrediction.confidence_lower.toFixed(1)} –{" "}
                    {selectedPrediction.confidence_upper.toFixed(1)} MT/Ha
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <div className="rounded-3xl border border-dashed border-slate-200 bg-slate-50 p-6 text-center text-sm text-slate-500">
              {t("dashboard.mapHint")}
            </div>
          )}
        </div>

        {/* District Map Section - Right */}
        <div className="h-full">
          <DistrictMap
            predictions={districtPredictions}
            selectedDistrict={selectedDistrict}
            onSelectDistrict={(name) => {
              // TEMP DEBUG — remove once district/year propagation is verified.
              console.log("[Home] district selected:", name);
              setSelectedDistrict(name);
            }}
          />
        </div>
      </div>

      {/* Bottom Section: Stat Cards */}
      <motion.div
        variants={container}
        initial="hidden"
        animate="show"
        className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4"
      >
        <motion.div variants={item}>
          <StatCard
            label={t("dashboard.current_season")}
            value={seasonValue}
            icon={Calendar}
            color="bg-emerald-600"
          />
        </motion.div>
        <motion.div variants={item}>
          <StatCard
            label={t("dashboard.best_district") || "Best District"}
            value={bestDistrictValue}
            icon={MapPin}
            color="bg-lime-500"
          />
        </motion.div>
        <motion.div variants={item}>
          <StatCard
            label={t("dashboard.peakTargetYield")}
            value={highestYieldValue}
            icon={BarChart3}
            color="bg-emerald-600"
          />
        </motion.div>
        <motion.div variants={item}>
          <StatCard
            label={t("dashboard.averageYield")}
            value={averageYieldValue}
            icon={TrendingUp}
            color="bg-lime-500"
          />
        </motion.div>
      </motion.div>
    </div>
  );
}

