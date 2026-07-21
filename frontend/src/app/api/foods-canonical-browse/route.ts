import { NextRequest, NextResponse } from "next/server";

import { getApiBaseUrl } from "@/lib/dailyDriverApi";

export async function GET(request: NextRequest) {
  const params = new URLSearchParams();
  for (const key of [
    "user_id",
    "scope",
    "offset",
    "limit",
    "q",
    "start_letter",
  ]) {
    const value = request.nextUrl.searchParams.get(key)?.trim();
    if (value) {
      params.set(key, value);
    }
  }

  try {
    const response = await fetch(
      `${getApiBaseUrl()}/foods/canonical/browse?${params.toString()}`,
      {
        cache: "no-store",
        headers: { Accept: "application/json" },
      },
    );
    const payload = (await response.json().catch(() => null)) as
      | Record<string, unknown>
      | null;

    if (!response.ok) {
      return NextResponse.json(
        {
          detail:
            typeof payload?.detail === "string"
              ? payload.detail
              : "The backend could not return the food catalog.",
        },
        { status: response.status },
      );
    }

    return NextResponse.json(payload);
  } catch {
    return NextResponse.json(
      { detail: "Unable to reach the backend food catalog endpoint." },
      { status: 502 },
    );
  }
}
