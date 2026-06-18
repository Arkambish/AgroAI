import type { NextConfig } from "next";
import path from "node:path";
import createNextIntlPlugin from "next-intl/plugin";

const withNextIntl = createNextIntlPlugin("./i18n/request.ts");

const nextConfig: NextConfig = {
  reactStrictMode: false, // 🔥 IMPORTANT for Leaflet stability
  // Pin Turbopack's workspace root to THIS folder. A stray package-lock.json in
  // the parent (FYP/Model) otherwise makes Next infer the wrong root, breaking
  // tailwindcss/postcss module resolution.
  turbopack: {
    root: path.join(__dirname),
  },
};

export default withNextIntl(nextConfig);