import { NextRequest, NextResponse } from "next/server";

import { getApiBaseUrl } from "@/lib/dailyDriverApi";

interface WeeklyPlanRequestPayload {
  user_id?: number;
  weekly_plan_id?: number;
  week_start_date?: string;
  training_weekdays?: number[];
  default_workout_size_preference?: string;
  current_date?: string;
}

async function forward(endpoint: string, init?: RequestInit) {
  try {
    const response = await fetch(endpoint, { cache: "no-store", ...init });
    const payload = (await response.json().catch(() => null)) as
      | Record<string, unknown>
      | null;
    if (!response.ok) {
      return NextResponse.json(
        {
          detail:
            typeof payload?.detail === "string"
              ? payload.detail
              : "The backend could not process the weekly training plan.",
        },
        { status: response.status },
      );
    }
    return NextResponse.json(payload);
  } catch {
    return NextResponse.json(
      { detail: "Unable to reach the backend weekly training plan endpoint." },
      { status: 502 },
    );
  }
}

export async function GET(request: NextRequest) {
  const userId = request.nextUrl.searchParams.get("user_id");
  const weekStartDate = request.nextUrl.searchParams.get("week_start_date");
  const currentDate = request.nextUrl.searchParams.get("current_date");
  if (!userId || !weekStartDate) {
    return NextResponse.json(
      { detail: "user_id and week_start_date are required." },
      { status: 400 },
    );
  }
  const params = new URLSearchParams({ week_start_date: weekStartDate });
  if (currentDate) {
    params.set("current_date", currentDate);
  }
  return forward(
    `${getApiBaseUrl()}/weekly-training-plans/${userId}?${params.toString()}`,
    { headers: { Accept: "application/json" } },
  );
}

export async function POST(request: NextRequest) {
  const payload = (await request.json().catch(() => null)) as
    | WeeklyPlanRequestPayload
    | null;
  if (
    !payload?.user_id ||
    !payload.week_start_date ||
    !payload.training_weekdays ||
    !payload.default_workout_size_preference
  ) {
    return NextResponse.json(
      { detail: "Weekly plan creation fields are required." },
      { status: 400 },
    );
  }
  return forward(
    `${getApiBaseUrl()}/weekly-training-plans/${payload.user_id}`,
    {
      method: "POST",
      headers: { Accept: "application/json", "Content-Type": "application/json" },
      body: JSON.stringify({
        week_start_date: payload.week_start_date,
        training_weekdays: payload.training_weekdays,
        default_workout_size_preference:
          payload.default_workout_size_preference,
        current_date: payload.current_date,
      }),
    },
  );
}

export async function PATCH(request: NextRequest) {
  const payload = (await request.json().catch(() => null)) as
    | WeeklyPlanRequestPayload
    | null;
  if (
    !payload?.user_id ||
    !payload.weekly_plan_id ||
    !payload.training_weekdays ||
    !payload.default_workout_size_preference ||
    !payload.current_date
  ) {
    return NextResponse.json(
      { detail: "Weekly plan update fields are required." },
      { status: 400 },
    );
  }
  return forward(
    `${getApiBaseUrl()}/weekly-training-plans/${payload.user_id}/${payload.weekly_plan_id}`,
    {
      method: "PATCH",
      headers: { Accept: "application/json", "Content-Type": "application/json" },
      body: JSON.stringify({
        training_weekdays: payload.training_weekdays,
        default_workout_size_preference:
          payload.default_workout_size_preference,
        current_date: payload.current_date,
      }),
    },
  );
}
