import type { NextConfig } from "next";

// Market data (Yahoo Finance via yfinance) is served by the Flask backend in
// the repo root. The browser calls /api/* on this site; Next proxies it.
const flaskUrl = process.env.FLASK_API_URL ?? "http://127.0.0.1:5000";

const nextConfig: NextConfig = {
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${flaskUrl}/api/:path*` }];
  },
};

export default nextConfig;
