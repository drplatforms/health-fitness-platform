import { NextRequest, NextResponse } from "next/server";

import { getApiBaseUrl } from "@/lib/dailyDriverApi";

interface WorkoutSubstitutionRequestPayload {
  plan_instance_id?: number;
  planned_exercise_id?: number;
  replacement_catalog_exercise_id?: number;
}

export async function POST(request: NextRequest) {
  const payload = (await request.json().catch(() => null)) as
    | WorkoutSubstitutionRequestPayload
    | null;
  const planInstanceId = payload?.plan_instance_id;
  const plannedExerciseId = payload?.planned_exercise_id;
  const replacementCatalogExerciseId =
    payload?.replacement_catalog_exercise_id;

  if (
    !planInstanceId ||
    !plannedExerciseId ||
    !replacementCatalogExerciseId
  ) {
    return NextResponse.json(
      {
        detail:
          "plan_instance_id, planned_exercise_id, and replacement_catalog_exercise_id are required.",
      },
      { status: 400 },
    );
  }

  const endpoint = `${getApiBaseUrl()}/workout-plans/${planInstanceId}/planned-exercises/${plannedExerciseId}/substitute`;

  try {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        replacement_catalog_exercise_id: replacementCatalogExerciseId,
        substitution_reason: "user_selected",
      }),
    });
    const responsePayload = (await response.json().catch(() => null)) as
      | Record<string, unknown>
      | null;

    if (!response.ok) {
      return NextResponse.json(
        { detail: "Unable to apply that substitution." },
        { status: response.status },
      );
    }

    return NextResponse.json(responsePayload);
  } catch {
    return NextResponse.json(
      { detail: "Unable to apply that substitution." },
      { status: 502 },
    );
  }
}
