import { NextRequest, NextResponse } from "next/server";

import { getApiBaseUrl } from "@/lib/dailyDriverApi";

interface RouteContext {
  params: Promise<{ mealId: string }>;
}

export async function POST(request: NextRequest, context: RouteContext) {
  const { mealId } = await context.params;
  const payload = (await request.json().catch(() => null)) as
    | { user_id?: number }
    | null;
  if (!payload?.user_id) {
    return NextResponse.json({ detail: "user_id is required." }, { status: 400 });
  }
  try {
    const response = await fetch(
      `${getApiBaseUrl()}/nutrition/${payload.user_id}/saved-meals/${mealId}/restore`,
      { method: "POST", cache: "no-store", headers: { Accept: "application/json" } },
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
              : "The backend could not restore this meal.",
        },
        { status: response.status },
      );
    }
    return NextResponse.json(responsePayload);
  } catch {
    return NextResponse.json(
      { detail: "Unable to reach the saved meal restore endpoint." },
      { status: 502 },
    );
  }
}
