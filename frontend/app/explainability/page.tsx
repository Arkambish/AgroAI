"use client";

import * as React from "react";
import useSWR from "swr";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { FeatureImportanceChart } from "@/components/feature-importance-chart";
import { getFeatureImportance } from "@/lib/api";
import { FEATURE_META } from "@/lib/constants";
import { formatNumber } from "@/lib/utils";

export default function ExplainabilityPage() {
  const { data, error, isLoading } = useSWR("feature-importance", getFeatureImportance);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Explainability</h1>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          Per-feature SHAP attributions for the best tabular model. Higher mean |SHAP value|
          means the feature has more influence on individual predictions.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Top 15 features by mean |SHAP|</CardTitle>
          <CardDescription>
            Computed via shap.TreeExplainer on the best Random Forest / XGBoost model. See{" "}
            <code className="text-xs">outputs/results/feature_importance.json</code> for the
            raw values.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading && (
            <div className="grid h-[420px] place-items-center text-sm text-slate-500">
              Loading SHAP values…
            </div>
          )}
          {error && (
            <p className="rounded-md border border-red-300 bg-red-50 p-3 text-sm text-red-800 dark:border-red-900 dark:bg-red-950 dark:text-red-200">
              Could not load feature importance: {String(error)}
            </p>
          )}
          {data && <FeatureImportanceChart entries={data} height={520} />}
        </CardContent>
      </Card>

      {data && (
        <Card>
          <CardHeader>
            <CardTitle>Top 5 — explained</CardTitle>
            <CardDescription>
              Which inputs drive predictions the most, in plain terms.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2 text-sm">
              {data.slice(0, 5).map((entry) => (
                <li key={entry.name} className="flex items-baseline gap-3">
                  <span className="inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-emerald-600 text-[11px] font-semibold text-white">
                    {entry.rank}
                  </span>
                  <div>
                    <span className="font-medium">
                      {FEATURE_META[entry.name]?.label ?? entry.name}
                    </span>
                    <span className="ml-2 text-xs text-slate-500 tabular-nums">
                      mean |SHAP| = {formatNumber(entry.mean_abs_shap, 4)}
                    </span>
                    {FEATURE_META[entry.name]?.help && (
                      <p className="text-xs text-slate-500 dark:text-slate-400">
                        {FEATURE_META[entry.name]?.help}
                      </p>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
