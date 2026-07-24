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
    | { user_id?: number; provider?: string; model?: string }
    | null;
  const userId = parsePositiveIntegerId(payload?.user_id);
  if (userId === null || !payload?.provider) {
    return NextResponse.json(
      { detail: "user_id and provider are required and valid." },
      { status: 400 },
    );
  }
  try {
    const response = await fetch(
      buildBackendUrl(getApiBaseUrl(), "nutrition", [
        userId,
        "saved-meals",
        parsedMealId,
        "instructions",
      ]),
      {
        method: "POST",
        cache: "no-store",
        headers: { Accept: "application/json", "Content-Type": "application/json" },
        body: JSON.stringify({ provider: payload.provider, model: payload.model }),
      },
    );
    const responsePayload = await response.json().catch(() => null);
    return NextResponse.json(
      responsePayload ?? { detail: "The backend returned no cooking instructions." },
      { status: response.status },
    );
  } catch {
    return NextResponse.json(
      { detail: "Unable to reach the saved recipe instructions endpoint." },
      { status: 502 },
    );
  }
}
