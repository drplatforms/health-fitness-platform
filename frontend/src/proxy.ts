import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

import {
  authorizeRemoteRequest,
  readRemoteAccessConfiguration,
  validateApiProxyRequest,
} from "@/lib/securityBoundary";

const BASIC_CHALLENGE = 'Basic realm="Fitness", charset="UTF-8"';

export async function proxy(request: NextRequest) {
  let remoteAccess;
  try {
    remoteAccess = readRemoteAccessConfiguration();
  } catch {
    return new NextResponse("Remote access is not configured.", {
      status: 503,
    });
  }

  const accessDecision = authorizeRemoteRequest(request, remoteAccess);
  if (!accessDecision.ok) {
    if (accessDecision.status === 401) {
      return new NextResponse("Authentication required.", {
        status: 401,
        headers: {
          "Cache-Control": "no-store",
          "WWW-Authenticate": BASIC_CHALLENGE,
        },
      });
    }
    return new NextResponse("Request origin rejected.", {
      status: 403,
      headers: { "Cache-Control": "no-store" },
    });
  }

  if (request.nextUrl.pathname.startsWith("/api/")) {
    const validation = await validateApiProxyRequest(request);
    if (!validation.ok) {
      return NextResponse.json(
        { detail: validation.message ?? "Invalid proxy request." },
        { status: validation.status ?? 400 },
      );
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    // API requests must always cross the authentication, Origin, and route checks.
    "/api/:path*",
    // Only framework assets, exercise media, and exact public root assets are public.
    "/((?!_next/static(?:/|$)|_next/image(?:/|$)|exercise-media(?:/|$)|(?:favicon\\.ico|file\\.svg|globe\\.svg|next\\.svg|vercel\\.svg|window\\.svg)$).*)",
  ],
};
