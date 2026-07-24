import type { NextConfig } from "next";

import { readRemoteAccessConfiguration } from "./src/lib/securityBoundary";

readRemoteAccessConfiguration();

const nextConfig: NextConfig = {
  /* config options here */
};

export default nextConfig;
