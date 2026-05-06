// Shared TypeScript types matching the Flask API contract in src/api.py.
// Update both this file and the API at the same time when shapes change.

export type District = "Matale" | "Anuradhapura" | "Polonnaruwa" | "Jaffna";
export type Season = "Yala" | "Maha";

export interface HealthResponse {
  status: "ok" | string;
  model: string | null;
  service: string;
}

export interface PredictRequest {
  district: District | string;
  season: Season | string;
  // Plus any subset of the 32 numeric features. Missing keys default to 0 server-side.
  [feature: string]: string | number | undefined;
}

export interface PredictResponse {
  district: string | null;
  season: string | null;
  predicted_yield_MT_per_Ha: number;
  confidence_lower: number;
  confidence_upper: number;
  model: string | null;
  model_r2: number | null;
}

export interface ModelComparisonRow {
  Model: string;
  RMSE: number;
  MAE: number;
  R2: number;
  MAPE: number;
  Train_Time_s: number | null;
  Parameters: number | null;
}

export interface FeatureImportanceEntry {
  rank: number;
  name: string;
  mean_abs_shap: number;
}

export interface ContextResponse {
  district: District | string;
  season: Season | string;
  year: number;
  source: "exact" | "historical_mean";
  available_years: number[];
  // 32 feature keys with numeric values.
  [feature: string]: string | number | number[];
}

export interface DistrictsResponse {
  districts: District[];
  seasons: Season[];
  years: number[];
}
