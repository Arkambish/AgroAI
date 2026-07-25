import { NextIntlClientProvider } from "next-intl";
import Navbar from "@/components/Navbar";
import { getSafeLocale, mergeMessages } from "@/i18n/routing";

export default async function LocaleLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  const safeLocale = getSafeLocale(locale);

  // Merge over English so any untranslated key degrades to English rather than
  // rendering a raw key. (This used to import the locale file directly, which
  // bypassed the fallback entirely.)
  const fallbackMessages = (await import("../../messages/en.json")).default;
  const localeMessages =
    safeLocale === "en"
      ? fallbackMessages
      : (await import(`../../messages/${safeLocale}.json`)).default;

  const messages = mergeMessages(
    fallbackMessages as Record<string, unknown>,
    localeMessages as Record<string, unknown>
  );

  return (
    <NextIntlClientProvider
      locale={safeLocale}
      messages={messages}
    >
      <Navbar />
      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {children}
      </main>
    </NextIntlClientProvider>
  );
}