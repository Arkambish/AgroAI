import { NextIntlClientProvider } from "next-intl";
import Navbar from "@/components/Navbar";

export default async function LocaleLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;

  const supportedLocales = ["en", "si", "ta"];
  const safeLocale = supportedLocales.includes(locale) ? locale : "en";

  const messages = (await import(`../../messages/${safeLocale}.json`))
    .default;

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