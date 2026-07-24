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
  const { mealId } = await context.params;
  const parsedMealId = parsePositiveIntegerId(mealId);
  const userId = parsePositiveIntegerId(
    request.nextUrl.searchParams.get("user_id"),
  );
  if (parsedMealId === null || userId === null) {
    return NextResponse.json(
      { detail: "user_id and meal_id must be positive integers." },
      { status: 400 },
    );
  }
  return forward(
    buildBackendUrl(getApiBaseUrl(), "nutrition", [
      userId,
      "saved-meals",
      parsedMealId,
    ]),
    "GET",
  );
}

export async function PATCH(request: NextRequest, context: RouteContext) {
  const { mealId } = await context.params;
  const parsedMealId = parsePositiveIntegerId(mealId);
  if (parsedMealId === null) {
    return NextResponse.json(
      { detail: "meal_id must be a positive integer." },
      { status: 400 },
    );
  }
  const payload = (await request.json().catch(() => null)) as
    | Record<string, unknown>
    | null;
  const userId = parsePositiveIntegerId(payload?.user_id);
  if (userId === null) {
    return NextResponse.json(
      { detail: "user_id must be a positive integer." },
      { status: 400 },
    );
  }
  const body = { ...payload };
  delete body.user_id;
  return forward(
    buildBackendUrl(getApiBaseUrl(), "nutrition", [
      userId,
      "saved-meals",
      parsedMealId,
    ]),
    "PATCH",
    body,
  );
}

export async function DELETE(request: NextRequest, context: RouteContext) {
  const { mealId } = await context.params;
  const parsedMealId = parsePositiveIntegerId(mealId);
  if (parsedMealId === null) {
    return NextResponse.json(
      { detail: "meal_id must be a positive integer." },
      { status: 400 },
    );
  }
  const payload = (await request.json().catch(() => null)) as
    | Record<string, unknown>
    | null;
  const userId = parsePositiveIntegerId(payload?.user_id);
  if (userId === null) {
    return NextResponse.json(
      { detail: "user_id must be a positive integer." },
      { status: 400 },
    );
  }
  return forward(
    buildBackendUrl(getApiBaseUrl(), "nutrition", [
      userId,
      "saved-meals",
      parsedMealId,
    ]),
    "DELETE",
  );
}

async function forward(
  endpoint: string,
  method: "GET" | "PATCH" | "DELETE",
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
      ...(body ? { body: JSON.stringify(body) } : {}),
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
              : "The backend could not complete this meal request.",
        },
        { status: response.status },
      );
    }
    return NextResponse.json(payload);
  } catch {
    return NextResponse.json(
      { detail: "Unable to reach the saved meal endpoint." },
      { status: 502 },
    );
  }
}
