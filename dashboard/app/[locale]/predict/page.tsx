"use client";

import { useState } from "react";
import { Sprout, CheckCircle2, TrendingUp, History, Info } from "lucide-react";

import { useTranslations, useLocale } from "next-intl";

import { predictYield, type PredictResponse } from "@/lib/api";
import { clsx } from "clsx";

export default function PredictPage() {
  const t = useTranslations();
  const locale = useLocale();

  const [loading, setLoading] = useState(false);

  const [result, setResult] = useState<PredictResponse | null>(null);

  const [formData, setFormData] = useState({
    district: "Matale",
    season: "Yala",
    year: 2024,
    rainfall: 120,
    temperature: 30,
    humidity: 65,
    solar: 18,
    ndvi: 0.55,
    evi: 0.35,
    soil_ph: 6.5,
    clay: 30,
    sand: 45,
    organic_carbon: 1.8,
  });

  const districts = [
    { value: "matale", label: t("districts.matale") },
    { value: "anuradhapura", label: t("districts.anuradhapura") },
    { value: "polonnaruwa", label: t("districts.polonnaruwa") },
    { value: "kurunegala", label: t("districts.kurunegala") },
  ];
  const seasons = ["yala", "maha"].map((s) => ({
    value: s,
    label: t(`seasons.${s}`),
  }));

  const currentYear = new Date().getFullYear();

  const years = [
    currentYear - 2,
    currentYear - 1,
    currentYear,
    currentYear + 1,
    currentYear + 2,
  ];

  // =========================
  // Handle Form Input Changes
  // =========================
  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>,
  ) => {
    const { name, value } = e.target;

    setFormData((prev) => ({
      ...prev,
      [name]: [
        "rainfall",
        "temperature",
        "humidity",
        "solar",
        "ndvi",
        "evi",
        "soil_ph",
        "clay",
        "sand",
        "organic_carbon",
        "year",
      ].includes(name)
        ? Number(value)
        : value,
    }));
  };

  // =========================
  // Predict Yield
  // =========================
  const handlePredict = async () => {
    setLoading(true);

    try {
      const payload = {
        district: formData.district,
        season: formData.season,
        year: formData.year,

        // Map UI fields to the model's real feature names. Remaining features
        // are auto-filled from /context inside predictYield().
        season_total_rainfall: formData.rainfall,
        season_avg_temp: formData.temperature,
        season_avg_humidity: formData.humidity,
        season_avg_solar_rad: formData.solar,
        season_mean_ndvi: formData.ndvi,
        season_mean_evi: formData.evi,
        soil_ph: formData.soil_ph,
        clay_pct: formData.clay,
        sand_pct: formData.sand,
        organic_carbon: formData.organic_carbon,
      };

      const res = await predictYield(payload);

      setResult(res);

      localStorage.setItem("last_prediction", JSON.stringify(res));
    } catch (error) {
      console.error("Prediction failed:", error);

      alert(t("predict.error"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col space-y-2">
        <h1 className="text-3xl font-bold tracking-tight text-slate-900">
          {t("predict.title")}
        </h1>

        <p className="text-slate-500">{t("predict.subtitle")}</p>
      </div>

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-2">
        {/* ========================= */}
        {/* Left Side - Input Form */}
        {/* ========================= */}
        <section className="rounded-2xl border bg-white p-8 shadow-md">
          <form className="space-y-6">
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
              {/* District */}
              <div className="space-y-2">
                <label className="text-sm font-bold text-slate-700">
                  {t("form.district")}
                </label>

                <select
                  name="district"
                  value={formData.district}
                  onChange={handleInputChange}
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3"
                >
                  {districts.map((d) => (
                    <option key={d.value} value={d.value}>
                      {d.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Season */}
              <div className="space-y-2">
                <label className="text-sm font-bold text-slate-700">
                  {t("form.season")}
                </label>

                <select
                  name="season"
                  value={formData.season}
                  onChange={handleInputChange}
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3"
                >
                  {seasons.map((season) => (
                    <option key={season.value} value={season.value}>
                      {season.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Year */}
              <div className="space-y-2">
                <label className="text-sm font-bold text-slate-700">
                  {t("form.year")}
                </label>

                <select
                  name="year"
                  value={formData.year}
                  onChange={handleInputChange}
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3"
                >
                  {years.map((year) => (
                    <option key={year} value={year}>
                      {year}
                    </option>
                  ))}
                </select>
              </div>

              {/* Rainfall */}
              <div className="space-y-2">
                <label className="text-sm font-bold text-slate-700">
                  {t("form.rainfall")}
                </label>

                <input
                  type="number"
                  name="rainfall"
                  value={formData.rainfall}
                  onChange={handleInputChange}
                  required
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3"
                />
              </div>

              {/* Temperature */}
              <div className="space-y-2">
                <label className="text-sm font-bold text-slate-700">
                  {t("form.temperature")}
                </label>

                <input
                  type="number"
                  name="temperature"
                  value={formData.temperature}
                  onChange={handleInputChange}
                  required
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3"
                />
              </div>

              {/* Humidity */}
              <div className="space-y-2">
                <label className="text-sm font-bold text-slate-700">
                  {t("form.humidity")}
                </label>

                <input
                  type="number"
                  name="humidity"
                  value={formData.humidity}
                  onChange={handleInputChange}
                  required
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3"
                />
              </div>

              {/* Solar Radiation */}
              <div className="space-y-2">
                <label className="text-sm font-bold text-slate-700">
                  {t("form.solarRad")}
                </label>

                <input
                  type="number"
                  step="0.1"
                  name="solar"
                  value={formData.solar}
                  onChange={handleInputChange}
                  required
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3"
                />
              </div>

              {/* NDVI (vegetation index — top predictor) */}
              <div className="space-y-2">
                <label className="text-sm font-bold text-slate-700">
                  {t("form.ndvi")}
                </label>

                <input
                  type="number"
                  step="0.01"
                  name="ndvi"
                  value={formData.ndvi}
                  onChange={handleInputChange}
                  required
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3"
                />
              </div>

              {/* EVI (vegetation index) */}
              <div className="space-y-2">
                <label className="text-sm font-bold text-slate-700">
                  {t("form.evi")}
                </label>

                <input
                  type="number"
                  step="0.01"
                  name="evi"
                  value={formData.evi}
                  onChange={handleInputChange}
                  required
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3"
                />
              </div>

              {/* Clay % */}
              <div className="space-y-2">
                <label className="text-sm font-bold text-slate-700">
                  {t("form.clay")}
                </label>

                <input
                  type="number"
                  step="0.1"
                  name="clay"
                  value={formData.clay}
                  onChange={handleInputChange}
                  required
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3"
                />
              </div>

              {/* Sand % */}
              <div className="space-y-2">
                <label className="text-sm font-bold text-slate-700">
                  {t("form.sand")}
                </label>

                <input
                  type="number"
                  step="0.1"
                  name="sand"
                  value={formData.sand}
                  onChange={handleInputChange}
                  required
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3"
                />
              </div>

              {/* Organic Carbon */}
              <div className="space-y-2">
                <label className="text-sm font-bold text-slate-700">
                  {t("form.organicCarbon")}
                </label>

                <input
                  type="number"
                  step="0.1"
                  name="organic_carbon"
                  value={formData.organic_carbon}
                  onChange={handleInputChange}
                  required
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3"
                />
              </div>

              {/* Soil pH */}
              <div className="space-y-2">
                <label className="text-sm font-bold text-slate-700">
                  {t("form.soilPh")}
                </label>

                <input
                  type="number"
                  step="0.1"
                  name="soil_ph"
                  value={formData.soil_ph}
                  onChange={handleInputChange}
                  required
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3"
                />
              </div>
            </div>

            {/* Submit Button */}
            <button
              type="button"
              onClick={handlePredict}
              disabled={loading}
              className="flex w-full items-center justify-center space-x-2 rounded-2xl bg-emerald-600 py-4 text-lg font-bold text-white shadow-lg transition-all hover:bg-emerald-700 disabled:opacity-70"
            >
              {loading ? (
                <div className="h-6 w-6 animate-spin rounded-full border-2 border-white border-t-transparent"></div>
              ) : (
                <>
                  <Sprout size={24} />
                  <span>{t("button.predict")}</span>
                </>
              )}
            </button>
          </form>
        </section>

        {/* ========================= */}
        {/* Right Side - Results */}
        {/* ========================= */}
        <section className="space-y-6">
          {!result ? (
            <div className="flex h-full min-h-[400px] flex-col items-center justify-center rounded-2xl border-2 border-dashed border-slate-200 bg-slate-50 p-8 text-center">
              <div className="rounded-full bg-slate-100 p-4">
                <Info size={40} className="text-slate-400" />
              </div>

              <h3 className="mt-4 text-xl font-bold text-slate-900">
                {t("predict.waiting")}
              </h3>

              <p className="mt-2 max-w-xs text-slate-500">
                {t("predict.waitingDescription")}
              </p>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Prediction Card */}
              <div className="overflow-hidden rounded-3xl border border-emerald-100 bg-emerald-50 p-8 shadow-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-bold uppercase tracking-wider text-emerald-600">
                      {t("predict.expectedYield")}
                    </p>

                    <h2 className="mt-2 text-5xl font-black text-emerald-900">
                      {result.predicted_yield_MT_per_Ha}

                      <span className="ml-2 text-2xl font-normal">MT/Ha</span>
                    </h2>
                  </div>

                  <div className="rounded-2xl bg-emerald-600 p-4 text-white shadow-md">
                    <TrendingUp size={32} />
                  </div>
                </div>
              </div>

              {/* Confidence */}
              <div className="flex items-center justify-between rounded-2xl border bg-white p-6 shadow-md">
                <div className="flex items-center space-x-3">
                  <div
                    className={clsx(
                      "h-4 w-4 rounded-full",
                      result.confidence === "High"
                        ? "bg-emerald-500"
                        : result.confidence === "Medium"
                          ? "bg-amber-500"
                          : "bg-red-500",
                    )}
                  />

                  <span className="text-lg font-bold text-slate-900">
                    {result.confidence} {t("predict.confidence")}
                  </span>
                </div>

                <div className="text-sm text-slate-500">
                  Range: {result.confidence_lower} - {result.confidence_upper}{" "}
                  MT/Ha
                </div>
              </div>

              {/* Stats */}
              <div className="grid grid-cols-2 gap-4">
                <div className="rounded-2xl border bg-white p-5 shadow-sm">
                  <p className="text-xs font-bold text-slate-500">
                    {t("predict.previousSeason")}
                  </p>

                  <div className="mt-2 flex items-center space-x-2">
                    <History size={18} className="text-slate-400" />

                    <span className="text-xl font-bold text-slate-900">
                      13.5 MT/Ha
                    </span>
                  </div>
                </div>

                <div className="rounded-2xl border bg-white p-5 shadow-sm">
                  <p className="text-xs font-bold text-slate-500">
                    {t("predict.change")}
                  </p>

                  <div className="mt-2 flex items-center space-x-2">
                    <TrendingUp size={18} className="text-emerald-500" />

                    <span className="text-xl font-bold text-emerald-600">
                      +5.2%
                    </span>
                  </div>
                </div>
              </div>

              {/* Success Card */}
              <div className="rounded-2xl bg-slate-900 p-6 text-white shadow-xl">
                <h4 className="flex items-center space-x-2 font-bold">
                  <CheckCircle2 size={18} className="text-emerald-400" />

                  <span>{t("predict.success")}</span>
                </h4>

                <p className="mt-2 text-sm text-slate-300">
                  {t("predict.successDescription")}
                </p>

                <a
                  href={`/${locale}/explain`}
                  className="mt-4 inline-flex items-center space-x-2 font-bold text-emerald-400 hover:text-emerald-300"
                >
                  <span>{t("predict.whyPrediction")}</span>

                  <ArrowRight size={16} />
                </a>
              </div>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}

function ArrowRight({ size }: { size: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M5 12h14M12 5l7 7-7 7" />
    </svg>
  );
}
