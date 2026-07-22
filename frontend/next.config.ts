import type { NextConfig } from "next";
import withSerwistInit from "@serwist/next";

const nextConfig: NextConfig = {
  /* config options here */
};

// Serwist generates the service worker via webpack (see package.json scripts,
// which opt out of Turbopack for `build`/`dev` with --webpack - Serwist does
// not yet support Turbopack, per Next.js's own PWA guide).
const withSerwist = withSerwistInit({
  swSrc: "src/app/sw.ts",
  swDest: "public/sw.js",
  disable: process.env.NODE_ENV === "development",
});

export default withSerwist(nextConfig);
