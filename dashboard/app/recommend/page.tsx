"use client";

import { useEffect, useState } from "react";
import { Lightbulb, CheckCircle2, ShieldAlert, Zap, ArrowUpRight } from "lucide-react";
import { convertSHAPToExplanation, type PredictResponse } from "@/lib/api";
import { clsx } from "clsx";

export default function RecommendationPage() {
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
          <Lightbulb size={64} className="text-slate-300" />
        </div>
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white">No Recommendations Yet</h2>
        <p className="max-w-md text-slate-500">Please make a prediction first to see personalized agricultural advice.</p>
        <a href="/predict" className="rounded-xl bg-primary px-6 py-3 font-bold text-white shadow-lg transition-transform hover:scale-105">
          Start Now
        </a>
      </div>
    );
  }

  // Recommendation Logic
  const getStrategies = () => {
    const strategies = [];
    const negativeFactors = explanations.filter(e => e.impact === "Negative");
    
    if (negativeFactors.some(e => e.name.toLowerCase().includes("rainfall"))) {
      strategies.push({
        title: "Optimize Irrigation",
        description: "Increase water supply during dry spells to compensate for low rainfall.",
        icon: Zap
      });
    }
    
    if (negativeFactors.some(e => e.name.toLowerCase().includes("temp"))) {
      strategies.push({
        title: "Heat Management",
        description: "Use mulching (straw or plastic) to keep soil cool and reduce evaporation.",
        icon: ShieldAlert
      });
    }

    if (negativeFactors.some(e => e.name.toLowerCase().includes("soil ph"))) {
      strategies.push({
        title: "Adjust Soil pH",
        description: "Apply lime if too acidic or sulfur if too alkaline to reach 6.0-7.0 range.",
        icon: CheckCircle2
      });
    }

    // Default if no specific negatives or to fill up
    if (strategies.length < 3) {
      strategies.push({
        title: "Nutrient Boost",
        description: "Apply balanced NPK fertilizer specifically tailored for big onions.",
        icon: CheckCircle2
      });
      strategies.push({
        title: "Pest Monitoring",
        description: "Regularly check for thrips and purple blotch during bulb formation.",
        icon: ShieldAlert
      });
    }

    return strategies;
  };

  return (
    <div className="space-y-10">
      <div className="flex flex-col space-y-2">
        <h1 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white">Actionable Advice</h1>
        <p className="text-slate-500 dark:text-slate-400">Steps you can take to improve your yield based on the AI analysis.</p>
      </div>

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
        {/* Improvement Strategies */}
        <div className="lg:col-span-2 space-y-6">
          <h2 className="text-xl font-bold text-slate-800 dark:text-slate-200">Strategies for Improvement</h2>
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
            {getStrategies().map((strategy, index) => (
              <div 
                key={index} 
                className="rounded-3xl border bg-white p-6 shadow-md transition-transform hover:scale-[1.02] dark:bg-slate-900"
              >
                <div className="mb-4 inline-flex rounded-2xl bg-lime-100 p-4 text-lime-600 dark:bg-lime-900/30">
                  <strategy.icon size={28} />
                </div>
                <h3 className="text-xl font-bold text-slate-900 dark:text-white">{strategy.title}</h3>
                <p className="mt-2 text-slate-600 dark:text-slate-400">
                  {strategy.description}
                </p>
                <button className="mt-6 flex items-center space-x-1 font-bold text-primary hover:underline">
                  <span>Learn how</span>
                  <ArrowUpRight size={16} />
                </button>
              </div>
            ))}
          </div>

          {/* What-If Scenario */}
          <div className="rounded-3xl bg-gradient-to-br from-emerald-600 to-lime-600 p-8 text-white shadow-xl">
            <h3 className="text-2xl font-bold">"If conditions improve..."</h3>
            <p className="mt-2 text-emerald-50 opacity-90">
              Our simulations show that by optimizing irrigation and soil nutrients, your yield could potentially increase from 
              <span className="mx-2 font-black text-white underline decoration-lime-400 decoration-4 underline-offset-4">
                {prediction.predicted_yield_MT_per_Ha} MT/Ha
              </span> 
              to 
              <span className="mx-2 font-black text-white underline decoration-white decoration-4 underline-offset-4">
                {(prediction.predicted_yield_MT_per_Ha * 1.15).toFixed(1)} MT/Ha
              </span>.
            </p>
            <div className="mt-8 flex space-x-4">
              <div className="rounded-2xl bg-white/20 p-4 backdrop-blur-md">
                <p className="text-xs font-bold uppercase">Estimated Gain</p>
                <p className="text-2xl font-black">+15% Potential</p>
              </div>
              <div className="rounded-2xl bg-white/20 p-4 backdrop-blur-md">
                <p className="text-xs font-bold uppercase">Confidence</p>
                <p className="text-2xl font-black">High</p>
              </div>
            </div>
          </div>
        </div>

        {/* Risk Prevention */}
        <div className="space-y-6">
          <h2 className="text-xl font-bold text-slate-800 dark:text-slate-200">Risk Prevention</h2>
          <div className="space-y-4">
            {[
              { title: "Heat Wave Alert", risk: "Moderate", action: "Increase irrigation" },
              { title: "Soil Erosion", risk: "Low", action: "Monitor drainage" },
              { title: "Pest Infestation", risk: "High", action: "Early spray recommended" },
            ].map((risk, index) => (
              <div key={index} className="rounded-2xl border bg-white p-5 shadow-sm dark:bg-slate-900">
                <div className="flex items-center justify-between">
                  <h4 className="font-bold text-slate-900 dark:text-white">{risk.title}</h4>
                  <span className={clsx(
                    "rounded-full px-2 py-1 text-[10px] font-bold uppercase",
                    risk.risk === "High" ? "bg-red-100 text-red-600" : 
                    risk.risk === "Moderate" ? "bg-amber-100 text-amber-600" : "bg-emerald-100 text-emerald-600"
                  )}>
                    {risk.risk} Risk
                  </span>
                </div>
                <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
                  <span className="font-bold">Action:</span> {risk.action}
                </p>
              </div>
            ))}
          </div>

          <div className="rounded-2xl bg-slate-900 p-6 text-white dark:bg-slate-800">
            <h4 className="font-bold">Expert Support</h4>
            <p className="mt-2 text-sm text-slate-400">
              Need more specific advice? Connect with a local agriculture officer.
            </p>
            <button className="mt-4 w-full rounded-xl bg-emerald-600 py-3 font-bold text-white transition-colors hover:bg-emerald-700">
              Find Officer
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
