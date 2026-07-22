import { NextRequest, NextResponse } from "next/server";

import { getApiBaseUrl } from "@/lib/dailyDriverApi";

interface RecoveryCheckInRequestPayload {
  user_id?: number;
  target_date?: string;
  body_weight?: number | null;
  sleep_hours?: number;
  sleep_quality?: number | null;
  energy_level?: number;
  soreness_level?: number;
  stress_level?: number | null;
  training_motivation?: number | null;
  pain_concern?: "none" | "mild" | "significant" | null;
  pain_area?: string | null;
  mood?: string | null;
  notes?: string | null;
}

export async function GET(request: NextRequest) {
  const userId = request.nextUrl.searchParams.get("user_id");
  const targetDate = request.nextUrl.searchParams.get("date");

  if (!userId) {
    return NextResponse.json(
      { detail: "user_id is required." },
      { status: 400 },
    );
  }

  const params = new URLSearchParams();
  if (targetDate) {
    params.set("target_date", targetDate);
  }

  const endpoint = `${getApiBaseUrl()}/recovery/checkins/${userId}${params.size ? `?${params.toString()}` : ""}`;

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
        {
          detail:
            typeof payload?.detail === "string"
              ? payload.detail
              : "The backend could not return today's recovery check-in.",
        },
        { status: response.status },
      );
    }

    return NextResponse.json(payload);
  } catch {
    return NextResponse.json(
      { detail: "Unable to reach the backend recovery check-in endpoint." },
      { status: 502 },
    );
  }
}

export async function POST(request: NextRequest) {
  const payload = (await request.json().catch(() => null)) as
    | RecoveryCheckInRequestPayload
    | null;

  if (
    !payload?.user_id ||
    payload.sleep_hours === undefined ||
    payload.energy_level === undefined ||
    payload.soreness_level === undefined
  ) {
    return NextResponse.json(
      {
        detail:
          "user_id, sleep_hours, energy_level, and soreness_level are required.",
      },
      { status: 400 },
    );
  }

  const endpoint = `${getApiBaseUrl()}/recovery/checkins`;

  try {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
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
              : "The backend could not save today's recovery check-in.",
        },
        { status: response.status },
      );
    }

    return NextResponse.json(responsePayload);
  } catch {
    return NextResponse.json(
      { detail: "Unable to reach the backend recovery save endpoint." },
      { status: 502 },
    );
  }
}
