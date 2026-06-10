import { getRequestConfig } from "next-intl/server";
import { getSafeLocale, mergeMessages } from "./routing";

export default getRequestConfig(async ({ requestLocale }) => {
  const requestedLocale = await requestLocale;
  const locale = getSafeLocale(requestedLocale);

  const fallbackMessages = (await import("../messages/en.json")).default;
  const localeMessages =
    locale === "en"
      ? fallbackMessages
      : (await import(`../messages/${locale}.json`)).default;

  return {
    locale,
    messages: mergeMessages(fallbackMessages, localeMessages),
    getMessageFallback({ key }) {
      return fallbackMessages[key as keyof typeof fallbackMessages] ?? key;
    },
  };
});
