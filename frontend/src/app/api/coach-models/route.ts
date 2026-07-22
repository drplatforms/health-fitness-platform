import { NextResponse } from "next/server";

import { getApiBaseUrl } from "@/lib/dailyDriverApi";

export async function GET() {
  try {
    const response = await fetch(`${getApiBaseUrl()}/coach/models`, {
      cache: "no-store",
      headers: { Accept: "application/json" },
    });
    const payload = await response.json().catch(() => null);
    return NextResponse.json(
      payload ?? { detail: "The backend returned no Coach model options." },
      { status: response.status },
    );
  } catch {
    return NextResponse.json(
      { detail: "Unable to load Coach models." },
      { status: 502 },
    );
  }
}
