import { NextRequest, NextResponse } from "next/server";

import { getApiBaseUrl } from "@/lib/dailyDriverApi";
import {
  buildBackendUrl,
  parsePositiveIntegerId,
} from "@/lib/securityBoundary";

interface RouteContext {
  params: Promise<{ mealId: string }>;
}

export async function POST(request: NextRequest, context: RouteContext) {
  const { mealId } = await context.params;
  const parsedMealId = parsePositiveIntegerId(mealId);
  if (parsedMealId === null) {
    return NextResponse.json(
      { detail: "meal_id must be a positive integer." },
      { status: 400 },
    );
  }
  const payload = (await request.json().catch(() => null)) as
    | { user_id?: number }
    | null;
  const userId = parsePositiveIntegerId(payload?.user_id);
  if (userId === null) {
    return NextResponse.json(
      { detail: "user_id must be a positive integer." },
      { status: 400 },
    );
  }
  try {
    const response = await fetch(
      buildBackendUrl(getApiBaseUrl(), "nutrition", [
        userId,
        "saved-meals",
        parsedMealId,
        "restore",
      ]),
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
