import { NextRequest, NextResponse } from "next/server";

import { getApiBaseUrl } from "@/lib/dailyDriverApi";

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
  try {
    const response = await fetch(
      `${getApiBaseUrl()}/nutrition/${userId}/meal-instructions`,
      {
        method: "POST",
        cache: "no-store",
        headers: { Accept: "application/json", "Content-Type": "application/json" },
        body: JSON.stringify(body),
      },
    );
    const responsePayload = await response.json().catch(() => null);
    return NextResponse.json(
      responsePayload ?? { detail: "The backend returned no cooking instructions." },
      { status: response.status },
    );
  } catch {
    return NextResponse.json(
      { detail: "Unable to reach the cooking instructions endpoint." },
      { status: 502 },
    );
  }
}
