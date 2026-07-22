import { NextRequest, NextResponse } from "next/server";

import { getApiBaseUrl } from "@/lib/dailyDriverApi";

export async function POST(request: NextRequest) {
  const body = await request.json().catch(() => null);
  if (!body || typeof body !== "object") {
    return NextResponse.json(
      { detail: "A JSON request is required." },
      { status: 400 },
    );
  }

  try {
    const response = await fetch(`${getApiBaseUrl()}/coach/ask`, {
      method: "POST",
      cache: "no-store",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(body),
    });
    const payload = await response.json().catch(() => null);
    return NextResponse.json(
      payload ?? { detail: "The backend returned an empty Coach response." },
      { status: response.status },
    );
  } catch {
    return NextResponse.json(
      { detail: "Unable to reach the Coach endpoint." },
      { status: 502 },
    );
  }
}
