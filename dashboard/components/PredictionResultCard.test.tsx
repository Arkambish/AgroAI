/**
 * The result card is the one surface that can misrepresent the model to a farmer.
 *
 * It no longer shows any technical explanation of where feature values came from
 * (historical average / exact record / climatological basis) — that clutter was
 * removed in favour of always showing the requested district/season/year. SHAP
 * explainability was also moved out of this card entirely — it now lives only on
 * the Explainability tab (app/[locale]/explain/page.tsx), as per-factor cards —
 * so this card stays focused on inputs, the result, and confidence info, with a
 * link out for the full breakdown. These tests render against the REAL message
 * catalogue so a missing or renamed translation key fails here rather than in
 * production as a raw key string.
 */

import { render, screen } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { describe, expect, it } from "vitest";

import PredictionResultCard from "@/components/PredictionResultCard";
import type { PredictResponse } from "@/lib/api";
import en from "@/messages/en.json";

const baseResult: PredictResponse = {
  district: "Polonnaruwa",
  season: "Yala",
  year: 2024,
  predicted_yield_MT_per_Ha: 16.16,
  confidence_lower: 0,
  confidence_upper: 33.9,
  confidence: "Low",
  shap_values: {},
  model: "SVR",
  model_r2: -0.3068,
  interval_method: "conformal_90pct",
  forecast_basis: {
    basis: "climatological",
    year_is_model_feature: false,
    year_affects_prediction: false,
    n_observed_inputs: 0,
    note: "No observed values were supplied.",
  },
};

function renderCard(overrides: Partial<PredictResponse> = {}) {
  return render(
    <NextIntlClientProvider locale="en" messages={en}>
      <PredictionResultCard
        result={{ ...baseResult, ...overrides }}
        baseline={null}
        locale="en"
      />
    </NextIntlClientProvider>,
  );
}

describe("PredictionResultCard — no data-provenance clutter", () => {
  it("always shows the district, season and requested year, regardless of forecast_basis", () => {
    renderCard();
    expect(screen.getByText(/Yala 2024/)).toBeInTheDocument();
  });

  it("shows the year the same way for a conditioned prediction", () => {
    renderCard({
      forecast_basis: {
        basis: "conditioned",
        year_is_model_feature: false,
        year_affects_prediction: true,
        n_observed_inputs: 2,
        note: "Conditioned on 2 values you supplied.",
      },
    });
    expect(screen.getByText(/Yala 2024/)).toBeInTheDocument();
  });

  it("shows the year the same way when the backend reports no forecast_basis at all", () => {
    renderCard({ forecast_basis: undefined });
    expect(screen.getByText(/Yala 2024/)).toBeInTheDocument();
  });

  it("never mentions historical averages, exact records or climatological basis", () => {
    const { container } = renderCard();
    const text = container.textContent ?? "";
    expect(text).not.toMatch(/historical average/i);
    expect(text).not.toMatch(/exact record/i);
    expect(text).not.toMatch(/climatological/i);
    expect(text).not.toMatch(/all years/i);
  });

  it("renders no translation keys as literal text", () => {
    const { container } = renderCard();
    // A missing key renders as e.g. "predict.expectedRange"; catch that shape anywhere.
    expect(container.textContent ?? "").not.toMatch(/\bpredict\.[a-zA-Z]+/);
  });
});

describe("PredictionResultCard — honest presentation", () => {
  it("leads with the interval rather than the point estimate", () => {
    renderCard();
    expect(screen.getByText(en.predict.expectedRange)).toBeInTheDocument();
    expect(screen.getByText("0.0")).toBeInTheDocument();
    expect(screen.getByText("33.9")).toBeInTheDocument();
  });

  it("names the model that actually produced the number", () => {
    renderCard({ model: "SVR" });
    expect(screen.getByText(/Model: SVR/)).toBeInTheDocument();
  });

  it("describes how the interval was produced", () => {
    renderCard();
    expect(screen.getByText(/conformal prediction interval/i)).toBeInTheDocument();
  });

  it("reports low reliability for a negative R²", () => {
    renderCard({ model_r2: -0.3068 });
    expect(screen.getByText(/rough guide only, not a forecast/i)).toBeInTheDocument();
  });
});

describe("PredictionResultCard — no SHAP explanation on the Predict tab", () => {
  // SHAP explainability now lives only on the Explainability tab (see
  // app/[locale]/explain/page.tsx, rendered as per-factor cards) — the
  // Predict tab stays focused on inputs, the result, and confidence info.
  // It still links to the Explainability tab for the full breakdown.
  it("never renders any SHAP factor explanation, even with a populated shap_values", () => {
    renderCard({
      shap_values: {
        season_total_rainfall: 1.2,
        season_avg_temp: -0.8,
      },
    });

    expect(screen.queryByText(/what influenced this prediction/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/increased your expected yield/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/reduced your expected yield/i)).not.toBeInTheDocument();
  });

  it("still links to the Explainability tab for the full breakdown", () => {
    renderCard();
    expect(screen.getByText(en.predict.whyPrediction)).toBeInTheDocument();
  });
});
