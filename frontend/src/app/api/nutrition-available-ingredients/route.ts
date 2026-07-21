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
  return proxyAvailableIngredients(
    `${getApiBaseUrl()}/nutrition/${userId}/available-ingredients`,
  );
}

export async function PUT(request: NextRequest) {
  return mutateAvailableIngredient(request, "PUT");
}

export async function DELETE(request: NextRequest) {
  return mutateAvailableIngredient(request, "DELETE");
}

async function mutateAvailableIngredient(
  request: NextRequest,
  method: "PUT" | "DELETE",
) {
  const { userId, canonicalFoodId } = requestIdentity(request);
  if (!userId || !canonicalFoodId) {
    return NextResponse.json(
      { detail: "user_id and canonical_food_id are required." },
      { status: 400 },
    );
  }
  return proxyAvailableIngredients(
    `${getApiBaseUrl()}/nutrition/${userId}/available-ingredients/canonical/${canonicalFoodId}`,
    method,
  );
}

async function proxyAvailableIngredients(
  endpoint: string,
  method: "GET" | "PUT" | "DELETE" = "GET",
) {
  try {
    const response = await fetch(endpoint, {
      method,
      cache: "no-store",
      headers: { Accept: "application/json" },
    });
    const payload = await backendJson(response);
    if (!response.ok) {
      return NextResponse.json(
        {
          detail:
            typeof payload?.detail === "string"
              ? payload.detail
              : "The backend could not update available ingredients.",
        },
        { status: response.status },
      );
    }
    return NextResponse.json(payload);
  } catch {
    return NextResponse.json(
      { detail: "Unable to reach the available ingredients endpoint." },
      { status: 502 },
    );
  }
}
