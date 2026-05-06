"use client";

import * as React from "react";
import { DISTRICTS, SEASONS } from "@/lib/constants";
import type { District, Season } from "@/lib/types";

interface SelectionState {
  district: District;
  season: Season;
  year: number;
  setDistrict: (d: District) => void;
  setSeason: (s: Season) => void;
  setYear: (y: number) => void;
}

const SelectionContext = React.createContext<SelectionState | null>(null);

const STORAGE_KEY = "agroai-selection";

interface PersistedSelection {
  district: District;
  season: Season;
  year: number;
}

function loadPersisted(): PersistedSelection | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as PersistedSelection;
    if (!DISTRICTS.includes(parsed.district)) return null;
    if (!SEASONS.includes(parsed.season)) return null;
    return parsed;
  } catch {
    return null;
  }
}

const DEFAULTS: PersistedSelection = { district: "Matale", season: "Yala", year: 2023 };

export function SelectionProvider({ children }: { readonly children: React.ReactNode }) {
  // Store all three together so persistence stays atomic.
  const [state, setState] = React.useState<PersistedSelection>(() => {
    // Lazy initialiser runs once, client-side, on first render.
    // On the server this returns DEFAULTS — the client then re-renders with
    // persisted state via the subscription below.
    return loadPersisted() ?? DEFAULTS;
  });

  const setDistrict = React.useCallback(
    (d: District) =>
      setState((s) => {
        const next = { ...s, district: d };
        try {
          window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
        } catch {
          /* ignore quota errors */
        }
        return next;
      }),
    [],
  );

  const setSeason = React.useCallback(
    (season: Season) =>
      setState((s) => {
        const next = { ...s, season };
        try {
          window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
        } catch {
          /* ignore */
        }
        return next;
      }),
    [],
  );

  const setYear = React.useCallback(
    (y: number) =>
      setState((s) => {
        const next = { ...s, year: y };
        try {
          window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
        } catch {
          /* ignore */
        }
        return next;
      }),
    [],
  );

  const value: SelectionState = React.useMemo(
    () => ({
      district: state.district,
      season: state.season,
      year: state.year,
      setDistrict,
      setSeason,
      setYear,
    }),
    [state, setDistrict, setSeason, setYear],
  );

  return <SelectionContext.Provider value={value}>{children}</SelectionContext.Provider>;
}

export function useSelection(): SelectionState {
  const ctx = React.useContext(SelectionContext);
  if (!ctx) {
    throw new Error("useSelection must be used inside <SelectionProvider>");
  }
  return ctx;
}
