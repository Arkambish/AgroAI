// Typed wrapper around the Flask API. All requests go through the Next.js
// rewrite at /api/backend/* (configured in next.config.ts) so the browser
// doesn't talk to a different origin.

import { z } from "zod";
import type {
  ContextResponse,
  DistrictsResponse,
  FeatureImportanceEntry,
  HealthResponse,
  ModelComparisonRow,
  PredictRequest,
  PredictResponse,
} from "./types";

const BASE = "/api/backend";

async function jsonFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`API ${path} failed: ${res.status} ${body}`);
  }
  return (await res.json()) as T;
}

// ---- Schemas (runtime validation) ----

const HealthSchema = z.object({
  status: z.string(),
  model: z.string().nullable(),
  service: z.string(),
});

const PredictSchema = z.object({
  district: z.string().nullable(),
  season: z.string().nullable(),
  predicted_yield_MT_per_Ha: z.number(),
  confidence_lower: z.number(),
  confidence_upper: z.number(),
  model: z.string().nullable(),
  model_r2: z.number().nullable(),
});

const ModelRowSchema = z.object({
  Model: z.string(),
  RMSE: z.number(),
  MAE: z.number(),
  R2: z.number(),
  MAPE: z.number(),
  Train_Time_s: z.number().nullable(),
  Parameters: z.number().nullable(),
});

const FeatureImportanceSchema = z.array(
  z.object({
    rank: z.number(),
    name: z.string(),
    mean_abs_shap: z.number(),
  }),
);

const DistrictsSchema = z.object({
  districts: z.array(z.string()),
  seasons: z.array(z.string()),
  years: z.array(z.number()),
});

// ---- Public API ----

export async function getHealth(): Promise<HealthResponse> {
  return HealthSchema.parse(await jsonFetch<HealthResponse>("/health"));
}

export async function predict(body: PredictRequest): Promise<PredictResponse> {
  const raw = await jsonFetch<PredictResponse>("/predict", {
    method: "POST",
    body: JSON.stringify(body),
  });
  return PredictSchema.parse(raw);
}

export async function getModelsCompare(): Promise<ModelComparisonRow[]> {
  const raw = await jsonFetch<ModelComparisonRow[]>("/models/compare");
  return z.array(ModelRowSchema).parse(raw);
}

export async function getFeatureImportance(): Promise<FeatureImportanceEntry[]> {
  return FeatureImportanceSchema.parse(
    await jsonFetch<FeatureImportanceEntry[]>("/feature-importance"),
  );
}

export async function getDistricts(): Promise<DistrictsResponse> {
  const raw = await jsonFetch<DistrictsResponse>("/districts");
  return DistrictsSchema.parse(raw) as DistrictsResponse;
}

export async function getContext(
  district: string,
  season: string,
  year: number,
): Promise<ContextResponse> {
  const params = new URLSearchParams({ district, season, year: String(year) });
  return jsonFetch<ContextResponse>(`/context?${params.toString()}`);
}
