export const locales = ["en", "ta", "si"] as const;
export const defaultLocale = "en";

export type AppLocale = (typeof locales)[number];

export function isValidLocale(locale: string | undefined): locale is AppLocale {
  return locales.includes(locale as AppLocale);
}

export function getSafeLocale(locale: string | undefined): AppLocale {
  return isValidLocale(locale) ? locale : defaultLocale;
}

export function mergeMessages(
  fallbackMessages: Record<string, string>,
  localeMessages: Record<string, string>,
) {
  return {
    ...fallbackMessages,
    ...localeMessages,
  };
}
