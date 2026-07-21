import { NextRequest, NextResponse } from "next/server";

import { getApiBaseUrl } from "@/lib/dailyDriverApi";

export async function GET(request: NextRequest) {
  const userId = request.nextUrl.searchParams.get("user_id")?.trim();
  const params = new URLSearchParams();
  if (userId) {
    params.set("user_id", userId);
  }
  try {
    const response = await fetch(
      `${getApiBaseUrl()}/foods/canonical/available-ingredient-starters?${params.toString()}`,
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
              : "The backend could not return quick-start ingredients.",
        },
        { status: response.status },
      );
    }
    return NextResponse.json(payload);
  } catch {
    return NextResponse.json(
      { detail: "Unable to reach the quick-start ingredients endpoint." },
      { status: 502 },
    );
  }
}
