"use client";

import { useCallback, useSyncExternalStore } from "react";

const listeners = new Set<() => void>();

function subscribe(onChange: () => void) {
  listeners.add(onChange);
  window.addEventListener("storage", onChange);
  return () => {
    listeners.delete(onChange);
    window.removeEventListener("storage", onChange);
  };
}

/**
 * A boolean preference persisted in localStorage.
 *
 * Uses useSyncExternalStore rather than reading localStorage inside an effect,
 * so there is no setState-in-effect cascade and SSR gets a stable `false`.
 */
export function useLocalFlag(
  key: string
): [boolean, (next: boolean) => void] {
  const value = useSyncExternalStore(
    subscribe,
    () => localStorage.getItem(key) === "true",
    () => false
  );

  const setValue = useCallback(
    (next: boolean) => {
      localStorage.setItem(key, String(next));
      listeners.forEach((notify) => notify());
    },
    [key]
  );

  return [value, setValue];
}

// getSnapshot must return a referentially stable value or React re-renders
// forever, so cache the parse and only redo it when the raw string changes.
const jsonCache = new Map<string, { raw: string | null; parsed: unknown }>();

/**
 * Read a JSON value out of localStorage without a setState-in-effect cascade.
 * Returns null on the server and when the key is absent or unparseable.
 */
export function useLocalJSON<T>(key: string): T | null {
  return useSyncExternalStore(
    subscribe,
    () => {
      const raw = localStorage.getItem(key);
      const cached = jsonCache.get(key);
      if (!cached || cached.raw !== raw) {
        let parsed: unknown = null;
        try {
          parsed = raw ? JSON.parse(raw) : null;
        } catch {
          parsed = null;
        }
        jsonCache.set(key, { raw, parsed });
        return parsed as T | null;
      }
      return cached.parsed as T | null;
    },
    () => null
  );
}

/**
 * Same as useLocalJSON, but read/write — a useState-shaped API backed by
 * localStorage instead of a component-local fiber.
 *
 * Next.js's App Router only preserves component state across navigations
 * for layouts that stay mounted; page.tsx-level useState is torn down and
 * rebuilt on ANY URL change, including a locale-only change (e.g.
 * /en/predict -> /si/predict), since locale lives in the path. Backing
 * state like this in localStorage instead sidesteps that entirely — the
 * value is re-read fresh on every mount rather than relying on a component
 * instance surviving the navigation.
 */
export function useLocalJSONState<T>(
  key: string
): [T | null, (next: T | null) => void] {
  const value = useLocalJSON<T>(key);

  const setValue = useCallback(
    (next: T | null) => {
      if (next === null) {
        localStorage.removeItem(key);
      } else {
        localStorage.setItem(key, JSON.stringify(next));
      }
      listeners.forEach((notify) => notify());
    },
    [key]
  );

  return [value, setValue];
}

// Shared keys for the Predict/Explain/Recommend state — exported so every
// reader and writer (predict/page.tsx, explain/page.tsx, recommend/page.tsx,
// resetPrediction below) uses the exact same string, rather than each
// re-declaring their own copy that could drift out of sync.
export const PREDICTION_KEY = "last_prediction";
export const FARMER_INPUTS_KEY = "last_farmer_inputs";

/**
 * Centralized "New Prediction" action: clears the stored prediction result
 * (and with it, the SHAP values the Explain tab reads and the context the
 * Recommendation tab generates from) and the draft form inputs, so Explain/
 * Recommendation fall back to their "run a prediction first" placeholder
 * and the Predict form returns to its default state.
 *
 * Deliberately does NOT touch any other localStorage key — the locale
 * (routed, not stored) and preferences like agrisense_advanced_mode are
 * untouched. Plain function, not a hook: callable from any component
 * (Predict, Explain, or Recommendation's "New Prediction" button) without
 * needing to hold its own useLocalJSONState instance, and it notifies every
 * mounted subscriber so a same-page reset re-renders immediately.
 */
export function resetPrediction(): void {
  localStorage.removeItem(PREDICTION_KEY);
  localStorage.removeItem(FARMER_INPUTS_KEY);
  listeners.forEach((notify) => notify());
}
