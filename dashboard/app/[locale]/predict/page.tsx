"use client";

import { useState, useEffect } from "react";
import {
  Sprout,
  CheckCircle2,
  TrendingUp,
  History,
  Info,
  MapPin,
  CloudSun,
  Leaf,
  FlaskConical,
  Sparkles,
  RefreshCw,
  ArrowRight,
} from "lucide-react";

import { useTranslations, useLocale } from "next-intl";

import { predictYield, getContext, type PredictResponse } from "@/lib/api";
import { clsx } from "clsx";

export default function PredictPage() {
  const t = useTranslations();
  const locale = useLocale();

  const [loading, setLoading] = useState(false);
  const [contextLoading, setContextLoading] = useState(false);
  const [contextSource, setContextSource] = useState<string | null>(null);
  const [result, setResult] = useState<PredictResponse | null>(null);

  const [formData, setFormData] = useState({
    district: "Matale",
    season: "Yala",
    year: new Date().getFullYear(),
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
    { value: "Matale", label: "Matale" },
    { value: "Anuradhapura", label: "Anuradhapura" },
    { value: "Polonnaruwa", label: "Polonnaruwa" },
    { value: "Kurunegala", label: "Kurunegala" },
  ];

  const seasons = [
    { value: "Yala", label: "Yala" },
    { value: "Maha", label: "Maha" },
  ];

  const currentYear = new Date().getFullYear();
  const years = [
    currentYear - 2,
    currentYear - 1,
    currentYear,
    currentYear + 1,
    currentYear + 2,
  ];

  // Auto-fill form values from historical /context API when Location changes
  useEffect(() => {
    let active = true;

    const fetchDistrictContext = async () => {
      setContextLoading(true);
      try {
        const ctx = await getContext(
          formData.district,
          formData.season,
          formData.year
        );

        if (active && ctx) {
          setContextSource(ctx.source || "historical_mean");
          setFormData((prev) => ({
            ...prev,
            rainfall:
              ctx.season_total_rainfall !== undefined
                ? Number(ctx.season_total_rainfall.toFixed(1))
                : prev.rainfall,
            temperature:
              ctx.season_avg_temp !== undefined
                ? Number(ctx.season_avg_temp.toFixed(1))
                : prev.temperature,
            humidity:
              ctx.season_avg_humidity !== undefined
                ? Number(ctx.season_avg_humidity.toFixed(1))
                : prev.humidity,
            solar:
              ctx.season_avg_solar_rad !== undefined
                ? Number(ctx.season_avg_solar_rad.toFixed(1))
                : prev.solar,
            ndvi:
              ctx.season_mean_ndvi !== undefined
                ? Number(ctx.season_mean_ndvi.toFixed(2))
                : prev.ndvi,
            evi:
              ctx.season_mean_evi !== undefined
                ? Number(ctx.season_mean_evi.toFixed(2))
                : prev.evi,
            soil_ph:
              ctx.soil_ph !== undefined
                ? Number(ctx.soil_ph.toFixed(1))
                : prev.soil_ph,
            clay:
              ctx.clay_pct !== undefined
                ? Number(ctx.clay_pct.toFixed(1))
                : prev.clay,
            sand:
              ctx.sand_pct !== undefined
                ? Number(ctx.sand_pct.toFixed(1))
                : prev.sand,
            organic_carbon:
              ctx.organic_carbon !== undefined
                ? Number(ctx.organic_carbon.toFixed(1))
                : prev.organic_carbon,
          }));
        }
      } catch {
        if (active) setContextSource(null);
      } finally {
        if (active) setContextLoading(false);
      }
    };

    fetchDistrictContext();

    return () => {
      active = false;
    };
  }, [formData.district, formData.season, formData.year]);

  // Handle Form Input Changes
  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
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

  // Predict Yield
  const handlePredict = async () => {
    setLoading(true);

    try {
      const payload = {
        district: formData.district,
        season: formData.season,
        year: formData.year,

        // Map UI fields to the model's feature names
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

      if (typeof window !== "undefined") {
        localStorage.setItem("last_prediction", JSON.stringify(res));
      }
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
        <div className="inline-flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-emerald-600">
          <Sparkles size={16} />
          <span>AI Decision Support</span>
        </div>
        <h1 className="text-3xl font-extrabold tracking-tight text-slate-900 md:text-4xl">
          {t("predict.title")}
        </h1>
        <p className="text-slate-500 max-w-2xl">{t("predict.subtitle")}</p>
      </div>

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
        {/* Left Side - Organized 4-Section Form */}
        <section className="lg:col-span-7 space-y-6">
          <form className="space-y-6">
            {/* SECTION 1: LOCATION & SEASON */}
            <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm space-y-4">
              <div className="flex items-center justify-between border-b pb-3">
                <div className="flex items-center space-x-2">
                  <MapPin className="text-emerald-600" size={20} />
                  <h3 className="text-lg font-bold text-slate-900">
                    1. Location & Timing
                  </h3>
                </div>
                {contextLoading ? (
                  <div className="flex items-center space-x-1 text-xs text-emerald-600 font-semibold animate-pulse">
                    <RefreshCw size={12} className="animate-spin" />
                    <span>Auto-filling historical context...</span>
                  </div>
                ) : contextSource ? (
                  <span className="rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-semibold text-emerald-800">
                    Auto-Filled ({contextSource === "exact" ? "Exact Year" : "Historical Mean"})
                  </span>
                ) : null}
              </div>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                {/* District */}
                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-slate-700">
                    District
                  </label>
                  <select
                    name="district"
                    value={formData.district}
                    onChange={handleInputChange}
                    className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm font-semibold text-slate-800 focus:bg-white focus:ring-2 focus:ring-emerald-500 outline-none"
                  >
                    {districts.map((d) => (
                      <option key={d.value} value={d.value}>
                        {d.label}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Season */}
                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-slate-700">
                    Cultivation Season
                  </label>
                  <select
                    name="season"
                    value={formData.season}
                    onChange={handleInputChange}
                    className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm font-semibold text-slate-800 focus:bg-white focus:ring-2 focus:ring-emerald-500 outline-none"
                  >
                    {seasons.map((s) => (
                      <option key={s.value} value={s.value}>
                        {s.label}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Year */}
                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-slate-700">
                    Target Year
                  </label>
                  <select
                    name="year"
                    value={formData.year}
                    onChange={handleInputChange}
                    className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm font-semibold text-slate-800 focus:bg-white focus:ring-2 focus:ring-emerald-500 outline-none"
                  >
                    {years.map((y) => (
                      <option key={y} value={y}>
                        {y}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>

            {/* SECTION 2: WEATHER INPUTS */}
            <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm space-y-4">
              <div className="flex items-center space-x-2 border-b pb-3">
                <CloudSun className="text-sky-600" size={20} />
                <h3 className="text-lg font-bold text-slate-900">
                  2. Weather Conditions
                </h3>
              </div>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                {/* Total Rainfall */}
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <label className="text-xs font-bold text-slate-700">
                      Total Season Rainfall (mm)
                    </label>
                    <span className="text-[11px] text-slate-400">0 - 2000 mm</span>
                  </div>
                  <input
                    type="number"
                    min={0}
                    max={2000}
                    step={1}
                    name="rainfall"
                    value={formData.rainfall}
                    onChange={handleInputChange}
                    className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm font-semibold text-slate-800 focus:bg-white focus:ring-2 focus:ring-emerald-500 outline-none"
                  />
                </div>

                {/* Temperature */}
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <label className="text-xs font-bold text-slate-700">
                      Average Temp (°C)
                    </label>
                    <span className="text-[11px] text-slate-400">10 - 50 °C</span>
                  </div>
                  <input
                    type="number"
                    min={10}
                    max={50}
                    step={0.1}
                    name="temperature"
                    value={formData.temperature}
                    onChange={handleInputChange}
                    className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm font-semibold text-slate-800 focus:bg-white focus:ring-2 focus:ring-emerald-500 outline-none"
                  />
                </div>

                {/* Humidity */}
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <label className="text-xs font-bold text-slate-700">
                      Relative Humidity (%)
                    </label>
                    <span className="text-[11px] text-slate-400">0 - 100 %</span>
                  </div>
                  <input
                    type="number"
                    min={0}
                    max={100}
                    step={1}
                    name="humidity"
                    value={formData.humidity}
                    onChange={handleInputChange}
                    className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm font-semibold text-slate-800 focus:bg-white focus:ring-2 focus:ring-emerald-500 outline-none"
                  />
                </div>

                {/* Solar Radiation */}
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <label className="text-xs font-bold text-slate-700">
                      Solar Rad (MJ/m²)
                    </label>
                    <span className="text-[11px] text-slate-400">0 - 40 MJ/m²</span>
                  </div>
                  <input
                    type="number"
                    min={0}
                    max={40}
                    step={0.1}
                    name="solar"
                    value={formData.solar}
                    onChange={handleInputChange}
                    className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm font-semibold text-slate-800 focus:bg-white focus:ring-2 focus:ring-emerald-500 outline-none"
                  />
                </div>
              </div>
            </div>

            {/* SECTION 3: VEGETATION INPUTS */}
            <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm space-y-4">
              <div className="flex items-center space-x-2 border-b pb-3">
                <Leaf className="text-emerald-600" size={20} />
                <h3 className="text-lg font-bold text-slate-900">
                  3. Satellite Vegetation Indices
                </h3>
              </div>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                {/* NDVI */}
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <label className="text-xs font-bold text-slate-700">
                      Mean NDVI (Greenness Index)
                    </label>
                    <span className="text-[11px] text-slate-400">0.0 to 1.0</span>
                  </div>
                  <input
                    type="number"
                    min={-1}
                    max={1}
                    step={0.01}
                    name="ndvi"
                    value={formData.ndvi}
                    onChange={handleInputChange}
                    className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm font-semibold text-slate-800 focus:bg-white focus:ring-2 focus:ring-emerald-500 outline-none"
                  />
                  <p className="text-[11px] text-slate-400">
                    Top predictor indicator for crop canopy density.
                  </p>
                </div>

                {/* EVI */}
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <label className="text-xs font-bold text-slate-700">
                      Mean EVI (Enhanced Vegetation)
                    </label>
                    <span className="text-[11px] text-slate-400">0.0 to 1.0</span>
                  </div>
                  <input
                    type="number"
                    min={-1}
                    max={1}
                    step={0.01}
                    name="evi"
                    value={formData.evi}
                    onChange={handleInputChange}
                    className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm font-semibold text-slate-800 focus:bg-white focus:ring-2 focus:ring-emerald-500 outline-none"
                  />
                  <p className="text-[11px] text-slate-400">
                    Adjusts for atmospheric and soil background interference.
                  </p>
                </div>
              </div>
            </div>

            {/* SECTION 4: SOIL INPUTS */}
            <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm space-y-4">
              <div className="flex items-center space-x-2 border-b pb-3">
                <FlaskConical className="text-amber-600" size={20} />
                <h3 className="text-lg font-bold text-slate-900">
                  4. Soil Properties
                </h3>
              </div>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                {/* Soil pH */}
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <label className="text-xs font-bold text-slate-700">
                      Soil pH
                    </label>
                    <span className="text-[11px] text-slate-400">0.0 - 14.0 (Opt: 6.0-7.0)</span>
                  </div>
                  <input
                    type="number"
                    min={0}
                    max={14}
                    step={0.1}
                    name="soil_ph"
                    value={formData.soil_ph}
                    onChange={handleInputChange}
                    className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm font-semibold text-slate-800 focus:bg-white focus:ring-2 focus:ring-emerald-500 outline-none"
                  />
                </div>

                {/* Clay % */}
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <label className="text-xs font-bold text-slate-700">
                      Clay Content (%)
                    </label>
                    <span className="text-[11px] text-slate-400">0 - 100 %</span>
                  </div>
                  <input
                    type="number"
                    min={0}
                    max={100}
                    step={0.1}
                    name="clay"
                    value={formData.clay}
                    onChange={handleInputChange}
                    className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm font-semibold text-slate-800 focus:bg-white focus:ring-2 focus:ring-emerald-500 outline-none"
                  />
                </div>

                {/* Sand % */}
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <label className="text-xs font-bold text-slate-700">
                      Sand Content (%)
                    </label>
                    <span className="text-[11px] text-slate-400">0 - 100 %</span>
                  </div>
                  <input
                    type="number"
                    min={0}
                    max={100}
                    step={0.1}
                    name="sand"
                    value={formData.sand}
                    onChange={handleInputChange}
                    className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm font-semibold text-slate-800 focus:bg-white focus:ring-2 focus:ring-emerald-500 outline-none"
                  />
                </div>

                {/* Organic Carbon */}
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <label className="text-xs font-bold text-slate-700">
                      Organic Carbon (%)
                    </label>
                    <span className="text-[11px] text-slate-400">0 - 20 %</span>
                  </div>
                  <input
                    type="number"
                    min={0}
                    max={20}
                    step={0.1}
                    name="organic_carbon"
                    value={formData.organic_carbon}
                    onChange={handleInputChange}
                    className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm font-semibold text-slate-800 focus:bg-white focus:ring-2 focus:ring-emerald-500 outline-none"
                  />
                </div>
              </div>
            </div>

            {/* Submit Button */}
            <button
              type="button"
              onClick={handlePredict}
              disabled={loading}
              className="flex w-full items-center justify-center space-x-2 rounded-2xl bg-emerald-600 py-4 text-lg font-bold text-white shadow-lg transition-all hover:bg-emerald-700 active:scale-[0.99] disabled:opacity-70"
            >
              {loading ? (
                <div className="h-6 w-6 animate-spin rounded-full border-2 border-white border-t-transparent" />
              ) : (
                <>
                  <Sprout size={24} />
                  <span>{t("button.predict")}</span>
                </>
              )}
            </button>
          </form>
        </section>

        {/* Right Side - Prediction AI Results */}
        <section className="lg:col-span-5 space-y-6">
          {!result ? (
            <div className="flex h-full min-h-[420px] flex-col items-center justify-center rounded-3xl border-2 border-dashed border-slate-200 bg-slate-50 p-8 text-center">
              <div className="rounded-2xl bg-emerald-100/60 p-4 text-emerald-700 mb-4">
                <Info size={36} />
              </div>
              <h3 className="text-xl font-bold text-slate-900">
                {t("predict.waiting")}
              </h3>
              <p className="mt-2 max-w-xs text-sm text-slate-500">
                {t("predict.waitingDescription")}
              </p>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Primary Prediction Card */}
              <div className="overflow-hidden rounded-3xl border border-emerald-200 bg-gradient-to-br from-emerald-50 via-white to-emerald-100/60 p-8 shadow-xl">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs font-bold uppercase tracking-wider text-emerald-700">
                      {t("predict.expectedYield")}
                    </p>

                    <h2 className="mt-2 text-5xl font-black text-emerald-950">
                      {result.predicted_yield_MT_per_Ha.toFixed(2)}
                      <span className="ml-2 text-xl font-medium text-emerald-800">
                        MT/Ha
                      </span>
                    </h2>
                  </div>

                  <div className="rounded-2xl bg-emerald-600 p-4 text-white shadow-lg">
                    <TrendingUp size={32} />
                  </div>
                </div>

                <div className="mt-6 pt-4 border-t border-emerald-100 flex items-center justify-between text-xs font-semibold text-emerald-900">
                  <span>Target Zone: {result.district} ({result.season} {result.year})</span>
                  <span>Model: {result.model || "XGBoost"}</span>
                </div>
              </div>

              {/* Confidence Indicator */}
              <div className="flex items-center justify-between rounded-2xl border border-slate-200 bg-white p-5 shadow-md">
                <div className="flex items-center space-x-3">
                  <div
                    className={clsx(
                      "h-3.5 w-3.5 rounded-full shadow-sm",
                      result.confidence === "High"
                        ? "bg-emerald-500"
                        : result.confidence === "Medium"
                        ? "bg-amber-500"
                        : "bg-red-500"
                    )}
                  />
                  <span className="text-base font-bold text-slate-900">
                    {result.confidence} Confidence
                  </span>
                </div>

                <div className="text-xs font-semibold text-slate-500 bg-slate-100 px-3 py-1 rounded-lg">
                  Range: {result.confidence_lower} – {result.confidence_upper}{" "}
                  MT/Ha
                </div>
              </div>

              {/* Stats Grid */}
              <div className="grid grid-cols-2 gap-4">
                <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                  <p className="text-xs font-bold text-slate-500">
                    Historical Benchmark
                  </p>
                  <div className="mt-2 flex items-center space-x-2">
                    <History size={18} className="text-slate-400" />
                    <span className="text-lg font-bold text-slate-900">
                      13.5 MT/Ha
                    </span>
                  </div>
                </div>

                <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                  <p className="text-xs font-bold text-slate-500">
                    Expected Variance
                  </p>
                  <div className="mt-2 flex items-center space-x-2">
                    <TrendingUp size={18} className="text-emerald-500" />
                    <span className="text-lg font-bold text-emerald-600">
                      +{((result.predicted_yield_MT_per_Ha - 13.5) / 13.5 * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>
              </div>

              {/* Success Callout & Explanation Link */}
              <div className="rounded-2xl bg-slate-900 p-6 text-white shadow-xl space-y-3">
                <h4 className="flex items-center space-x-2 font-bold text-emerald-400">
                  <CheckCircle2 size={20} />
                  <span>{t("predict.success")}</span>
                </h4>

                <p className="text-xs text-slate-300 leading-relaxed">
                  {t("predict.successDescription")}
                </p>

                <a
                  href={`/${locale}/explain`}
                  className="mt-2 inline-flex items-center space-x-2 text-sm font-bold text-emerald-400 hover:text-emerald-300 transition-colors"
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

