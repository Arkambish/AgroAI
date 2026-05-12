import { PredictResponse } from "./api";

export const predictYieldMock = async (payload: any): Promise<PredictResponse> => {
  // You can customize the mock response as needed
  return {
    district: payload.district || "Colombo",
    season: payload.season || "Yala",
    year: payload.year || 2024,
    predicted_yield_MT_per_Ha: 14.8,
    confidence_lower: 13.2,
    confidence_upper: 16.1,
    confidence: "High",
    shap_values: {
      rainfall: 0.32,
      temperature: -0.12,
      humidity: 0.18,
      soil_moisture: 0.05,
      soil_ph: 0.09,
    },
    model: "XGBoost (Mock)",
    model_r2: 0.91,
  };
};
