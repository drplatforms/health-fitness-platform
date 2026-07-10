import { NextRequest, NextResponse } from "next/server";

import { getApiBaseUrl } from "@/lib/dailyDriverApi";

interface RouteContext {
  params: Promise<{
    entryId: string;
  }>;
}

interface CanonicalNutritionLogUpdatePayload {
  user_id?: number;
  grams?: number;
  serving_unit_id?: number;
  quantity?: number;
  meal_type?: string;
  entry_date?: string;
}

async function readBackendJson(response: Response) {
  return (await response.json().catch(() => null)) as
    | Record<string, unknown>
    | null;
}

function backendErrorPayload(
  responsePayload: Record<string, unknown> | null,
  fallbackMessage: string,
) {
  return {
    detail:
      typeof responsePayload?.detail === "string"
        ? responsePayload.detail
        : fallbackMessage,
  };
}

export async function PATCH(request: NextRequest, context: RouteContext) {
  const { entryId } = await context.params;
  const payload = (await request.json().catch(() => null)) as
    | CanonicalNutritionLogUpdatePayload
    | null;

  if (!payload?.user_id) {
    return NextResponse.json(
      { detail: "user_id is required." },
      { status: 400 },
    );
  }

  const endpoint = `${getApiBaseUrl()}/nutrition/${payload.user_id}/canonical-logs/${entryId}`;
  const backendPayload = {
    grams: payload.grams,
    serving_unit_id: payload.serving_unit_id,
    quantity: payload.quantity,
    meal_type: payload.meal_type,
    entry_date: payload.entry_date,
  };

  try {
    const response = await fetch(endpoint, {
      method: "PATCH",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify(backendPayload),
    });
    const responsePayload = await readBackendJson(response);

    if (!response.ok) {
      return NextResponse.json(
        backendErrorPayload(responsePayload, "The backend could not update this food."),
        { status: response.status },
      );
    }

    return NextResponse.json(responsePayload);
  } catch {
    return NextResponse.json(
      { detail: "Unable to reach the backend logged-food update endpoint." },
      { status: 502 },
    );
  }
}

export async function DELETE(request: NextRequest, context: RouteContext) {
  const { entryId } = await context.params;
  const searchParams = request.nextUrl.searchParams;
  const userId = searchParams.get("user_id");
  const date = searchParams.get("date");

  if (!userId || !date) {
    return NextResponse.json(
      { detail: "user_id and date are required." },
      { status: 400 },
    );
  }

  const params = new URLSearchParams({ date });
  const endpoint = `${getApiBaseUrl()}/nutrition/${userId}/canonical-logs/${entryId}?${params.toString()}`;

  try {
    const response = await fetch(endpoint, {
      method: "DELETE",
      headers: {
        Accept: "application/json",
      },
    });
    const responsePayload = await readBackendJson(response);

    if (!response.ok) {
      return NextResponse.json(
        backendErrorPayload(responsePayload, "The backend could not delete this food."),
        { status: response.status },
      );
    }

    return NextResponse.json(responsePayload);
  } catch {
    return NextResponse.json(
      { detail: "Unable to reach the backend logged-food delete endpoint." },
      { status: 502 },
    );
  }
}
