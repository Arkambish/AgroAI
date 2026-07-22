import axios from "axios";
import { predictYieldMock } from "./sample-api";
import { ExplanationItem } from "@/app/[locale]/explain/page";

const API_BASE_URL = "http://localhost:5000";
// Toggle this to switch between mock and real API
const USE_MOCK = true;
export const api = axios.create({
  baseURL: API_BASE_URL,
});

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

export const predictYield = async (data: any): Promise<PredictResponse> => {
  if (USE_MOCK) {
    return await predictYieldMock(data);
  }
  try {
    const response = await api.post("/predict", data);
    return response.data;
  } catch (err) {
    console.error("Predict API error:", err);
    // Normalize network/backend errors so callers can show a user-friendly message
    throw new Error("NetworkError");
  }
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

