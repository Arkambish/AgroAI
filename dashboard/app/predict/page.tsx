"use client";

import { useState } from "react";
import { Sprout, CheckCircle2, TrendingUp, History, Info } from "lucide-react";

import { predictYield, type PredictResponse } from "@/lib/api";
import { clsx } from "clsx";

export default function PredictPage() {
  const [loading, setLoading] = useState(false);

  const [result, setResult] = useState<PredictResponse | null>(null);

  const [formData, setFormData] = useState({
    district: "Matale",
    season: "Yala",
    year: 2024,
    rainfall: 120,
    temperature: 30,
    humidity: 65,
    soil_moisture: 45,
    soil_ph: 6.5,
  });

  const districts = ["Matale", "Anuradhapura", "Polonnaruwa", "Jaffna"];

  const seasons = ["Yala", "Maha"];

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
        "soil_moisture",
        "soil_ph",
        "year",
      ].includes(name)
        ? Number(value)
        : value,
    }));
  };

  // =========================
  // Predict Yield
  // =========================
  const handlePredict = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      // Backend payload mapping
      const payload = {
        district: formData.district,
        season: formData.season,
        year: formData.year,

        rainfall: formData.rainfall,
        temperature: formData.temperature,
        humidity: formData.humidity,
        soil_moisture: formData.soil_moisture,
        soil_ph: formData.soil_ph,

        // ML model aliases
        season_total_rainfall: formData.rainfall,
        season_avg_temp: formData.temperature,
        season_avg_humidity: formData.humidity,
      };

      // API / Mock call
      const res = await predictYield(payload);

      setResult(res);

      // Save for Explain page
      localStorage.setItem("last_prediction", JSON.stringify(res));
    } catch (error) {
      console.error("Prediction failed:", error);

      alert("Prediction failed. Backend may not be running.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col space-y-2">
        <h1 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
          Predict Big Onion Yield
        </h1>

        <p className="text-slate-500 dark:text-slate-400">
          Enter agricultural data to get an AI-powered yield prediction.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-2">
        {/* ========================= */}
        {/* Left Side - Input Form */}
        {/* ========================= */}
        <section className="rounded-2xl border bg-white p-8 shadow-md dark:bg-slate-900">
          <form className="space-y-6">
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
              {/* District */}
              <div className="space-y-2">
                <label className="text-sm font-bold text-slate-700 dark:text-slate-300">
                  District
                </label>

                <select
                  name="district"
                  value={formData.district}
                  onChange={handleInputChange}
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 dark:border-slate-700 dark:bg-slate-800"
                >
                  {districts.map((district) => (
                    <option key={district} value={district}>
                      {district}
                    </option>
                  ))}
                </select>
              </div>

              {/* Season */}
              <div className="space-y-2">
                <label className="text-sm font-bold text-slate-700 dark:text-slate-300">
                  Season
                </label>

                <select
                  name="season"
                  value={formData.season}
                  onChange={handleInputChange}
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 dark:border-slate-700 dark:bg-slate-800"
                >
                  {seasons.map((season) => (
                    <option key={season} value={season}>
                      {season}
                    </option>
                  ))}
                </select>
              </div>

              {/* Year */}
              <div className="space-y-2">
                <label className="text-sm font-bold text-slate-700 dark:text-slate-300">
                  Year
                </label>

                <select
                  name="year"
                  value={formData.year}
                  onChange={handleInputChange}
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 dark:border-slate-700 dark:bg-slate-800"
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
                <label className="text-sm font-bold text-slate-700 dark:text-slate-300">
                  Rainfall (mm)
                </label>

                <input
                  type="number"
                  name="rainfall"
                  value={formData.rainfall}
                  onChange={handleInputChange}
                  required
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 dark:border-slate-700 dark:bg-slate-800"
                />
              </div>

              {/* Temperature */}
              <div className="space-y-2">
                <label className="text-sm font-bold text-slate-700 dark:text-slate-300">
                  Temperature (°C)
                </label>

                <input
                  type="number"
                  name="temperature"
                  value={formData.temperature}
                  onChange={handleInputChange}
                  required
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 dark:border-slate-700 dark:bg-slate-800"
                />
              </div>

              {/* Humidity */}
              <div className="space-y-2">
                <label className="text-sm font-bold text-slate-700 dark:text-slate-300">
                  Humidity (%)
                </label>

                <input
                  type="number"
                  name="humidity"
                  value={formData.humidity}
                  onChange={handleInputChange}
                  required
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 dark:border-slate-700 dark:bg-slate-800"
                />
              </div>

              {/* Soil Moisture */}
              <div className="space-y-2">
                <label className="text-sm font-bold text-slate-700 dark:text-slate-300">
                  Soil Moisture (%)
                </label>

                <input
                  type="number"
                  name="soil_moisture"
                  value={formData.soil_moisture}
                  onChange={handleInputChange}
                  required
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 dark:border-slate-700 dark:bg-slate-800"
                />
              </div>

              {/* Soil pH */}
              <div className="space-y-2">
                <label className="text-sm font-bold text-slate-700 dark:text-slate-300">
                  Soil pH
                </label>

                <input
                  type="number"
                  step="0.1"
                  name="soil_ph"
                  value={formData.soil_ph}
                  onChange={handleInputChange}
                  required
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 dark:border-slate-700 dark:bg-slate-800"
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
                  <span>Predict Yield</span>
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
            <div className="flex h-full min-h-[400px] flex-col items-center justify-center rounded-2xl border-2 border-dashed border-slate-200 bg-slate-50 p-8 text-center dark:border-slate-800 dark:bg-slate-900/50">
              <div className="rounded-full bg-slate-100 p-4 dark:bg-slate-800">
                <Info size={40} className="text-slate-400" />
              </div>

              <h3 className="mt-4 text-xl font-bold text-slate-900 dark:text-white">
                Waiting for Prediction
              </h3>

              <p className="mt-2 max-w-xs text-slate-500 dark:text-slate-400">
                Fill out the form and click Predict Yield to see the AI
                analysis.
              </p>
            </div>
          ) : (
            result && (
              <div className="space-y-6">
                {/* Prediction Card */}
                <div className="overflow-hidden rounded-3xl border border-emerald-100 bg-emerald-50 p-8 shadow-lg dark:border-emerald-900/30 dark:bg-emerald-900/20">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-bold uppercase tracking-wider text-emerald-600 dark:text-emerald-400">
                        Expected Yield
                      </p>

                      <h2 className="mt-2 text-5xl font-black text-emerald-900 dark:text-white">
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
                <div className="flex items-center justify-between rounded-2xl border bg-white p-6 shadow-md dark:bg-slate-900">
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
                    <span className="text-lg font-bold text-slate-900 dark:text-white">
                      {result.confidence} Confidence
                    </span>
                  </div>
                  <div className="text-sm text-slate-500 dark:text-slate-400">
                    Range: {result.confidence_lower} - {result.confidence_upper}
                    MT/Ha
                  </div>
                </div>
                {/* Stats */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="rounded-2xl border bg-white p-5 shadow-sm dark:bg-slate-900">
                    <p className="text-xs font-bold text-slate-500 dark:text-slate-400">
                      PREVIOUS SEASON
                    </p>
                    <div className="mt-2 flex items-center space-x-2">
                      <History size={18} className="text-slate-400" />
                      <span className="text-xl font-bold text-slate-900 dark:text-white">
                        13.5 MT/Ha
                      </span>
                    </div>
                  </div>
                  <div className="rounded-2xl border bg-white p-5 shadow-sm dark:bg-slate-900">
                    <p className="text-xs font-bold text-slate-500 dark:text-slate-400">
                      CHANGE
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
                <div className="rounded-2xl bg-slate-900 p-6 text-white shadow-xl dark:bg-emerald-950">
                  <h4 className="flex items-center space-x-2 font-bold">
                    <CheckCircle2 size={18} className="text-emerald-400" />
                    <span>Prediction Successful</span>
                  </h4>
                  <p className="mt-2 text-sm text-slate-300">
                    We analyzed multiple agricultural factors to generate this
                    prediction.
                  </p>
                  <a
                    href="/explain"
                    className="mt-4 inline-flex items-center space-x-2 font-bold text-emerald-400 hover:text-emerald-300"
                  >
                    <span>Why this prediction?</span>
                    <ArrowRight size={16} />
                  </a>
                </div>
              </div>
            )
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
