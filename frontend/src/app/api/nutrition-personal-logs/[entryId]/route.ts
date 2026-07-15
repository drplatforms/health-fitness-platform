import { NextRequest, NextResponse } from "next/server";

import { getApiBaseUrl } from "@/lib/dailyDriverApi";

interface RouteContext {
  params: Promise<{ entryId: string }>;
}

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

export async function PATCH(request: NextRequest, context: RouteContext) {
  const { entryId } = await context.params;
  const payload = (await request.json().catch(() => null)) as
    | {
        user_id?: number;
        grams?: number;
        serving_quantity?: number;
        meal_type?: string;
        entry_date?: string;
      }
    | null;
  if (!payload?.user_id) {
    return NextResponse.json({ detail: "user_id is required." }, { status: 400 });
  }
  const endpoint = `${getApiBaseUrl()}/nutrition/${payload.user_id}/personal-logs/${entryId}`;
  try {
    const response = await fetch(endpoint, {
      method: "PATCH",
      headers: { Accept: "application/json", "Content-Type": "application/json" },
      body: JSON.stringify({
        grams: payload.grams,
        serving_quantity: payload.serving_quantity,
        meal_type: payload.meal_type,
        entry_date: payload.entry_date,
      }),
    });
    const responsePayload = await backendJson(response);
    if (!response.ok) {
      return NextResponse.json(
        backendError(responsePayload, "The backend could not update this log."),
        { status: response.status },
      );
    }
    return NextResponse.json(responsePayload);
  } catch {
    return NextResponse.json(
      { detail: "Unable to reach the personal food log update endpoint." },
      { status: 502 },
    );
  }
}

export async function DELETE(request: NextRequest, context: RouteContext) {
  const { entryId } = await context.params;
  const userId = request.nextUrl.searchParams.get("user_id");
  const date = request.nextUrl.searchParams.get("date");
  if (!userId || !date) {
    return NextResponse.json(
      { detail: "user_id and date are required." },
      { status: 400 },
    );
  }
  const params = new URLSearchParams({ date });
  const endpoint = `${getApiBaseUrl()}/nutrition/${userId}/personal-logs/${entryId}?${params.toString()}`;
  try {
    const response = await fetch(endpoint, {
      method: "DELETE",
      headers: { Accept: "application/json" },
    });
    const responsePayload = await backendJson(response);
    if (!response.ok) {
      return NextResponse.json(
        backendError(responsePayload, "The backend could not delete this log."),
        { status: response.status },
      );
    }
    return NextResponse.json(responsePayload);
  } catch {
    return NextResponse.json(
      { detail: "Unable to reach the personal food log delete endpoint." },
      { status: 502 },
    );
  }
}
