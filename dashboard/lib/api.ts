import axios from "axios";
import { predictYieldMock } from "./sample-api";

/** One SHAP factor, ready to render. Defined here (not in the explain page) so
 * lib/ never imports from app/. */
export type ExplanationItem = {
  /** Translation key suffix under `explain.features.*` */
  name: string;
  /** The raw model feature this came from */
  feature: string;
  impact: "Positive" | "Negative";
  color?: string;
  raw: number;
  /** |shap| normalised to the largest factor, 0–1 */
  magnitude: number;
};

// Real model API by default. macOS port 5000 is AirPlay, so Flask runs on 5050.
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:5050";
// Set NEXT_PUBLIC_USE_MOCK=true to fall back to sample data.
const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK === "true";
export const api = axios.create({
  baseURL: API_BASE_URL,
});

import type { FeatureSource } from "./features";

export interface DataCompleteness {
  n_features: number;
  n_user_supplied: number;
  n_grounded: number;
  n_zero_filled: number;
  fraction_grounded: number;
}

export interface PredictResponse {
  district: string;
  season: string;
  year: number;
  predicted_yield_MT_per_Ha: number;
  confidence_lower: number;
  confidence_upper: number;
  confidence: "High" | "Medium" | "Low";
  shap_values: Record<string, number>;
  model: string;
  model_r2: number | null;
  /** e.g. "conformal_90pct" | "gaussian_1.96rmse" | "heuristic_15pct" */
  interval_method?: string;
  interval_coverage?: number | null;
  /** Where each of the 32 features came from — see src/api.py _resolve_features */
  feature_sources?: Record<string, FeatureSource>;
  /** The values actually fed to the model */
  resolved_features?: Record<string, number>;
  data_completeness?: DataCompleteness;
}

/** One district as advertised by GET /districts (dataset-derived). */
export interface DistrictInfo {
  name: string;
  seasons: string[];
  years: number[];
}

export interface DistrictsResponse {
  districts: DistrictInfo[];
  seasons: string[];
  years: number[];
  variant?: string;
  source?: string;
}

export interface ContextResponse extends Record<string, unknown> {
  district: string;
  season: string;
  year: number;
  /** "exact" when the year is in the dataset, otherwise "historical_mean" */
  source: "exact" | "historical_mean";
  n_years?: number;
  available_years?: number[];
}

export interface BaselineResponse {
  district: string;
  season: string;
  mean: number;
  min: number;
  max: number;
  n_years: number;
  years: number[];
  source: string;
}

export const getHealth = async () => {
  const response = await api.get("/health");
  return response.data;
};

export const getDistricts = async (): Promise<DistrictsResponse> => {
  const response = await api.get("/districts");
  return response.data;
};

export const getContext = async (
  district: string,
  season: string,
  year: number
): Promise<ContextResponse> => {
  const response = await api.get("/context", {
    params: { district, season, year },
  });
  return response.data;
};

/** Real per-district historical yield — replaces the hardcoded 13.5 MT/Ha. */
export const getBaseline = async (
  district: string,
  season: string
): Promise<BaselineResponse> => {
  const response = await api.get("/baseline", { params: { district, season } });
  return response.data;
};

/**
 * Send only what the caller actually knows.
 *
 * The backend resolves the remaining features through a
 * district+season → district → season → global mean cascade and recomputes the
 * three interaction terms itself, so the client no longer merges /context into
 * the payload (that merge silently produced an all-zero vector whenever
 * /context 404'd, e.g. Kurunegala on the synthetic model).
 */
export const predictYield = async (
  data: Record<string, unknown>
): Promise<PredictResponse> => {
  if (USE_MOCK) {
    return await predictYieldMock(data);
  }
  const response = await api.post("/predict", data);
  return response.data;
};

// Helper to convert SHAP to simple language
export const convertSHAPToExplanation = (
  shapValues: Record<string, number>
): ExplanationItem[] => {
  const features = Object.entries(shapValues)
    .sort(([, a], [, b]) => Math.abs(b) - Math.abs(a))
    .slice(0, 5);

  const maxAbs = Math.max(...features.map(([, v]) => Math.abs(v)), 1e-9);

  return features.map(([name, value]): ExplanationItem => {
    const isPositive = value > 0;

    // Map the raw model feature onto a translation key. Order matters:
    // soil_ph must be tested before the generic "soil" families, and
    // interaction terms before their component names.
    let key: string;
    if (name === "temp_x_humidity") key = "temp_x_humidity";
    else if (name === "rainfall_x_ndvi") key = "rainfall_x_ndvi";
    else if (name === "ndvi_x_lst") key = "ndvi_x_lst";
    else if (name === "soil_ph") key = "soil_ph";
    else if (name.includes("organic_carbon")) key = "organic_carbon";
    else if (name.includes("clay")) key = "clay";
    else if (name.includes("sand")) key = "sand";
    else if (name.includes("yield")) key = "prev_yield";
    else if (name.includes("rainfall")) key = "rainfall";
    else if (name.includes("drought")) key = "drought";
    else if (name.includes("lst")) key = "temperature";
    else if (name.includes("temp")) key = "temperature";
    else if (name.includes("humidity")) key = "humidity";
    else if (name.includes("evi")) key = "evi";
    else if (name.includes("ndvi")) key = "ndvi";
    else if (name.includes("solar")) key = "solar_radiation";
    else key = "other";

    return {
      name: key,
      feature: name,
      impact: isPositive ? "Positive" : "Negative",
      color: isPositive ? "text-emerald-600" : "text-red-600",
      raw: value,
      /** 0–1, for rendering the influence bar */
      magnitude: Math.abs(value) / maxAbs,
    };
  });
};

