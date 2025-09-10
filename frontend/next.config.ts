import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Enable standalone output for Docker containers
  output: "standalone",

  // Optimize for production builds
  poweredByHeader: false,
  reactStrictMode: true,
};

export default nextConfig;
