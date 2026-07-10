import { NextRequest, NextResponse } from "next/server";

import { getApiBaseUrl } from "@/lib/dailyDriverApi";

interface WorkoutProgressionHistoryRequestPayload {
  user_id?: number;
  exercise_names?: string[];
  lookback_days?: number;
  limit?: number;
}

export async function POST(request: NextRequest) {
  const payload = (await request.json().catch(() => null)) as
    | WorkoutProgressionHistoryRequestPayload
    | null;
  const userId = payload?.user_id;
  const exerciseNames = payload?.exercise_names ?? [];

  if (!userId) {
    return NextResponse.json(
      { detail: "user_id is required." },
      { status: 400 },
    );
  }

  if (!exerciseNames.length) {
    return NextResponse.json(
      { detail: "exercise_names is required." },
      { status: 400 },
    );
  }

  const endpoint = `${getApiBaseUrl()}/workout-plans/${userId}/progression-history`;

  try {
    const response = await fetch(endpoint, {
      method: "POST",
      cache: "no-store",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        exercise_names: exerciseNames,
        lookback_days: payload?.lookback_days,
        limit: payload?.limit,
      }),
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
              : "The backend could not return workout progression history.",
        },
        { status: response.status },
      );
    }

    return NextResponse.json(responsePayload);
  } catch {
    return NextResponse.json(
      { detail: "Unable to reach the backend workout progression history endpoint." },
      { status: 502 },
    );
  }
}
