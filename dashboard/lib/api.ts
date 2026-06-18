import axios from "axios";
import { predictYieldMock } from "./sample-api";
import { ExplanationItem } from "@/app/[locale]/explain/page";

// Real model API by default. macOS port 5000 is AirPlay, so Flask runs on 5050.
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:5050";
// Set NEXT_PUBLIC_USE_MOCK=true to fall back to sample data.
const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK === "true";
export const api = axios.create({
  baseURL: API_BASE_URL,
});

// The form supplies district/season in lowercase; the model + /context expect
// Title-case (e.g. "matale" → "Matale", "yala" → "Yala").
const titleCase = (s: string): string =>
  s.length > 0 ? s.charAt(0).toUpperCase() + s.slice(1).toLowerCase() : s;

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
}

export const getHealth = async () => {
  const response = await api.get("/health");
  return response.data;
};

export const getDistricts = async () => {
  const response = await api.get("/districts");
  return response.data;
};

export const getContext = async (district: string, season: string, year: number) => {
  const response = await api.get("/context", {
    params: { district, season, year },
  });
  return response.data;
};
export const predictYield = async (data: any): Promise<PredictResponse> => {
  if (USE_MOCK) {
    return await predictYieldMock(data);
  }

  // The form only collects a few fields. Enrich the payload with the full
  // 32-feature context for that district/season/year so the model receives a
  // complete, realistic feature vector (otherwise missing features default to 0).
  const district = titleCase(String(data?.district ?? ""));
  const season = titleCase(String(data?.season ?? ""));
  const parsedYear = Number(data?.year);
  const year = Number.isFinite(parsedYear) ? parsedYear : undefined;

  let payload: Record<string, unknown> = { ...data, district, season };
  if (district && season && year !== undefined) {
    try {
      const ctx = await getContext(district, season, year);
      // /context returns all 32 features flat; user-entered values override them.
      payload = { ...ctx, ...data, district, season, year };
    } catch {
      // Context unavailable (e.g. future year / API down) — use the raw payload.
    }
  }

  // Keep interaction features consistent with the (possibly user-edited) inputs.
  const num = (k: string) => Number(payload[k]) || 0;
  payload["rainfall_x_ndvi"] = num("season_total_rainfall") * num("season_mean_ndvi");
  payload["temp_x_humidity"] = num("season_avg_temp") * num("season_avg_humidity");
  payload["ndvi_x_lst"] = num("season_mean_ndvi") * num("season_mean_lst_day");

  const response = await api.post("/predict", payload);
  return response.data;
};

// Helper to convert SHAP to simple language
export const convertSHAPToExplanation = (
  shapValues: Record<string, number>,
  lang: "en" | "ta" | "si" = "en"
) => {  const features = Object.entries(shapValues)
    .sort(([, a], [, b]) => Math.abs(b) - Math.abs(a))
    .slice(0, 5);

 return features.map(([name, value]): ExplanationItem => {
  const isPositive = value > 0;

  let description = "";
  if (name.includes("rainfall")) description = "rainfall";
  else if (name.includes("temp")) description = "temperature";
  else if (name.includes("humidity")) description = "humidity";
  else if (name.includes("soil_ph")) description = "soil_ph";
  else if (name.includes("soil_moisture")) description = "soil_moisture";
  else if (name.includes("ndvi")) description = "ndvi";
  else if (name.includes("solar")) description = "solar_radiation";
  else description = name.replace(/_/g, " ");

  return {
    name: description,
    impact: isPositive ? "Positive" : "Negative",
    color: isPositive ? "text-emerald-600" : "text-red-600",
    raw: value,
  };
});
};

export const mockPredictResponse: PredictResponse = {
  district: "Matale",
  season: "Yala",
  year: 2024,

  predicted_yield_MT_per_Ha: 14.8,

  confidence_lower: 13.2,
  confidence_upper: 16.1,
  confidence: "High",

  shap_values: {
    rainfall: 0.42,
    temperature: -0.18,
    humidity: 0.25,
    soil_ph: 0.12,
    soil_moisture: 0.33,
    ndvi: 0.21,
    solar_radiation: -0.09,
  },

  model: "XGBoost Regressor (Mock)",
  model_r2: 0.91,
};

