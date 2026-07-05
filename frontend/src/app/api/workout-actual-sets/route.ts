import { NextRequest, NextResponse } from "next/server";

import { getApiBaseUrl } from "@/lib/dailyDriverApi";

interface WorkoutActualSetRequestPayload {
  plan_instance_id?: number;
  planned_workout_exercise_id?: number;
  exercise_name?: string;
  set_number?: number;
  actual_reps?: number;
  actual_weight?: number;
  actual_rir?: number;
  completed?: boolean;
  skipped?: boolean;
  substitution_for_planned_exercise_id?: number;
  notes?: string;
}

export async function POST(request: NextRequest) {
  const payload = (await request.json().catch(() => null)) as
    | WorkoutActualSetRequestPayload
    | null;
  const planInstanceId = payload?.plan_instance_id;

  if (!planInstanceId) {
    return NextResponse.json(
      { detail: "plan_instance_id is required." },
      { status: 400 },
    );
  }

  const endpoint = `${getApiBaseUrl()}/workout-plans/${planInstanceId}/actual-sets`;

  try {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        planned_workout_exercise_id: payload?.planned_workout_exercise_id,
        exercise_name: payload?.exercise_name,
        set_number: payload?.set_number,
        actual_reps: payload?.actual_reps,
        actual_weight: payload?.actual_weight,
        actual_rir: payload?.actual_rir,
        completed: payload?.completed,
        skipped: payload?.skipped,
        substitution_for_planned_exercise_id:
          payload?.substitution_for_planned_exercise_id,
        notes: payload?.notes,
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
              : "The backend could not save that actual set.",
        },
        { status: response.status },
      );
    }

    return NextResponse.json(responsePayload);
  } catch {
    return NextResponse.json(
      { detail: "Unable to reach the backend workout actual-set endpoint." },
      { status: 502 },
    );
  }
}
