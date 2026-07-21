import { NextRequest, NextResponse } from "next/server";

import { getApiBaseUrl } from "@/lib/dailyDriverApi";

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const userId = searchParams.get("user_id");
  const date = searchParams.get("date");
  const limit = searchParams.get("limit") || "8";

  if (!userId || !date) {
    return NextResponse.json(
      { detail: "user_id and date are required." },
      { status: 400 },
    );
  }

  const params = new URLSearchParams({ date, limit });
  const endpoint = `${getApiBaseUrl()}/nutrition/${userId}/food-suggestions?${params.toString()}`;

  try {
    const response = await fetch(endpoint, {
      cache: "no-store",
      headers: {
        Accept: "application/json",
      },
    });
    const responsePayload = (await response.json().catch(() => null)) as
      | Record<string, unknown>
      | null;

    if (!response.ok) {
      return NextResponse.json(
        {
          detail:
            typeof responsePayload?.detail === "string"
              ? responsePayload.detail
              : "The backend could not return nutrition gap actions.",
        },
        { status: response.status },
      );
    }

    return NextResponse.json(responsePayload);
  } catch {
    return NextResponse.json(
      { detail: "Unable to reach the backend nutrition gap actions endpoint." },
      { status: 502 },
    );
  }
}
