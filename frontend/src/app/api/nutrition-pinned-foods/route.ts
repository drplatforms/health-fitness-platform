import { NextRequest, NextResponse } from "next/server";

import { getApiBaseUrl } from "@/lib/dailyDriverApi";

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
    userId: params.get("user_id"),
    foodType: params.get("food_type"),
    foodId: params.get("food_id"),
  };
}

export async function GET(request: NextRequest) {
  const { userId } = requestIdentity(request);
  if (!userId) {
    return NextResponse.json({ detail: "user_id is required." }, { status: 400 });
  }
  return proxyPinnedFoods(`${getApiBaseUrl()}/nutrition/${userId}/pinned-foods`);
}

export async function PUT(request: NextRequest) {
  return mutatePinnedFood(request, "PUT");
}

export async function DELETE(request: NextRequest) {
  return mutatePinnedFood(request, "DELETE");
}

async function mutatePinnedFood(request: NextRequest, method: "PUT" | "DELETE") {
  const { userId, foodType, foodId } = requestIdentity(request);
  if (!userId || !foodType || !foodId) {
    return NextResponse.json(
      { detail: "user_id, food_type, and food_id are required." },
      { status: 400 },
    );
  }
  return proxyPinnedFoods(
    `${getApiBaseUrl()}/nutrition/${userId}/pinned-foods/${foodType}/${foodId}`,
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
