import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Ensure Prisma generated files and binaries are included in serverless functions
  outputFileTracingIncludes: {
    "**": [
      "./generated/prisma/**",
    ],
  },
};

export default nextConfig;
