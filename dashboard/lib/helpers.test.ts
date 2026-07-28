/**
 * Pure display helpers. These decide what colour and label a farmer sees next to a yield,
 * so an off-by-one at a boundary is a visible wrong answer rather than a cosmetic slip.
 */

import { describe, expect, it } from "vitest";

import { getYieldCategory, getYieldColor, YIELD_CATEGORIES } from "@/lib/api";
import { ALL_FEATURE_META, EDITABLE_FEATURES, formatFeatureValue } from "@/lib/features";
import en from "@/messages/en.json";

describe("getYieldCategory", () => {
  it.each([
    [20, "Very High"],
    [16, "Very High"],
    [15.99, "High"],
    [13, "High"],
    [12.99, "Medium"],
    [10, "Medium"],
    [9.99, "Low"],
    [7, "Low"],
    [6.99, "Very Low"],
    [0, "Very Low"],
  ])("classifies %s as %s", (value, label) => {
    expect(getYieldCategory(value).label).toBe(label);
  });

  it("degrades to a neutral grey rather than guessing when the value is missing", () => {
    const missing = getYieldCategory(undefined);
    expect(missing.color).toBe("#cbd5e1");
    // Must not be mistaken for the real "Medium" band's styling.
    expect(missing.color).not.toBe(YIELD_CATEGORIES[2].color);
  });

  it("treats NaN as missing, not as very low", () => {
    expect(getYieldCategory(Number.NaN).color).toBe("#cbd5e1");
  });

  it("never returns an undefined category for any finite input", () => {
    for (let v = -5; v <= 40; v += 0.5) {
      expect(getYieldCategory(v)).toBeDefined();
      expect(getYieldColor(v)).toMatch(/^#[0-9a-f]{6}$/i);
    }
  });
});

describe("formatFeatureValue", () => {
  const meta = { name: "x", labelKey: "x", unit: "mm", decimals: 1 };

  it("renders an em dash rather than 'NaN' or '0' when the value is absent", () => {
    expect(formatFeatureValue(undefined, meta)).toBe("—");
    expect(formatFeatureValue(Number.NaN, meta)).toBe("—");
  });

  it("keeps zero as a real measurement", () => {
    // Zero is a genuine reading for rainfall; it must not be shown as missing.
    expect(formatFeatureValue(0, meta)).toBe("0.0 mm");
  });

  it("respects the declared precision and unit", () => {
    expect(formatFeatureValue(12.345, meta)).toBe("12.3 mm");
    expect(
      formatFeatureValue(12.345, { name: "y", labelKey: "y", unit: "", decimals: 2 }),
    ).toBe("12.35");
  });
});

describe("feature metadata", () => {
  it("declares a unique name for every feature", () => {
    const names = ALL_FEATURE_META.map((f) => f.name);
    expect(new Set(names).size).toBe(names.length);
  });

  it("exposes exactly the features marked editable", () => {
    expect(EDITABLE_FEATURES.length).toBeGreaterThan(0);
    expect(EDITABLE_FEATURES.every((f) => f.editable)).toBe(true);
  });

  it("gives every feature a translatable label key and a sane precision", () => {
    for (const f of ALL_FEATURE_META) {
      expect(f.labelKey, `${f.name} has no labelKey`).toBeTruthy();
      expect(f.decimals, `${f.name} has bad precision`).toBeGreaterThanOrEqual(0);
    }
  });

  it("resolves every labelKey against the message catalogue", () => {
    // A labelKey with no entry under `features.*` renders the raw key to the user.
    const catalogue = en.features as Record<string, string>;
    const unresolved = ALL_FEATURE_META.filter((f) => !catalogue[f.labelKey]);
    expect(unresolved.map((f) => f.labelKey)).toEqual([]);
  });

  it("gives every editable feature a usable range", () => {
    for (const f of EDITABLE_FEATURES) {
      expect(f.min, `${f.name} has no min`).toBeTypeOf("number");
      expect(f.max, `${f.name} has no max`).toBeTypeOf("number");
      expect(f.max!, `${f.name} has an inverted range`).toBeGreaterThan(f.min!);
    }
  });
});
