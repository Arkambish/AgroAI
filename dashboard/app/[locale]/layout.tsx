import { NextIntlClientProvider } from "next-intl";
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "../globals.css";
import Navbar from "@/components/Navbar";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "AgroAI Dashboard | Onion Yield Prediction",
  description:
    "Farmer-friendly Explainable AI decision support system for big onion yield prediction.",
};

// ✅ FIX: params must be treated safely (async + no destructuring)
export default async function LocaleLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;

  // ✅ fallback to prevent undefined.json crash
  const supportedLocales = ["en", "si", "ta"];
  const safeLocale = supportedLocales.includes(locale) ? locale : "en";

  // ✅ safe dynamic import
  const messages = (await import(`../../messages/${safeLocale}.json`)).default;

  return (
    <html lang={safeLocale}>
      <body className={`${inter.className} min-h-screen antialiased`}>
        <NextIntlClientProvider locale={safeLocale} messages={messages}>
          <Navbar />
          <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
            {children}
          </main>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}