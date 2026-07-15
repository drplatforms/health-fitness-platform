import { NextRequest, NextResponse } from "next/server";

import { getApiBaseUrl } from "@/lib/dailyDriverApi";

interface PersonalLogPayload {
  user_id?: number;
  personal_food_id?: number;
  grams?: number;
  serving_quantity?: number;
  entry_date?: string;
  meal_type?: string;
}

export async function POST(request: NextRequest) {
  const payload = (await request.json().catch(() => null)) as
    | PersonalLogPayload
    | null;
  if (!payload?.user_id || !payload.personal_food_id) {
    return NextResponse.json(
      { detail: "user_id and personal_food_id are required." },
      { status: 400 },
    );
  }
  const hasGrams = payload.grams !== undefined;
  const hasServing = payload.serving_quantity !== undefined;
  if (hasGrams === hasServing) {
    return NextResponse.json(
      { detail: "Provide exactly one of grams or serving_quantity." },
      { status: 400 },
    );
  }

  const endpoint = `${getApiBaseUrl()}/nutrition/${payload.user_id}/log-personal`;
  const backendPayload = {
    personal_food_id: payload.personal_food_id,
    grams: payload.grams,
    serving_quantity: payload.serving_quantity,
    entry_date: payload.entry_date,
    meal_type: payload.meal_type,
  };
  try {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: { Accept: "application/json", "Content-Type": "application/json" },
      body: JSON.stringify(backendPayload),
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
              : "The backend could not log this personal food.",
        },
        { status: response.status },
      );
    }
    return NextResponse.json(responsePayload);
  } catch {
    return NextResponse.json(
      { detail: "Unable to reach the personal food logging endpoint." },
      { status: 502 },
    );
  }
}
