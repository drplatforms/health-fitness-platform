import { NextRequest, NextResponse } from "next/server";

import { getApiBaseUrl } from "@/lib/dailyDriverApi";
import {
  buildBackendUrl,
  parsePositiveIntegerId,
} from "@/lib/securityBoundary";

async function backendJson(response: Response) {
  return (await response.json().catch(() => null)) as
    | Record<string, unknown>
    | null;
}

function backendError(payload: Record<string, unknown> | null, fallback: string) {
  return {
    detail: typeof payload?.detail === "string" ? payload.detail : fallback,
  };
}

function requestIdentity(request: NextRequest) {
  const params = request.nextUrl.searchParams;
  return {
    userId: parsePositiveIntegerId(params.get("user_id")),
    foodType: params.get("food_type"),
    foodId: parsePositiveIntegerId(params.get("food_id")),
  };
}

export async function GET(request: NextRequest) {
  const { userId } = requestIdentity(request);
  if (userId === null) {
    return NextResponse.json(
      { detail: "user_id must be a positive integer." },
      { status: 400 },
    );
  }
  return proxyPinnedFoods(
    buildBackendUrl(getApiBaseUrl(), "nutrition", [userId, "pinned-foods"]),
  );
}

export async function PUT(request: NextRequest) {
  return mutatePinnedFood(request, "PUT");
}

export async function DELETE(request: NextRequest) {
  return mutatePinnedFood(request, "DELETE");
}

async function mutatePinnedFood(request: NextRequest, method: "PUT" | "DELETE") {
  const { userId, foodType, foodId } = requestIdentity(request);
  if (
    userId === null ||
    foodId === null ||
    !foodType ||
    !["canonical", "personal"].includes(foodType)
  ) {
    return NextResponse.json(
      {
        detail:
          "user_id and food_id must be positive integers and food_type must be canonical or personal.",
      },
      { status: 400 },
    );
  }
  return proxyPinnedFoods(
    buildBackendUrl(getApiBaseUrl(), "nutrition", [
      userId,
      "pinned-foods",
      foodType,
      foodId,
    ]),
    method,
  );
}

async function proxyPinnedFoods(endpoint: string, method: "GET" | "PUT" | "DELETE" = "GET") {
  try {
    const response = await fetch(endpoint, {
      method,
      cache: "no-store",
      headers: { Accept: "application/json" },
    });
    const payload = await backendJson(response);
    if (!response.ok) {
      return NextResponse.json(
        backendError(payload, "The backend could not update pinned foods."),
        { status: response.status },
      );
    }
    return NextResponse.json(payload);
  } catch {
    return NextResponse.json(
      { detail: "Unable to reach the pinned foods endpoint." },
      { status: 502 },
    );
  }
}
