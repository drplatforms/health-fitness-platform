import { NextRequest, NextResponse } from "next/server";

import { getApiBaseUrl } from "@/lib/dailyDriverApi";
import type {
  WorkoutExerciseFamiliarity,
  WorkoutExercisePreference,
} from "@/types/workoutExerciseProfile";

interface ResolvePayload {
  user_id?: number;
  catalog_exercise_ids?: number[];
}

interface SavePayload {
  user_id?: number;
  catalog_exercise_id?: number;
  familiarity_state?: WorkoutExerciseFamiliarity | null;
  preference_state?: WorkoutExercisePreference | null;
}

interface DeletePayload {
  user_id?: number;
  catalog_exercise_id?: number;
}

async function proxyResponse(
  endpoint: string,
  method: "POST" | "PUT" | "DELETE",
  body?: Record<string, unknown>,
) {
  try {
    const response = await fetch(endpoint, {
      method,
      cache: "no-store",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: body ? JSON.stringify(body) : undefined,
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
              : "The backend could not update exercise profile.",
        },
        { status: response.status },
      );
    }
    return NextResponse.json(responsePayload);
  } catch {
    return NextResponse.json(
      { detail: "Unable to reach the backend exercise-profile endpoint." },
      { status: 502 },
    );
  }
}

export async function POST(request: NextRequest) {
  const payload = (await request.json().catch(() => null)) as
    | ResolvePayload
    | null;
  if (!payload?.user_id || !payload.catalog_exercise_ids?.length) {
    return NextResponse.json(
      { detail: "user_id and catalog_exercise_ids are required." },
      { status: 400 },
    );
  }
  return proxyResponse(
    `${getApiBaseUrl()}/workout-plans/${payload.user_id}/exercise-profiles/resolve`,
    "POST",
    { catalog_exercise_ids: payload.catalog_exercise_ids },
  );
}

export async function PUT(request: NextRequest) {
  const payload = (await request.json().catch(() => null)) as SavePayload | null;
  if (!payload?.user_id || !payload.catalog_exercise_id) {
    return NextResponse.json(
      { detail: "user_id and catalog_exercise_id are required." },
      { status: 400 },
    );
  }
  return proxyResponse(
    `${getApiBaseUrl()}/workout-plans/${payload.user_id}/exercise-profiles`,
    "PUT",
    {
      catalog_exercise_id: payload.catalog_exercise_id,
      familiarity_state: payload.familiarity_state ?? null,
      preference_state: payload.preference_state ?? null,
    },
  );
}

export async function DELETE(request: NextRequest) {
  const payload = (await request.json().catch(() => null)) as
    | DeletePayload
    | null;
  if (!payload?.user_id || !payload.catalog_exercise_id) {
    return NextResponse.json(
      { detail: "user_id and catalog_exercise_id are required." },
      { status: 400 },
    );
  }
  return proxyResponse(
    `${getApiBaseUrl()}/workout-plans/${payload.user_id}/exercise-profiles/${payload.catalog_exercise_id}`,
    "DELETE",
  );
}
