import { NextRequest, NextResponse } from "next/server";

import { getApiBaseUrl } from "@/lib/dailyDriverApi";

interface RouteContext {
  params: Promise<{ personalFoodId: string }>;
}

export async function POST(request: NextRequest, context: RouteContext) {
  const { personalFoodId } = await context.params;
  const payload = (await request.json().catch(() => null)) as
    | { user_id?: number }
    | null;
  if (!payload?.user_id) {
    return NextResponse.json({ detail: "user_id is required." }, { status: 400 });
  }
  const endpoint = `${getApiBaseUrl()}/nutrition/${payload.user_id}/personal-foods/${personalFoodId}/restore`;
  try {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: { Accept: "application/json" },
    });
    const responsePayload = (await response.json().catch(() => null)) as
      | Record<string, unknown>
      | null;
    if (!response.ok) {
      return NextResponse.json(
        {
          detail:
            typeof responsePayload?.detail === "string"
              ? responsePayload.detail
              : "The backend could not restore this food.",
        },
        { status: response.status },
      );
    }
    return NextResponse.json(responsePayload);
  } catch {
    return NextResponse.json(
      { detail: "Unable to reach the personal food restore endpoint." },
      { status: 502 },
    );
  }
}
