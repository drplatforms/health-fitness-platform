import { NextRequest, NextResponse } from "next/server";

import { getApiBaseUrl } from "@/lib/dailyDriverApi";

export async function GET(request: NextRequest) {
  const userId = request.nextUrl.searchParams.get("user_id");
  if (!userId) {
    return NextResponse.json({ detail: "user_id is required." }, { status: 400 });
  }

  try {
    const response = await fetch(
      `${getApiBaseUrl()}/nutrition/${encodeURIComponent(userId)}/meal-ideas/history`,
      { cache: "no-store", headers: { Accept: "application/json" } },
    );
    const payload = await response.json().catch(() => null);
    return NextResponse.json(
      payload ?? { detail: "The backend returned an empty generation-history response." },
      { status: response.status },
    );
  } catch {
    return NextResponse.json(
      { detail: "Unable to reach meal idea history." },
      { status: 502 },
    );
  }
}
