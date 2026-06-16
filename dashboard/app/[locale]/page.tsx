"use client";

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

export default function Home() {
  const t = useTranslations();
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
  return (
    <div className="space-y-10">
      {/* Hero Section */}
      <section className="relative overflow-hidden rounded-3xl bg-emerald-600 px-8 py-12 text-white shadow-xl">
        <div className="relative z-10 max-w-5xl">
          <h1 className="text-4xl font-extrabold tracking-tight md:text-5xl">
            {t("title.home")}
          </h1>
          <p className="mt-4 text-lg text-emerald-50 text-opacity-90">
            {t("title.description")}
          </p>
          <div className="mt-8 flex flex-wrap gap-4">
            <Link
              href={`/${typeof window !== "undefined" ? window.location.pathname.split("/")[1] : "en"}/predict`}
              className="flex items-center space-x-2 rounded-xl bg-white px-6 py-3 font-bold text-emerald-600 transition-transform hover:scale-105"
            >
              <span>{t("button.start")}</span>
              <ArrowRight size={20} />
            </Link>
          </div>
        </div>
        <div className="absolute -right-20 -top-20 h-64 w-64 rounded-full bg-emerald-500 opacity-20 blur-3xl"></div>
        <div className="absolute -bottom-20 right-20 h-64 w-64 rounded-full bg-lime-400 opacity-20 blur-3xl"></div>
      </section>
      <motion.div
        variants={container}
        initial="hidden"
        animate="show"
        className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4"
      >
        <motion.div variants={item}>
          <StatCard
            label={t("dashboard.current_season")}
            value="Yala 2024"
            icon={Calendar}
            trend="Harvest in 3 months"
            color="bg-emerald-600"
          />
        </motion.div>
        <motion.div variants={item}>
          <StatCard
            label={t("dashboard.expected_yield")}
            value="14.2 MT/Ha"
            icon={TrendingUp}
            trend="+5.2% from last year"
            trendType="up"
            color="bg-lime-500"
          />
        </motion.div>
        <motion.div variants={item}>
          <StatCard
            label={t("dashboard.best_district") || "Best District"}
            value="Matale"
            icon={MapPin}
            trend="Highest potential"
            color="bg-emerald-600"
          />
        </motion.div>
        <motion.div variants={item}>
          <StatCard
            label={t("dashboard.weather_summary") || "Weather Summary"}
            value="Favorable"
            icon={CloudSun}
            trend="Moderate rainfall"
            trendType="neutral"
            color="bg-lime-500"
          />
        </motion.div>
      </motion.div>
      <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
        {/* Map Section */}
        <div className="lg:col-span-2">
          <DistrictMap />
        </div>
      </div>
    </div>
  );
}
