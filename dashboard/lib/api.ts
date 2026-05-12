import axios from "axios";

const API_BASE_URL = "http://localhost:5000";

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
