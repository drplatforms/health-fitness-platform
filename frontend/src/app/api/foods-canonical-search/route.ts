import { NextRequest, NextResponse } from "next/server";

import { getApiBaseUrl } from "@/lib/dailyDriverApi";

export async function GET(request: NextRequest) {
  const query = request.nextUrl.searchParams.get("q")?.trim() ?? "";
  const limit = request.nextUrl.searchParams.get("limit")?.trim();
  const userId = request.nextUrl.searchParams.get("user_id")?.trim();

  if (!query) {
    return NextResponse.json({
      success: true,
      query: "",
      results: [],
    });
  }

  const params = new URLSearchParams({ q: query });
  if (limit) {
    params.set("limit", limit);
  }
  if (userId) {
    params.set("user_id", userId);
  }

  const endpoint = `${getApiBaseUrl()}/foods/canonical/search?${params.toString()}`;

  try {
    const response = await fetch(endpoint, {
      cache: "no-store",
      headers: {
        Accept: "application/json",
      },
    });
    const payload = (await response.json().catch(() => null)) as
      | Record<string, unknown>
      | null;

    if (!response.ok) {
      return NextResponse.json(
        {
          detail:
            typeof payload?.detail === "string"
              ? payload.detail
              : "The backend could not return canonical foods.",
        },
        { status: response.status },
      );
    }

    return NextResponse.json(payload);
  } catch {
    return NextResponse.json(
      { detail: "Unable to reach the backend food search endpoint." },
      { status: 502 },
    );
  }
}
