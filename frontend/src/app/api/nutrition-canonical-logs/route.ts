import { NextRequest, NextResponse } from "next/server";

import { getApiBaseUrl } from "@/lib/dailyDriverApi";

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const userId = searchParams.get("user_id");
  const date = searchParams.get("date");

  if (!userId || !date) {
    return NextResponse.json(
      { detail: "user_id and date are required." },
      { status: 400 },
    );
  }

  const params = new URLSearchParams({ date });
  const endpoint = `${getApiBaseUrl()}/nutrition/${userId}/canonical-logs?${params.toString()}`;

  try {
    const response = await fetch(endpoint, {
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
              : "The backend could not return logged foods.",
        },
        { status: response.status },
      );
    }

    return NextResponse.json(responsePayload);
  } catch {
    return NextResponse.json(
      { detail: "Unable to reach the backend logged foods endpoint." },
      { status: 502 },
    );
  }
}
