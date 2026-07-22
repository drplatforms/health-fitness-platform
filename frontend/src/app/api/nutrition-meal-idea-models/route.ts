import { NextResponse } from "next/server";

import { getApiBaseUrl } from "@/lib/dailyDriverApi";

export async function GET() {
  try {
    const response = await fetch(
      `${getApiBaseUrl()}/nutrition/meal-ideas/model-options`,
      {
        cache: "no-store",
        headers: { Accept: "application/json" },
      },
    );
    const payload = await response.json().catch(() => null);
    return NextResponse.json(
      payload ?? { detail: "The backend returned no model options." },
      { status: response.status },
    );
  } catch {
    return NextResponse.json(
      { detail: "Unable to load meal idea models." },
      { status: 502 },
    );
  }
}
