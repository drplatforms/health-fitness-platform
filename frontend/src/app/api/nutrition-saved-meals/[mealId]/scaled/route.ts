import { NextRequest, NextResponse } from "next/server";

import { getApiBaseUrl } from "@/lib/dailyDriverApi";

interface RouteContext {
  params: Promise<{ mealId: string }>;
}

export async function GET(request: NextRequest, context: RouteContext) {
  const { mealId } = await context.params;
  const userId = request.nextUrl.searchParams.get("user_id");
  const multiplier = request.nextUrl.searchParams.get("multiplier") ?? "1";
  if (!userId) {
    return NextResponse.json({ detail: "user_id is required." }, { status: 400 });
  }
  try {
    const response = await fetch(
      `${getApiBaseUrl()}/nutrition/${userId}/saved-meals/${mealId}/scaled?multiplier=${encodeURIComponent(multiplier)}`,
      { cache: "no-store", headers: { Accept: "application/json" } },
    );
    const payload = await response.json().catch(() => null);
    return NextResponse.json(
      payload ?? { detail: "The backend returned no scaled recipe." },
      { status: response.status },
    );
  } catch {
    return NextResponse.json(
      { detail: "Unable to reach the recipe scaling endpoint." },
      { status: 502 },
    );
  }
}
