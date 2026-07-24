import { NextRequest, NextResponse } from "next/server";

import { getApiBaseUrl } from "@/lib/dailyDriverApi";
import {
  buildBackendUrl,
  parsePositiveIntegerId,
} from "@/lib/securityBoundary";

interface RouteContext {
  params: Promise<{ mealId: string }>;
}

export async function GET(request: NextRequest, context: RouteContext) {
  const { mealId: rawMealId } = await context.params;
  const mealId = parsePositiveIntegerId(rawMealId);
  const userId = parsePositiveIntegerId(
    request.nextUrl.searchParams.get("user_id"),
  );
  const multiplier = request.nextUrl.searchParams.get("multiplier") ?? "1";
  if (userId === null || mealId === null) {
    return NextResponse.json(
      { detail: "user_id and meal_id must be positive integers." },
      { status: 400 },
    );
  }
  try {
    const backendParams = new URLSearchParams({ multiplier });
    const response = await fetch(
      buildBackendUrl(
        getApiBaseUrl(),
        "nutrition",
        [userId, "saved-meals", mealId, "scaled"],
        backendParams,
      ),
      { cache: "no-store", headers: { Accept: "application/json" } },
    );
    const payload = await response.json().catch(() => null);
    return NextResponse.json(
      payload ?? { detail: "The backend returned no scaled recipe." },
      { status: response.status },
    );
  } catch {
    return NextResponse.json(
      { detail: "Unable to reach the recipe scaling endpoint." },
      { status: 502 },
    );
  }
}
