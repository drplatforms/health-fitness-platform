import { NextRequest, NextResponse } from "next/server";

import { getApiBaseUrl } from "@/lib/dailyDriverApi";

interface RouteContext {
  params: Promise<{ personalFoodId: string }>;
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

export async function GET(request: NextRequest, context: RouteContext) {
  const { personalFoodId } = await context.params;
  const userId = request.nextUrl.searchParams.get("user_id");
  if (!userId) {
    return NextResponse.json({ detail: "user_id is required." }, { status: 400 });
  }
  return forward(
    `${getApiBaseUrl()}/nutrition/${userId}/personal-foods/${personalFoodId}`,
    "GET",
  );
}

export async function PATCH(request: NextRequest, context: RouteContext) {
  const { personalFoodId } = await context.params;
  const payload = (await request.json().catch(() => null)) as
    | Record<string, unknown>
    | null;
  const userId = payload?.user_id;
  if (typeof userId !== "number" || userId <= 0) {
    return NextResponse.json({ detail: "user_id is required." }, { status: 400 });
  }
  const backendPayload = { ...payload };
  delete backendPayload.user_id;
  return forward(
    `${getApiBaseUrl()}/nutrition/${userId}/personal-foods/${personalFoodId}`,
    "PATCH",
    backendPayload,
  );
}

export async function DELETE(request: NextRequest, context: RouteContext) {
  const { personalFoodId } = await context.params;
  const userId = request.nextUrl.searchParams.get("user_id");
  if (!userId) {
    return NextResponse.json({ detail: "user_id is required." }, { status: 400 });
  }
  return forward(
    `${getApiBaseUrl()}/nutrition/${userId}/personal-foods/${personalFoodId}`,
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
    const payload = await backendJson(response);
    if (!response.ok) {
      return NextResponse.json(
        backendError(payload, "The backend could not complete this request."),
        { status: response.status },
      );
    }
    return NextResponse.json(payload);
  } catch {
    return NextResponse.json(
      { detail: "Unable to reach the personal food endpoint." },
      { status: 502 },
    );
  }
}
