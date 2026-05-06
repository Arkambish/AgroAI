import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import "leaflet/dist/leaflet.css";
import { SelectionProvider } from "@/components/selection-context";
import { HeaderBranding, SiteNav } from "@/components/site-nav";
import { GlobalSelector } from "@/components/global-selector";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Agro AI · Big Onion Yield Predictor",
  description:
    "Decision-support dashboard for big onion (Allium cepa) yield prediction across Matale, Anuradhapura, Polonnaruwa, and Jaffna districts.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        <SelectionProvider>
          <header className="border-b border-slate-200 bg-white/90 backdrop-blur dark:border-slate-800 dark:bg-slate-950/80 sticky top-0 z-40">
            <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-4 py-3 lg:px-6">
              <HeaderBranding />
              <SiteNav />
            </div>
          </header>

          <div className="mx-auto flex w-full max-w-7xl flex-1 gap-6 px-4 py-6 lg:px-6">
            <aside className="hidden w-60 shrink-0 lg:block">
              <div className="sticky top-20 rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
                <h2 className="mb-3 text-sm font-semibold">Selection</h2>
                <GlobalSelector />
                <p className="mt-3 text-xs text-slate-500 dark:text-slate-400">
                  Choices persist in your browser and are shared across pages.
                </p>
              </div>
            </aside>
            <main className="min-w-0 flex-1 space-y-6">{children}</main>
          </div>

          <footer className="border-t border-slate-200 py-6 text-center text-xs text-slate-500 dark:border-slate-800 dark:text-slate-400">
            Agro AI · FYP 2026 · University of Moratuwa, Faculty of IT
          </footer>
        </SelectionProvider>
      </body>
    </html>
  );
}
