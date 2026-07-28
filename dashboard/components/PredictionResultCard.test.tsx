/**
 * The result card is the one surface that can misrepresent the model to a farmer.
 *
 * It previously stamped the requested year onto a number that did not depend on the year,
 * which reads as a forecast for that year and is not one. These tests pin the honest
 * behaviour, and they render against the REAL message catalogue so a missing or renamed
 * translation key fails here rather than in production as a raw key string.
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

describe("PredictionResultCard — forecast basis", () => {
  it("warns that a climatological result is not a forecast for the requested year", () => {
    renderCard();
    expect(screen.getByText(/not a forecast for 2024/i)).toBeInTheDocument();
    expect(
      screen.getByText(/returns this same number for every year/i),
    ).toBeInTheDocument();
  });

  it("does not stamp the requested year onto a climatological number", () => {
    renderCard();
    expect(screen.getByText(/all years/i)).toBeInTheDocument();
    expect(screen.queryByText(/Yala 2024/)).not.toBeInTheDocument();
  });

  it("shows the year once the prediction is conditioned on observations", () => {
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
    expect(screen.queryByText(/not a forecast for/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/all years/i)).not.toBeInTheDocument();
  });

  it("stays silent about the basis when the backend does not report one", () => {
    // Older API builds omit forecast_basis entirely; the card must not claim either way.
    renderCard({ forecast_basis: undefined });
    expect(screen.queryByText(/not a forecast for/i)).not.toBeInTheDocument();
    expect(screen.getByText(/Yala 2024/)).toBeInTheDocument();
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

  it("renders no translation keys as literal text", () => {
    const { container } = renderCard();
    // A missing key renders as e.g. "predict.basisAllYears"; catch that shape anywhere.
    expect(container.textContent ?? "").not.toMatch(/\bpredict\.[a-zA-Z]+/);
  });
});
