import { NextRequest, NextResponse } from "next/server";

import { getApiBaseUrl } from "@/lib/dailyDriverApi";

export async function GET(request: NextRequest) {
  const userId = Number(request.nextUrl.searchParams.get("user_id"));
  if (!Number.isInteger(userId) || userId <= 0) {
    return NextResponse.json(
      { detail: "A valid user_id is required." },
      { status: 400 },
    );
  }

  const backendParams = new URLSearchParams();
  for (const name of [
    "lookback_days",
    "exercise_limit",
    "session_limit",
    "include_set_details",
  ]) {
    const value = request.nextUrl.searchParams.get(name);
    if (value !== null) {
      backendParams.set(name, value);
    }
  }
  const query = backendParams.toString();
  const sessionKey = request.nextUrl.searchParams.get("session_key");
  if (sessionKey !== null && !/^[a-f0-9]{20}$/.test(sessionKey)) {
    return NextResponse.json(
      { detail: "A valid session_key is required." },
      { status: 400 },
    );
  }
  const endpoint = sessionKey
    ? `${getApiBaseUrl()}/workout-plans/${userId}/exercise-history-analytics/sessions/${sessionKey}${query ? `?${query}` : ""}`
    : `${getApiBaseUrl()}/workout-plans/${userId}/exercise-history-analytics${query ? `?${query}` : ""}`;

  try {
    const response = await fetch(endpoint, {
      cache: "no-store",
      headers: { Accept: "application/json" },
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
              : "The backend could not return exercise history analytics.",
        },
        { status: response.status },
      );
    }
    return NextResponse.json(payload);
  } catch {
    return NextResponse.json(
      { detail: "Unable to reach the backend exercise history endpoint." },
      { status: 502 },
    );
  }
}
