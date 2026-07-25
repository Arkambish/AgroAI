export const locales = ["en", "ta", "si"] as const;
export const defaultLocale = "en";

export type AppLocale = (typeof locales)[number];

export function isValidLocale(locale: string | undefined): locale is AppLocale {
  return locales.includes(locale as AppLocale);
}

export function getSafeLocale(locale: string | undefined): AppLocale {
  return isValidLocale(locale) ? locale : defaultLocale;
}

const isPlainObject = (v: unknown): v is Record<string, unknown> =>
  typeof v === "object" && v !== null && !Array.isArray(v);

/**
 * Deep-merge locale messages over the English fallback.
 *
 * A shallow spread replaced whole namespaces, so a `form` section in ta.json
 * missing one key rendered that key as a raw string instead of falling back to
 * English. Recursing means any untranslated key degrades to English.
 */
export function mergeMessages(
  fallbackMessages: Record<string, unknown>,
  localeMessages: Record<string, unknown>,
): Record<string, unknown> {
  const merged: Record<string, unknown> = { ...fallbackMessages };

  for (const [key, localeValue] of Object.entries(localeMessages)) {
    const fallbackValue = merged[key];
    if (isPlainObject(fallbackValue) && isPlainObject(localeValue)) {
      merged[key] = mergeMessages(fallbackValue, localeValue);
    } else if (localeValue !== undefined && localeValue !== "") {
      merged[key] = localeValue;
    }
  }

  return merged;
}
