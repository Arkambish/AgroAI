"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Calendar,
  TrendingUp,
  MapPin,
  CloudSun,
  ArrowRight,
} from "lucide-react";
import StatCard from "@/components/StatCard";
import DistrictMap from "@/components/DistrictMap";
import Link from "next/link";
import { motion } from "framer-motion";
import { useTranslations } from "next-intl";
import { predictYield, type PredictResponse } from "@/lib/api";

const DEFAULT_PAYLOAD = {
  district: "Matale",
  season: "Yala",
  year: new Date().getFullYear(),
  rainfall: 120,
  temperature: 30,
  humidity: 65,
  soil_moisture: 45,
  soil_ph: 6.5,
};

export default function Home() {
  const t = useTranslations();
  const [dashboardData, setDashboardData] = useState<PredictResponse | null>(null);
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

    const fetchDashboardData = async () => {
      setLoading(true);
      setError(null);

      try {
        const response = await predictYield(DEFAULT_PAYLOAD);

        if (mounted) {
          setDashboardData(response);
        }
      } catch (err) {
        if (mounted) {
          setError(
            err instanceof Error
              ? err.message
              : "Unable to load dashboard data."
          );
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };

    fetchDashboardData();

    return () => {
      mounted = false;
    };
  }, []);

  const predictionMap = useMemo(() => {
    if (!dashboardData) {
      return {};
    }

    return {
      [dashboardData.district]: dashboardData.predicted_yield_MT_per_Ha,
    };
  }, [dashboardData]);

  const seasonValue = loading
    ? "Loading..."
    : dashboardData
      ? `${dashboardData.season} ${dashboardData.year}`
      : error
        ? "Unavailable"
        : "--";

  const yieldValue = loading
    ? "Loading..."
    : dashboardData
      ? `${dashboardData.predicted_yield_MT_per_Ha.toFixed(1)} MT/Ha`
      : error
        ? "Unavailable"
        : "--";

  const bestDistrictValue = loading
    ? "Loading..."
    : dashboardData
      ? dashboardData.district
      : error
        ? "Unavailable"
        : "--";

  const weatherValue = loading
    ? "Loading..."
    : dashboardData
      ? dashboardData.confidence
      : error
        ? "Unavailable"
        : "--";

  const yieldTrend = dashboardData
    ? `${dashboardData.confidence_lower.toFixed(1)} - ${dashboardData.confidence_upper.toFixed(1)} MT/Ha`
    : "Checking forecast";

  const seasonTrend = dashboardData
    ? `${dashboardData.model}`
    : "Preparing data";

  const bestDistrictTrend = dashboardData
    ? "Highest predicted potential"
    : "Checking district ranking";

  const weatherTrend = dashboardData
    ? dashboardData.confidence === "High"
      ? "Strong forecast confidence"
      : dashboardData.confidence === "Medium"
        ? "Moderate forecast confidence"
        : "Lower forecast confidence"
    : "Checking conditions";

  return (
    <div className="space-y-10">
      {error && (
        <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Top Section: Intro Left, Map Right */}
      <div className="grid grid-cols-1 gap-8 lg:grid-cols-2">
        {/* Intro Section - Left */}
        <section className="relative overflow-hidden rounded-3xl text-emerald-600 px-8 py-12 bg-white shadow-xl">
          <div className="relative z-10">
            <h1 className="text-4xl font-extrabold tracking-tight md:text-5xl">
              {t("title.home")
                .split("AgriSense")
                .map((part, index, arr) => (
                  <span key={`${part}-${index}`}>
                    {part}
                    {index < arr.length - 1 && (
                      <span className="text-emerald-900">AgriSense</span>
                    )}
                  </span>
                ))}
            </h1>
            <p className="mt-4 text-lg text-emerald-900 text-opacity-90">
              {t("title.description")}
            </p>
            <div className="mt-8 flex flex-wrap gap-4">
              <Link
                href={`/${typeof window !== "undefined" ? window.location.pathname.split("/")[1] : "en"}/predict`}
                className="flex items-center space-x-2 rounded-xl text-white px-6 py-3 font-bold bg-emerald-600 transition-transform hover:scale-105"
              >
                <span>{t("button.start")}</span>
                <ArrowRight size={20} />
              </Link>
            </div>
          </div>
          <div className="absolute -right-20 -top-20 h-64 w-64 rounded-full bg-emerald-500 opacity-20 blur-3xl"></div>
          <div className="absolute -bottom-20 right-20 h-64 w-64 rounded-full bg-lime-400 opacity-20 blur-3xl"></div>
        </section>

        {/* District Map Section - Right */}
        <div>
          <DistrictMap predictions={predictionMap} />
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
            trend={seasonTrend}
            color="bg-emerald-600"
          />
        </motion.div>
        <motion.div variants={item}>
          <StatCard
            label={t("dashboard.expected_yield")}
            value={yieldValue}
            icon={TrendingUp}
            trend={yieldTrend}
            trendType={dashboardData?.confidence === "High" ? "up" : dashboardData?.confidence === "Low" ? "down" : "neutral"}
            color="bg-lime-500"
          />
        </motion.div>
        <motion.div variants={item}>
          <StatCard
            label={t("dashboard.best_district") || "Best District"}
            value={bestDistrictValue}
            icon={MapPin}
            trend={bestDistrictTrend}
            color="bg-emerald-600"
          />
        </motion.div>
        <motion.div variants={item}>
          <StatCard
            label={t("dashboard.weather_summary") || "Weather Summary"}
            value={weatherValue}
            icon={CloudSun}
            trend={weatherTrend}
            trendType={dashboardData?.confidence === "High" ? "up" : dashboardData?.confidence === "Low" ? "down" : "neutral"}
            color="bg-lime-500"
          />
        </motion.div>
      </motion.div>
    </div>
  );
}
