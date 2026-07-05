import { NextRequest, NextResponse } from "next/server";

import { getApiBaseUrl } from "@/lib/dailyDriverApi";

interface WorkoutCompleteRequestPayload {
  plan_instance_id?: number;
}

export async function POST(request: NextRequest) {
  const payload = (await request.json().catch(() => null)) as
    | WorkoutCompleteRequestPayload
    | null;
  const planInstanceId = payload?.plan_instance_id;

  if (!planInstanceId) {
    return NextResponse.json(
      { detail: "plan_instance_id is required." },
      { status: 400 },
    );
  }

  const endpoint = `${getApiBaseUrl()}/workout-plans/${planInstanceId}/complete`;

  try {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: {
        Accept: "application/json",
      },
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
              : "The backend could not complete this workout.",
        },
        { status: response.status },
      );
    }

    return NextResponse.json(responsePayload);
  } catch {
    return NextResponse.json(
      { detail: "Unable to reach the backend workout completion endpoint." },
      { status: 502 },
    );
  }
}
