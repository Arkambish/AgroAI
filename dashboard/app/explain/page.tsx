"use client";

import { useEffect, useState } from "react";
import { Brain, TrendingUp, TrendingDown, Info, AlertTriangle } from "lucide-react";
import { convertSHAPToExplanation, type PredictResponse } from "@/lib/api";
import { clsx } from "clsx";

export default function ExplainPage() {
  const [prediction, setPrediction] = useState<PredictResponse | null>(null);
  const [explanations, setExplanations] = useState<any[]>([]);

  useEffect(() => {
    const lastPrediction = localStorage.getItem("last_prediction");
    if (lastPrediction) {
      const parsed = JSON.parse(lastPrediction);
      setPrediction(parsed);
      setExplanations(convertSHAPToExplanation(parsed.shap_values));
    }
  }, []);

  if (!prediction) {
    return (
      <div className="flex min-h-[400px] flex-col items-center justify-center space-y-4 text-center">
        <div className="rounded-full bg-slate-100 p-6 dark:bg-slate-800">
          <Brain size={64} className="text-slate-300" />
        </div>
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white">No Prediction Found</h2>
        <p className="max-w-md text-slate-500">Please make a prediction first on the "Predict Yield" page to see the explanation.</p>
        <a href="/predict" className="rounded-xl bg-primary px-6 py-3 font-bold text-white shadow-lg transition-transform hover:scale-105">
          Go to Prediction
        </a>
      </div>
    );
  }

  return (
    <div className="space-y-10">
      <div className="flex flex-col space-y-2">
        <h1 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white">Why This Prediction?</h1>
        <p className="text-slate-500 dark:text-slate-400">Understanding the factors that influenced your predicted yield of {prediction.predicted_yield_MT_per_Ha} MT/Ha.</p>
      </div>

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-2">
        {/* Feature Impact Cards */}
        <section className="space-y-6">
          <h2 className="text-xl font-bold text-slate-800 dark:text-slate-200">Key Factors</h2>
          <div className="grid grid-cols-1 gap-4">
            {explanations.map((item, index) => (
              <div 
                key={index} 
                className="flex items-center justify-between rounded-2xl border bg-white p-6 shadow-sm transition-all hover:shadow-md dark:bg-slate-900"
              >
                <div className="flex items-center space-x-4">
                  <div className={clsx(
                    "rounded-xl p-3",
                    item.impact === "Positive" ? "bg-emerald-100 text-emerald-600 dark:bg-emerald-900/30" : "bg-red-100 text-red-600 dark:bg-red-900/30"
                  )}>
                    {item.impact === "Positive" ? <TrendingUp size={24} /> : <TrendingDown size={24} />}
                  </div>
                  <div>
                    <h4 className="font-bold text-slate-900 dark:text-white">{item.name}</h4>
                    <p className={clsx("text-sm font-medium", item.color)}>
                      {item.impact} Impact
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <div className="h-2 w-24 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
                    <div 
                      className={clsx(
                        "h-full rounded-full",
                        item.impact === "Positive" ? "bg-emerald-500" : "bg-red-500"
                      )}
                      style={{ width: `${Math.min(100, Math.abs(item.raw) * 100)}%` }}
                    ></div>
                  </div>
                  <span className="mt-1 block text-[10px] text-slate-400">Relative Influence</span>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Farmer Explanation Panel */}
        <section className="space-y-6">
          <h2 className="text-xl font-bold text-slate-800 dark:text-slate-200">Summary for Farmers</h2>
          <div className="rounded-3xl border-2 border-primary/20 bg-white p-8 shadow-xl dark:bg-slate-900">
            <div className="flex items-center space-x-3 text-primary">
              <Brain size={32} />
              <h3 className="text-2xl font-bold">The AI's reasoning</h3>
            </div>
            
            <div className="mt-6 space-y-4 text-lg leading-relaxed text-slate-700 dark:text-slate-300">
              <p>
                Based on your inputs for <span className="font-bold text-slate-900 dark:text-white">{prediction.district}</span>, here is why we expect a yield of <span className="font-bold text-primary">{prediction.predicted_yield_MT_per_Ha} MT/Ha</span>:
              </p>
              
              <ul className="list-disc space-y-4 pl-6">
                {explanations.map((item, index) => (
                  <li key={index}>
                    <span className="font-bold">{item.name}</span> {item.impact === "Positive" ? "helped increase" : "reduced"} the potential yield this time.
                  </li>
                ))}
              </ul>

              <div className="mt-8 rounded-2xl bg-amber-50 p-6 dark:bg-amber-900/10">
                <div className="flex items-start space-x-3">
                  <AlertTriangle className="mt-1 text-amber-500" size={24} />
                  <div>
                    <h4 className="font-bold text-amber-800 dark:text-amber-200">Key Insight</h4>
                    <p className="mt-1 text-sm text-amber-700 dark:text-amber-300">
                      Overall conditions are {prediction.predicted_yield_MT_per_Ha > 15 ? "very favorable" : "moderately suitable"}. 
                      The biggest limiting factor currently is <span className="font-bold">{explanations.find(e => e.impact === "Negative")?.name || "none"}</span>.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
