import type { NextConfig } from "next";
import path from "node:path";

const apiBase = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:5050";

const nextConfig: NextConfig = {
  // Pin Turbopack's workspace root to THIS folder. A stray package-lock.json in
  // the parent (FYP/Model) otherwise makes Next infer the wrong root, breaking
  // tailwindcss/postcss module resolution.
  turbopack: {
    root: path.join(__dirname),
  },
  async rewrites() {
    return [
      {
        source: "/api/backend/:path*",
        destination: `${apiBase}/:path*`,
      },
    ];
  },
};

export default nextConfig;
