import { NextRequest, NextResponse } from "next/server";

import { getApiBaseUrl } from "@/lib/dailyDriverApi";

interface RouteContext {
  params: Promise<{ mealId: string }>;
}

export async function POST(request: NextRequest, context: RouteContext) {
  const { mealId } = await context.params;
  const payload = (await request.json().catch(() => null)) as
    | { user_id?: number; entry_date?: string; meal_type?: string }
    | null;
  if (!payload?.user_id || !payload.entry_date) {
    return NextResponse.json(
      { detail: "user_id and entry_date are required." },
      { status: 400 },
    );
  }
  try {
    const response = await fetch(
      `${getApiBaseUrl()}/nutrition/${payload.user_id}/saved-meals/${mealId}/log`,
      {
        method: "POST",
        cache: "no-store",
        headers: { Accept: "application/json", "Content-Type": "application/json" },
        body: JSON.stringify({
          entry_date: payload.entry_date,
          meal_type: payload.meal_type,
        }),
      },
    );
    const responsePayload = (await response.json().catch(() => null)) as
      | Record<string, unknown>
      | null;
    if (!response.ok) {
      return NextResponse.json(
        {
          detail:
            typeof responsePayload?.detail === "string"
              ? responsePayload.detail
              : "The backend could not log this meal.",
        },
        { status: response.status },
      );
    }
    return NextResponse.json(responsePayload);
  } catch {
    return NextResponse.json(
      { detail: "Unable to reach the saved meal logging endpoint." },
      { status: 502 },
    );
  }
}
