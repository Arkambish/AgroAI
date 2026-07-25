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
