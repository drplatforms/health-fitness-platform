import { NextRequest, NextResponse } from "next/server";

import { getApiBaseUrl } from "@/lib/dailyDriverApi";

async function backendJson(response: Response) {
  return (await response.json().catch(() => null)) as
    | Record<string, unknown>
    | null;
}

function errorPayload(payload: Record<string, unknown> | null, fallback: string) {
  return { detail: typeof payload?.detail === "string" ? payload.detail : fallback };
}

export async function GET(request: NextRequest) {
  const params = request.nextUrl.searchParams;
  const userId = params.get("user_id");
  if (!userId) {
    return NextResponse.json({ detail: "user_id is required." }, { status: 400 });
  }
  const backendParams = new URLSearchParams();
  if (params.has("include_archived")) {
    backendParams.set("include_archived", params.get("include_archived") ?? "false");
  }
  return forward(
    `${getApiBaseUrl()}/nutrition/${userId}/saved-meals?${backendParams.toString()}`,
    "GET",
  );
}

export async function POST(request: NextRequest) {
  const payload = (await request.json().catch(() => null)) as
    | Record<string, unknown>
    | null;
  const userId = payload?.user_id;
  if (typeof userId !== "number" || userId <= 0) {
    return NextResponse.json({ detail: "user_id is required." }, { status: 400 });
  }
  const body = { ...payload };
  delete body.user_id;
  return forward(
    `${getApiBaseUrl()}/nutrition/${userId}/saved-meals`,
    "POST",
    body,
  );
}

async function forward(
  endpoint: string,
  method: "GET" | "POST",
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
        errorPayload(payload, "The backend could not complete this meal request."),
        { status: response.status },
      );
    }
    return NextResponse.json(payload);
  } catch {
    return NextResponse.json(
      { detail: "Unable to reach the saved meals endpoint." },
      { status: 502 },
    );
  }
}
