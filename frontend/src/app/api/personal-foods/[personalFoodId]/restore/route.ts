import { NextRequest, NextResponse } from "next/server";

import { getApiBaseUrl } from "@/lib/dailyDriverApi";
import {
  buildBackendUrl,
  parsePositiveIntegerId,
} from "@/lib/securityBoundary";

interface RouteContext {
  params: Promise<{ personalFoodId: string }>;
}

export async function POST(request: NextRequest, context: RouteContext) {
  const { personalFoodId } = await context.params;
  const parsedPersonalFoodId = parsePositiveIntegerId(personalFoodId);
  if (parsedPersonalFoodId === null) {
    return NextResponse.json(
      { detail: "personal_food_id must be a positive integer." },
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
  const endpoint = buildBackendUrl(getApiBaseUrl(), "nutrition", [
    userId,
    "personal-foods",
    parsedPersonalFoodId,
    "restore",
  ]);
  try {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: { Accept: "application/json" },
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
              : "The backend could not restore this food.",
        },
        { status: response.status },
      );
    }
    return NextResponse.json(responsePayload);
  } catch {
    return NextResponse.json(
      { detail: "Unable to reach the personal food restore endpoint." },
      { status: 502 },
    );
  }
}
