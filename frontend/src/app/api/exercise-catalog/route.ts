import { NextResponse } from "next/server";

import { getApiBaseUrl } from "@/lib/dailyDriverApi";

export async function GET() {
  try {
    const response = await fetch(`${getApiBaseUrl()}/exercise-catalog`, {
      cache: "no-store",
      headers: { Accept: "application/json" },
    });
    const payload = (await response.json().catch(() => null)) as
      | Record<string, unknown>
      | null;
    if (!response.ok) {
      return NextResponse.json(
        { detail: "The backend could not return the exercise catalog." },
        { status: response.status },
      );
    }
    return NextResponse.json(payload);
  } catch {
    return NextResponse.json(
      { detail: "Unable to reach the backend exercise catalog." },
      { status: 502 },
    );
  }
}
