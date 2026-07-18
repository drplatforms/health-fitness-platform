import { NextRequest, NextResponse } from "next/server";

import { getApiBaseUrl } from "@/lib/dailyDriverApi";

interface LimitationPayload {
  user_id?: number;
  affected_regions?: string[];
  restricted_movement_patterns?: string[];
  excluded_catalog_exercise_ids?: number[];
  expires_at?: string | null;
}

async function proxy(
  endpoint: string,
  method: "GET" | "PUT" | "DELETE",
  body?: Record<string, unknown>,
) {
  try {
    const response = await fetch(endpoint, {
      method,
      cache: "no-store",
      headers: {
        Accept: "application/json",
        ...(body ? { "Content-Type": "application/json" } : {}),
      },
      body: body ? JSON.stringify(body) : undefined,
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
              : "The backend could not update the temporary limitation.",
        },
        { status: response.status },
      );
    }
    return NextResponse.json(payload);
  } catch {
    return NextResponse.json(
      { detail: "Unable to reach the backend temporary-limitation endpoint." },
      { status: 502 },
    );
  }
}

export async function GET(request: NextRequest) {
  const userId = request.nextUrl.searchParams.get("user_id");
  if (!userId) {
    return NextResponse.json({ detail: "user_id is required." }, { status: 400 });
  }
  return proxy(
    `${getApiBaseUrl()}/users/${userId}/temporary-workout-limitation`,
    "GET",
  );
}

export async function PUT(request: NextRequest) {
  const payload = (await request.json().catch(() => null)) as
    | LimitationPayload
    | null;
  if (!payload?.user_id) {
    return NextResponse.json({ detail: "user_id is required." }, { status: 400 });
  }
  return proxy(
    `${getApiBaseUrl()}/users/${payload.user_id}/temporary-workout-limitation`,
    "PUT",
    {
      affected_regions: payload.affected_regions ?? [],
      restricted_movement_patterns:
        payload.restricted_movement_patterns ?? [],
      excluded_catalog_exercise_ids:
        payload.excluded_catalog_exercise_ids ?? [],
      expires_at: payload.expires_at ?? null,
    },
  );
}

export async function DELETE(request: NextRequest) {
  const payload = (await request.json().catch(() => null)) as
    | LimitationPayload
    | null;
  if (!payload?.user_id) {
    return NextResponse.json({ detail: "user_id is required." }, { status: 400 });
  }
  return proxy(
    `${getApiBaseUrl()}/users/${payload.user_id}/temporary-workout-limitation`,
    "DELETE",
  );
}
