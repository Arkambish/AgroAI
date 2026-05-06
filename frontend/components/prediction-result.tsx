import * as React from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { PredictResponse } from "@/lib/types";
import { formatNumber } from "@/lib/utils";

interface PredictionResultProps {
  result: PredictResponse;
}

export function PredictionResult({ result }: PredictionResultProps) {
  const { predicted_yield_MT_per_Ha, confidence_lower, confidence_upper, model, model_r2, district, season } = result;

  const range = Math.max(0.001, confidence_upper - confidence_lower);
  const pct = Math.min(
    100,
    Math.max(0, ((predicted_yield_MT_per_Ha - confidence_lower) / range) * 100),
  );

  return (
    <Card className="border-emerald-200 dark:border-emerald-900">
      <CardHeader>
        <CardTitle className="text-lg">
          Predicted yield · {district} · {season}
        </CardTitle>
        <CardDescription>
          Served by <span className="font-medium">{model ?? "?"}</span>
          {model_r2 !== null && ` · model R² = ${formatNumber(model_r2, 3)}`}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <div className="text-4xl font-semibold tabular-nums text-emerald-700 dark:text-emerald-300">
            {formatNumber(predicted_yield_MT_per_Ha, 2)}
            <span className="ml-2 text-base font-normal text-slate-500">MT/Ha</span>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            95 % confidence interval (Gaussian, ±1.96 × RMSE):
            {" "}
            <span className="tabular-nums">
              [{formatNumber(confidence_lower, 2)}, {formatNumber(confidence_upper, 2)}]
            </span>
          </p>
        </div>

        <div className="space-y-2" aria-label="Confidence interval visualisation">
          <div className="relative h-2 w-full rounded-full bg-slate-100 dark:bg-slate-800">
            <div
              className="absolute top-0 h-2 rounded-full bg-emerald-200 dark:bg-emerald-900"
              style={{ left: 0, right: 0 }}
            />
            <div
              className="absolute -top-0.5 h-3 w-1 rounded-full bg-emerald-700 dark:bg-emerald-300"
              style={{ left: `calc(${pct}% - 2px)` }}
              aria-hidden
            />
          </div>
          <div className="flex justify-between text-[11px] tabular-nums text-slate-500">
            <span>{formatNumber(confidence_lower, 2)}</span>
            <span>{formatNumber(confidence_upper, 2)}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
