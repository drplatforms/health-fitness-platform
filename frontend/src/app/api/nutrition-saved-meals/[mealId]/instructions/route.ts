import { NextRequest, NextResponse } from "next/server";

import { getApiBaseUrl } from "@/lib/dailyDriverApi";

interface RouteContext {
  params: Promise<{ mealId: string }>;
}

export async function POST(request: NextRequest, context: RouteContext) {
  const { mealId } = await context.params;
  const payload = (await request.json().catch(() => null)) as
    | { user_id?: number; provider?: string; model?: string }
    | null;
  if (!payload?.user_id || !payload.provider) {
    return NextResponse.json(
      { detail: "user_id and provider are required." },
      { status: 400 },
    );
  }
  try {
    const response = await fetch(
      `${getApiBaseUrl()}/nutrition/${payload.user_id}/saved-meals/${mealId}/instructions`,
      {
        method: "POST",
        cache: "no-store",
        headers: { Accept: "application/json", "Content-Type": "application/json" },
        body: JSON.stringify({ provider: payload.provider, model: payload.model }),
      },
    );
    const responsePayload = await response.json().catch(() => null);
    return NextResponse.json(
      responsePayload ?? { detail: "The backend returned no cooking instructions." },
      { status: response.status },
    );
  } catch {
    return NextResponse.json(
      { detail: "Unable to reach the saved recipe instructions endpoint." },
      { status: 502 },
    );
  }
}
