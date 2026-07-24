import { NextRequest, NextResponse } from "next/server";

import { getApiBaseUrl } from "@/lib/dailyDriverApi";
import {
  buildBackendUrl,
  parsePositiveIntegerId,
} from "@/lib/securityBoundary";

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
  const parsedEntryId = parsePositiveIntegerId(entryId);
  if (parsedEntryId === null) {
    return NextResponse.json(
      { detail: "entry_id must be a positive integer." },
      { status: 400 },
    );
  }
  const payload = (await request.json().catch(() => null)) as
    | {
        user_id?: number;
        grams?: number;
        serving_quantity?: number;
        meal_type?: string;
        entry_date?: string;
      }
    | null;
  const userId = parsePositiveIntegerId(payload?.user_id);
  if (!payload || userId === null) {
    return NextResponse.json(
      { detail: "user_id must be a positive integer." },
      { status: 400 },
    );
  }
  const endpoint = buildBackendUrl(getApiBaseUrl(), "nutrition", [
    userId,
    "personal-logs",
    parsedEntryId,
  ]);
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
  const parsedEntryId = parsePositiveIntegerId(entryId);
  const userId = parsePositiveIntegerId(
    request.nextUrl.searchParams.get("user_id"),
  );
  const date = request.nextUrl.searchParams.get("date");
  if (parsedEntryId === null || userId === null || !date) {
    return NextResponse.json(
      { detail: "user_id, entry_id, and date are required." },
      { status: 400 },
    );
  }
  const params = new URLSearchParams({ date });
  const endpoint = buildBackendUrl(
    getApiBaseUrl(),
    "nutrition",
    [userId, "personal-logs", parsedEntryId],
    params,
  );
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
