import { NextRequest, NextResponse } from "next/server";

import { getApiBaseUrl } from "@/lib/dailyDriverApi";
import { WorkoutProgressionDecisionRequestExercise } from "@/types/todayWorkout";

interface WorkoutProgressionDecisionRequestPayload {
  user_id?: number;
  target_date?: string;
  exercises?: WorkoutProgressionDecisionRequestExercise[];
}

export async function POST(request: NextRequest) {
  const payload = (await request.json().catch(() => null)) as
    | WorkoutProgressionDecisionRequestPayload
    | null;
  const userId = payload?.user_id;
  const targetDate = payload?.target_date;
  const exercises = payload?.exercises ?? [];

  if (!userId) {
    return NextResponse.json(
      { detail: "user_id is required." },
      { status: 400 },
    );
  }

  if (!targetDate) {
    return NextResponse.json(
      { detail: "target_date is required." },
      { status: 400 },
    );
  }

  if (!exercises.length) {
    return NextResponse.json(
      { detail: "exercises is required." },
      { status: 400 },
    );
  }

  const endpoint = `${getApiBaseUrl()}/workout-plans/${userId}/progression-decisions`;

  try {
    const response = await fetch(endpoint, {
      method: "POST",
      cache: "no-store",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        target_date: targetDate,
        exercises,
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
              : "The backend could not return workout progression decisions.",
        },
        { status: response.status },
      );
    }

    return NextResponse.json(responsePayload);
  } catch {
    return NextResponse.json(
      { detail: "Unable to reach the backend progression decision endpoint." },
      { status: 502 },
    );
  }
}
