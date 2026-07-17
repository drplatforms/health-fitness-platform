import { NextRequest, NextResponse } from "next/server";

import { getApiBaseUrl } from "@/lib/dailyDriverApi";
import { WorkoutExerciseMemoryIdentity } from "@/types/workoutExerciseMemory";

interface ResolvePayload {
  user_id?: number;
  exercises?: WorkoutExerciseMemoryIdentity[];
}

interface SavePayload extends Partial<WorkoutExerciseMemoryIdentity> {
  user_id?: number;
  memory_id?: number;
  memory_text?: string;
}

interface DeletePayload {
  user_id?: number;
  memory_id?: number;
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
              : "The backend could not update exercise memory.",
        },
        { status: response.status },
      );
    }
    return NextResponse.json(responsePayload);
  } catch {
    return NextResponse.json(
      { detail: "Unable to reach the backend exercise-memory endpoint." },
      { status: 502 },
    );
  }
}

export async function POST(request: NextRequest) {
  const payload = (await request.json().catch(() => null)) as
    | ResolvePayload
    | null;
  if (!payload?.user_id || !payload.exercises?.length) {
    return NextResponse.json(
      { detail: "user_id and exercises are required." },
      { status: 400 },
    );
  }
  return proxyResponse(
    `${getApiBaseUrl()}/workout-plans/${payload.user_id}/exercise-memories/resolve`,
    "POST",
    { exercises: payload.exercises },
  );
}

export async function PUT(request: NextRequest) {
  const payload = (await request.json().catch(() => null)) as SavePayload | null;
  if (!payload?.user_id || !payload.exercise_name || payload.memory_text === undefined) {
    return NextResponse.json(
      { detail: "user_id, exercise_name, and memory_text are required." },
      { status: 400 },
    );
  }
  return proxyResponse(
    `${getApiBaseUrl()}/workout-plans/${payload.user_id}/exercise-memories`,
    "PUT",
    {
      memory_id: payload.memory_id,
      catalog_exercise_id: payload.catalog_exercise_id,
      exercise_name: payload.exercise_name,
      memory_text: payload.memory_text,
    },
  );
}

export async function DELETE(request: NextRequest) {
  const payload = (await request.json().catch(() => null)) as
    | DeletePayload
    | null;
  if (!payload?.user_id || !payload.memory_id) {
    return NextResponse.json(
      { detail: "user_id and memory_id are required." },
      { status: 400 },
    );
  }
  return proxyResponse(
    `${getApiBaseUrl()}/workout-plans/${payload.user_id}/exercise-memories/${payload.memory_id}`,
    "DELETE",
  );
}
