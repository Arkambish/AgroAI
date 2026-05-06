"use client";

import * as React from "react";
import { Loader2, RefreshCw, Sparkles } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { FeatureInputTabs } from "@/components/feature-input-tabs";
import { PredictionResult } from "@/components/prediction-result";
import { useSelection } from "@/components/selection-context";
import { getContext, predict } from "@/lib/api";
import { ALL_FEATURES } from "@/lib/constants";
import type { PredictResponse } from "@/lib/types";

function emptyFeatures(): Record<string, number> {
  return Object.fromEntries(ALL_FEATURES.map((f) => [f, 0]));
}

export default function PredictPage() {
  const { district, season, year } = useSelection();
  const [features, setFeatures] = React.useState<Record<string, number>>(emptyFeatures);
  const [contextSource, setContextSource] = React.useState<string | null>(null);
  const [loadingContext, setLoadingContext] = React.useState(false);
  const [submitting, setSubmitting] = React.useState(false);
  const [result, setResult] = React.useState<PredictResponse | null>(null);
  const [error, setError] = React.useState<string | null>(null);

  const loadContext = React.useCallback(async () => {
    setLoadingContext(true);
    setError(null);
    try {
      const ctx = await getContext(district, season, year);
      const next: Record<string, number> = { ...emptyFeatures() };
      for (const [k, v] of Object.entries(ctx)) {
        if (typeof v === "number" && ALL_FEATURES.includes(k)) {
          next[k] = v;
        }
      }
      setFeatures(next);
      setContextSource(typeof ctx.source === "string" ? ctx.source : null);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoadingContext(false);
    }
  }, [district, season, year]);

  // No auto-load on mount — React 19 forbids setState in useEffect bodies.
  // The user clicks "Load context" to prefill all 32 features in one go.

  const onSubmit = async () => {
    setSubmitting(true);
    setError(null);
    try {
      const r = await predict({ district, season, ...features });
      setResult(r);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">New prediction</h1>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          Use the sidebar selectors to choose <span className="font-medium">district</span>,{" "}
          <span className="font-medium">season</span>, and{" "}
          <span className="font-medium">year</span>, then load contextual feature values from
          the historical dataset and adjust as needed.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">
            {district} · {season} · {year}
          </CardTitle>
          <CardDescription>
            Click <em>Load context</em> to prefill all 32 features from the integrated dataset.
            For years not in the dataset, the (district, season) historical mean is used.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap items-center gap-3">
            <Button onClick={loadContext} disabled={loadingContext} variant="secondary">
              {loadingContext ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <RefreshCw className="h-4 w-4" />
              )}
              {loadingContext ? "Loading…" : "Load context"}
            </Button>
            {contextSource && (
              <span className="text-xs text-slate-500 dark:text-slate-400">
                Source: <span className="font-medium">{contextSource}</span>
              </span>
            )}
          </div>

          <FeatureInputTabs values={features} onChange={setFeatures} />

          <div className="flex justify-end">
            <Button onClick={onSubmit} disabled={submitting}>
              {submitting ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Sparkles className="h-4 w-4" />
              )}
              {submitting ? "Predicting…" : "Predict yield"}
            </Button>
          </div>

          {error && (
            <p className="rounded-md border border-red-300 bg-red-50 p-3 text-sm text-red-800 dark:border-red-900 dark:bg-red-950 dark:text-red-200">
              {error}
            </p>
          )}
        </CardContent>
      </Card>

      {result && <PredictionResult result={result} />}
    </div>
  );
}