export const TARGET_DISTRICTS = [
  "Matale",
  "Anuradhapura",
  "Polonnaruwa",
  "Kurunegala",
] as const;

export type TargetDistrictName = (typeof TARGET_DISTRICTS)[number];

export interface DistrictPredictionsMap {
  [district: string]: PredictResponse;
}

export interface BatchPredictionResult {
  predictions: DistrictPredictionsMap;
  districtYields: Record<string, number>;
  bestDistrict: string;
  highestYield: number;
  lowestDistrict: string;
  lowestYield: number;
  averageYield: number;
  /** Districts whose prediction failed — render an error, never a fake number. */
  failedDistricts: string[];
}

// 🎨 Yield Color Scaling Utility
export type YieldCategoryLabel = "Very High" | "High" | "Medium" | "Low" | "Very Low";

export interface YieldCategoryInfo {
  label: YieldCategoryLabel;
  color: string;
  bgClass: string;
  textClass: string;
  min: number;
  max: number;
}

export const YIELD_CATEGORIES: YieldCategoryInfo[] = [
  { label: "Very High", color: "#15803d", bgClass: "bg-emerald-700", textClass: "text-emerald-700", min: 16, max: Infinity },
  { label: "High", color: "#22c55e", bgClass: "bg-emerald-500", textClass: "text-emerald-600", min: 13, max: 16 },
  { label: "Medium", color: "#eab308", bgClass: "bg-amber-400", textClass: "text-amber-600", min: 10, max: 13 },
  { label: "Low", color: "#f97316", bgClass: "bg-orange-500", textClass: "text-orange-600", min: 7, max: 10 },
  { label: "Very Low", color: "#ef4444", bgClass: "bg-red-500", textClass: "text-red-600", min: -Infinity, max: 7 },
];

export function getYieldCategory(value?: number): YieldCategoryInfo {
  if (value === undefined || value === null || isNaN(value)) {
    return { label: "Medium", color: "#cbd5e1", bgClass: "bg-slate-300", textClass: "text-slate-500", min: 0, max: 0 };
  }
  if (value >= 16) return YIELD_CATEGORIES[0];
  if (value >= 13) return YIELD_CATEGORIES[1];
  if (value >= 10) return YIELD_CATEGORIES[2];
  if (value >= 7) return YIELD_CATEGORIES[3];
  return YIELD_CATEGORIES[4];
}

export function getYieldColor(value?: number): string {
  return getYieldCategory(value).color;
}

/**
 * Executes parallel predictions for all 4 target districts.
 */
export const predictYieldsForAllDistricts = async (
  season = "Yala",
  year = new Date().getFullYear(),
  basePayload: Record<string, unknown> = {},
  districts: readonly string[] = TARGET_DISTRICTS
): Promise<BatchPredictionResult> => {
  // Send district/season/year only — the backend fills every remaining feature
  // from its per-district defaults. (This previously sent `rainfall`,
  // `temperature`, `soil_moisture` etc., which are UI names, not model feature
  // names, so the model silently ignored them.)
  const requests = districts.map((district) =>
    predictYield({ district, season, year, ...basePayload })
      .then((res) => ({ ok: true as const, district, res }))
      .catch((err) => {
        console.warn(`Failed prediction for ${district}:`, err);
        return { ok: false as const, district, res: null };
      })
  );

  const settled = await Promise.all(requests);
  const succeeded = settled.filter((s) => s.ok);
  const failedDistricts = settled.filter((s) => !s.ok).map((s) => s.district);

  // Previously a failure substituted hardcoded per-district yields with
  // model_r2: 0.91, so the homepage could display invented numbers with no
  // error shown. Surface the failure instead.
  if (succeeded.length === 0) {
    throw new Error(
      `All district predictions failed (${failedDistricts.join(", ")})`
    );
  }

  const predictions: DistrictPredictionsMap = {};
  const districtYields: Record<string, number> = {};

  let highestYield = -Infinity;
  let lowestYield = Infinity;
  let bestDistrict = succeeded[0].district;
  let lowestDistrict = succeeded[0].district;
  let totalYield = 0;

  succeeded.forEach(({ res }) => {
    const prediction = res as PredictResponse;
    const yieldVal = prediction.predicted_yield_MT_per_Ha;
    predictions[prediction.district] = prediction;
    districtYields[prediction.district] = yieldVal;
    totalYield += yieldVal;

    if (yieldVal > highestYield) {
      highestYield = yieldVal;
      bestDistrict = prediction.district;
    }
    if (yieldVal < lowestYield) {
      lowestYield = yieldVal;
      lowestDistrict = prediction.district;
    }
  });

  const averageYield = Number((totalYield / succeeded.length).toFixed(2));

  return {
    predictions,
    districtYields,
    bestDistrict,
    highestYield,
    lowestDistrict,
    lowestYield,
    averageYield,
    failedDistricts,
  };
};


