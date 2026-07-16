import { NextRequest, NextResponse } from "next/server";

import { getApiBaseUrl } from "@/lib/dailyDriverApi";

export async function GET(request: NextRequest) {
  const planInstanceId = request.nextUrl.searchParams.get("plan_instance_id");
  const plannedExerciseId = request.nextUrl.searchParams.get(
    "planned_exercise_id",
  );

  if (!planInstanceId || !plannedExerciseId) {
    return NextResponse.json(
      { detail: "plan_instance_id and planned_exercise_id are required." },
      { status: 400 },
    );
  }

  const endpoint = `${getApiBaseUrl()}/workout-plans/${planInstanceId}/planned-exercises/${plannedExerciseId}/substitution-candidates`;

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
        { detail: "Unable to load substitutions right now." },
        { status: response.status },
      );
    }

    return NextResponse.json(payload);
  } catch {
    return NextResponse.json(
      { detail: "Unable to load substitutions right now." },
      { status: 502 },
    );
  }
}
