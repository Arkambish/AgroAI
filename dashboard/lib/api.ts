import axios from "axios";
import { predictYieldMock } from "./sample-api";

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
  const response = await api.post("/predict", data);
  return response.data;
};

// Helper to convert SHAP to simple language
export const convertSHAPToExplanation = (shapValues: Record<string, number>) => {
  const features = Object.entries(shapValues)
    .sort(([, a], [, b]) => Math.abs(b) - Math.abs(a))
    .slice(0, 5);

  return features.map(([name, value]) => {
    const isPositive = value > 0;
    const impact = Math.abs(value);
    
    let description = "";
    if (name.includes("rainfall")) description = "Rainfall";
    else if (name.includes("temp")) description = "Temperature";
    else if (name.includes("humidity")) description = "Humidity";
    else if (name.includes("soil_ph")) description = "Soil pH";
    else if (name.includes("ndvi")) description = "Vegetation health (NDVI)";
    else if (name.includes("solar")) description = "Solar radiation";
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