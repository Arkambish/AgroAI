/**
 * Agronomic rule / threshold engine for the Recommendation tab.
 *
 * This is the "Actionable Feature Filtering" + "Agronomic Rule / Threshold
 * Engine" stage of the recommendation pipeline:
 *
 *   Prediction -> SHAP -> ERI -> Actionable Feature Filtering
 *   -> Agronomic Rule/Threshold Engine -> Template layer -> Farmer text
 *
 * It never re-runs the model or invents new numbers — it only reads the
 * SHAP values, per-feature ERI and resolved feature values already returned
 * by /predict (the same data the Explain tab renders), and compares them
 * against static DOA/FAO big-onion (Allium cepa) cultivation thresholds.
 *
 * A rule only fires when BOTH are true:
 *   1. The feature's value breaches its agronomic threshold/range, AND
 *   2. That feature's SHAP contribution is actually pulling this
 *      prediction's yield down.
 * A threshold breach with a non-negative SHAP contribution is not shown —
 * it isn't what's hurting *this* prediction, so recommending it would be
 * generic advice, not a grounded one. This is what keeps the tab from
 * showing "Nutrient Boost" / "Pest Monitoring"-style advice that isn't
 * actually tied to the current prediction.
 */
import type { PredictResponse } from "./api";

export type RecommendationCategory = "soil" | "water" | "heat" | "humidity";
export type EffectTier = "high" | "medium" | "low";
export type ReliabilityTier =
  | "cardHigh"
  | "cardGood"
  | "cardModerate"
  | "cardLow"
  | "cardUnknown";

interface BaseFinding {
  /** Matches a `recommend.rules.<id>.*` translation key. */
  id: string;
  category: RecommendationCategory;
  /** Raw model feature(s) this finding's SHAP direction/magnitude comes from. */
  featureNames: string[];
  /** The raw feature actually compared against the agronomic threshold. */
  valueFeature: string;
  currentValue: number;
  unit: string;
  shapValue: number;
  reliability: number | undefined;
  reliabilityTier: ReliabilityTier;
  source: string;
}

export interface AgronomicRecommendation extends BaseFinding {
  kind: "recommendation";
  effectTier: EffectTier;
  recommendedRange: [number, number];
}

export interface AgronomicRisk extends BaseFinding {
  kind: "risk";
  level: EffectTier;
  threshold: number;
  comparison: "above" | "below";
}

export type AgronomicFinding = AgronomicRecommendation | AgronomicRisk;

const SOURCE_DOA_FAO = "DOA / FAO onion (Allium cepa) cultivation guideline";

type Rule = {
  id: string;
  category: RecommendationCategory;
  kind: "recommendation" | "risk";
  featureNames: string[];
  valueFeature: string;
  unit: string;
  breach: (value: number, resolved: Record<string, number>) => boolean;
  range?: [number, number];
  threshold?: number;
  comparison?: "above" | "below";
};

// Thresholds are deliberately simple, literature-level defaults for big
// onion cultivation in Sri Lanka (DOA extension guidance / FAO crop water
// requirements for Allium cepa) — not a substitute for a soil test or a
// district agronomist, which is exactly why "Need more help?" stays on the
// page.
const RULES: Rule[] = [
  {
    id: "soil_ph_low",
    category: "soil",
    kind: "recommendation",
    featureNames: ["soil_ph"],
    valueFeature: "soil_ph",
    unit: "pH",
    range: [5.5, 6.5],
    breach: (v) => v < 5.5,
  },
  {
    id: "soil_ph_high",
    category: "soil",
    kind: "recommendation",
    featureNames: ["soil_ph"],
    valueFeature: "soil_ph",
    unit: "pH",
    range: [5.5, 6.5],
    breach: (v) => v > 6.5,
  },
  {
    id: "water_deficit",
    category: "water",
    kind: "recommendation",
    featureNames: ["season_total_rainfall", "drought_index_spi"],
    valueFeature: "season_total_rainfall",
    unit: "mm",
    range: [350, 600],
    breach: (v, r) => v < 350 || (r.drought_index_spi ?? 0) <= -1.0,
  },
  {
    id: "heat_stress",
    category: "heat",
    kind: "risk",
    featureNames: ["heat_stress_days", "season_avg_temp"],
    valueFeature: "heat_stress_days",
    unit: "days",
    threshold: 10,
    comparison: "above",
    breach: (v, r) => v > 10 || (r.season_avg_temp ?? 0) > 30,
  },
  {
    id: "humidity_disease_risk",
    category: "humidity",
    kind: "risk",
    featureNames: ["season_avg_humidity"],
    valueFeature: "season_avg_humidity",
    unit: "%",
    threshold: 85,
    comparison: "above",
    breach: (v) => v > 85,
  },
];

