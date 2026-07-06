import { NextRequest, NextResponse } from "next/server";

import { getApiBaseUrl } from "@/lib/dailyDriverApi";

interface CanonicalNutritionLogRequestPayload {
  user_id?: number;
  canonical_food_id?: number;
  grams?: number;
  entry_date?: string;
  meal_type?: string;
}

export async function POST(request: NextRequest) {
  const payload = (await request.json().catch(() => null)) as
    | CanonicalNutritionLogRequestPayload
    | null;

  if (
    !payload?.user_id ||
    !payload.canonical_food_id ||
    payload.grams === undefined
  ) {
    return NextResponse.json(
      {
        detail: "user_id, canonical_food_id, and grams are required.",
      },
      { status: 400 },
    );
  }

  const endpoint = `${getApiBaseUrl()}/nutrition/${payload.user_id}/log-canonical`;
  const backendPayload = {
    canonical_food_id: payload.canonical_food_id,
    grams: payload.grams,
    entry_date: payload.entry_date,
    meal_type: payload.meal_type,
  };

  try {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
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
              : "The backend could not log this food.",
        },
        { status: response.status },
      );
    }

    return NextResponse.json(responsePayload);
  } catch {
    return NextResponse.json(
      { detail: "Unable to reach the backend food logging endpoint." },
      { status: 502 },
    );
  }
}
