import type { NextConfig } from "next";
import withSerwistInit from "@serwist/next";

const nextConfig: NextConfig = {
  // Allows the dev server to be reached from its LAN address (e.g. to test
  // camera capture on a phone on the same network), not just localhost.
  allowedDevOrigins: ["10.253.231.58"],
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