function reliabilityTierFor(eri: number | undefined): ReliabilityTier {
  if (eri === undefined) return "cardUnknown";
  const pct = eri * 100;
  if (pct >= 90) return "cardHigh";
  if (pct >= 70) return "cardGood";
  if (pct >= 50) return "cardModerate";
  return "cardLow";
}

function effectTierFor(magnitude: number): EffectTier {
  if (magnitude >= 0.66) return "high";
  if (magnitude >= 0.33) return "medium";
  return "low";
}

/**
 * Run every agronomic rule against one prediction's resolved features, SHAP
 * values and per-feature ERI. Pure and synchronous — no network calls, no
 * model logic, nothing beyond threshold comparisons on data /predict already
 * returned.
 */
export function evaluateAgronomicRules(
  prediction: Pick<
    PredictResponse,
    "resolved_features" | "shap_values" | "per_feature_eri"
  >
): { recommendations: AgronomicRecommendation[]; risks: AgronomicRisk[] } {
  const resolved = prediction.resolved_features;
  const shapValues = prediction.shap_values ?? {};
  const perFeatureEri = prediction.per_feature_eri;

  const recommendations: AgronomicRecommendation[] = [];
  const risks: AgronomicRisk[] = [];

  if (!resolved) return { recommendations, risks };

  // Anchor effect-tier magnitude to the single largest |SHAP| across every
  // raw feature for this prediction, so severity reads consistently with
  // the Explain tab's own High/Medium/Low tiers rather than a scale local
  // to just the handful of rules that fired.
  const maxAbsShap = Math.max(
    ...Object.values(shapValues).map((v) => Math.abs(v)),
    1e-9
  );

  for (const rule of RULES) {
    const value = resolved[rule.valueFeature];
    if (value === undefined || !rule.breach(value, resolved)) continue;

    let combinedShap = 0;
    let weightedEriSum = 0;
    let absShapSum = 0;
    for (const f of rule.featureNames) {
      const shap = shapValues[f] ?? 0;
      combinedShap += shap;
      const absShap = Math.abs(shap);
      absShapSum += absShap;
      const eriForRaw = perFeatureEri?.[f];
      if (eriForRaw !== undefined) weightedEriSum += absShap * eriForRaw;
    }

    // The threshold is breached, but this factor isn't what's dragging
    // *this* prediction down — skip it rather than show ungrounded advice.
    if (combinedShap >= 0) continue;

    const reliability = absShapSum > 0 ? weightedEriSum / absShapSum : undefined;
    const magnitude = Math.abs(combinedShap) / maxAbsShap;

    const base = {
      id: rule.id,
      category: rule.category,
      featureNames: rule.featureNames,
      valueFeature: rule.valueFeature,
      currentValue: value,
      unit: rule.unit,
      shapValue: combinedShap,
      reliability,
      reliabilityTier: reliabilityTierFor(reliability),
      source: SOURCE_DOA_FAO,
    };

    if (rule.kind === "recommendation") {
      recommendations.push({
        ...base,
        kind: "recommendation",
        effectTier: effectTierFor(magnitude),
        recommendedRange: rule.range as [number, number],
      });
    } else {
      risks.push({
        ...base,
        kind: "risk",
        level: effectTierFor(magnitude),
        threshold: rule.threshold as number,
        comparison: rule.comparison as "above" | "below",
      });
    }
  }

  recommendations.sort((a, b) => Math.abs(b.shapValue) - Math.abs(a.shapValue));
  risks.sort((a, b) => Math.abs(b.shapValue) - Math.abs(a.shapValue));

  return { recommendations, risks };
}
