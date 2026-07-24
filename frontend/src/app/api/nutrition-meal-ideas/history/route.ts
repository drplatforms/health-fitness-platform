import { NextRequest, NextResponse } from "next/server";

import { getApiBaseUrl } from "@/lib/dailyDriverApi";
import {
  buildBackendUrl,
  parsePositiveIntegerId,
} from "@/lib/securityBoundary";

export async function GET(request: NextRequest) {
  const userId = parsePositiveIntegerId(
    request.nextUrl.searchParams.get("user_id"),
  );
  if (userId === null) {
    return NextResponse.json(
      { detail: "user_id must be a positive integer." },
      { status: 400 },
    );
  }

  try {
    const response = await fetch(
      buildBackendUrl(getApiBaseUrl(), "nutrition", [
        userId,
        "meal-ideas",
        "history",
      ]),
      { cache: "no-store", headers: { Accept: "application/json" } },
    );
    const payload = await response.json().catch(() => null);
    return NextResponse.json(
      payload ?? { detail: "The backend returned an empty generation-history response." },
      { status: response.status },
    );
  } catch {
    return NextResponse.json(
      { detail: "Unable to reach meal idea history." },
      { status: 502 },
    );
  }
}
