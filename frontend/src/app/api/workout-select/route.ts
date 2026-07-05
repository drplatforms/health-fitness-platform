import { NextRequest, NextResponse } from "next/server";

import { getApiBaseUrl } from "@/lib/dailyDriverApi";

interface WorkoutSelectRequestPayload {
  user_id?: number;
  approved_workout_plan?: Record<string, unknown>;
}

export async function POST(request: NextRequest) {
  const payload = (await request.json().catch(() => null)) as
    | WorkoutSelectRequestPayload
    | null;
  const userId = payload?.user_id;
  const approvedWorkoutPlan = payload?.approved_workout_plan;

  if (!userId || !approvedWorkoutPlan) {
    return NextResponse.json(
      { detail: "user_id and approved_workout_plan are required." },
      { status: 400 },
    );
  }

  const endpoint = `${getApiBaseUrl()}/workout-plans/${userId}/select-preview`;

  try {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        approved_workout_plan: approvedWorkoutPlan,
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
              : "The backend could not save the visible workout preview.",
        },
        { status: response.status },
      );
    }

    return NextResponse.json(responsePayload);
  } catch {
    return NextResponse.json(
      { detail: "Unable to reach the backend workout selection endpoint." },
      { status: 502 },
    );
  }
}
