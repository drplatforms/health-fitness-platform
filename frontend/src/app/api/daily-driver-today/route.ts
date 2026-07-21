import { NextRequest, NextResponse } from "next/server";

import { getApiBaseUrl } from "@/lib/dailyDriverApi";

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const userId = searchParams.get("user_id");
  const date = searchParams.get("date");

  if (!userId) {
    return NextResponse.json(
      { detail: "user_id is required." },
      { status: 400 },
    );
  }

  const params = new URLSearchParams({ user_id: userId });
  if (date) {
    params.set("date", date);
  }
  const endpoint = `${getApiBaseUrl()}/api/today?${params.toString()}`;

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
              : "The backend could not return Today.",
        },
        { status: response.status },
      );
    }

    return NextResponse.json(responsePayload);
  } catch {
    return NextResponse.json(
      { detail: "Unable to reach the backend Today endpoint." },
      { status: 502 },
    );
  }
}
