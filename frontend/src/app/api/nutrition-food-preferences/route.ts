import { NextRequest, NextResponse } from "next/server";

import { getApiBaseUrl } from "@/lib/dailyDriverApi";

async function backendJson(response: Response) {
  return (await response.json().catch(() => null)) as
    | Record<string, unknown>
    | null;
}

function requestIdentity(request: NextRequest) {
  const params = request.nextUrl.searchParams;
  return {
    userId: params.get("user_id"),
    canonicalFoodId: params.get("canonical_food_id"),
  };
}

export async function GET(request: NextRequest) {
  const { userId } = requestIdentity(request);
  if (!userId) {
    return NextResponse.json({ detail: "user_id is required." }, { status: 400 });
  }
  return proxyFoodPreferences(
    `${getApiBaseUrl()}/nutrition/${userId}/food-preferences`,
  );
}

export async function PUT(request: NextRequest) {
  const { userId, canonicalFoodId } = requestIdentity(request);
  if (!userId || !canonicalFoodId) {
    return NextResponse.json(
      { detail: "user_id and canonical_food_id are required." },
      { status: 400 },
    );
  }
  const payload = (await request.json().catch(() => null)) as
    | { preference?: unknown }
    | null;
  if (typeof payload?.preference !== "string") {
    return NextResponse.json(
      { detail: "preference is required." },
      { status: 400 },
    );
  }
  return proxyFoodPreferences(
    `${getApiBaseUrl()}/nutrition/${userId}/food-preferences/canonical/${canonicalFoodId}`,
    "PUT",
    { preference: payload.preference },
  );
}

export async function DELETE(request: NextRequest) {
  const { userId, canonicalFoodId } = requestIdentity(request);
  if (!userId || !canonicalFoodId) {
    return NextResponse.json(
      { detail: "user_id and canonical_food_id are required." },
      { status: 400 },
    );
  }
  return proxyFoodPreferences(
    `${getApiBaseUrl()}/nutrition/${userId}/food-preferences/canonical/${canonicalFoodId}`,
    "DELETE",
  );
}

async function proxyFoodPreferences(
  endpoint: string,
  method: "GET" | "PUT" | "DELETE" = "GET",
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
    const payload = await backendJson(response);
    if (!response.ok) {
      return NextResponse.json(
        {
          detail:
            typeof payload?.detail === "string"
              ? payload.detail
              : "The backend could not update food preferences.",
        },
        { status: response.status },
      );
    }
    return NextResponse.json(payload);
  } catch {
    return NextResponse.json(
      { detail: "Unable to reach the food preferences endpoint." },
      { status: 502 },
    );
  }
}
