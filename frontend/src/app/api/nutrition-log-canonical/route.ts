import { NextRequest, NextResponse } from "next/server";

import { getApiBaseUrl } from "@/lib/dailyDriverApi";

interface CanonicalNutritionLogRequestPayload {
  user_id?: number;
  canonical_food_id?: number;
  grams?: number;
  serving_unit_id?: number;
  quantity?: number;
  entry_date?: string;
  meal_type?: string;
}

export async function POST(request: NextRequest) {
  const payload = (await request.json().catch(() => null)) as
    | CanonicalNutritionLogRequestPayload
    | null;

  if (!payload?.user_id || !payload.canonical_food_id) {
    return NextResponse.json(
      {
        detail: "user_id and canonical_food_id are required.",
      },
      { status: 400 },
    );
  }

  const hasGrams = payload.grams !== undefined;
  const hasServingUnit =
    payload.serving_unit_id !== undefined || payload.quantity !== undefined;

  if (hasGrams && hasServingUnit) {
    return NextResponse.json(
      {
        detail: "Provide either grams or serving_unit_id with quantity, not both.",
      },
      { status: 400 },
    );
  }

  if (!hasGrams && !hasServingUnit) {
    return NextResponse.json(
      {
        detail: "Either grams or serving_unit_id with quantity is required.",
      },
      { status: 400 },
    );
  }

  if (
    hasServingUnit &&
    (payload.serving_unit_id === undefined || payload.quantity === undefined)
  ) {
    return NextResponse.json(
      {
        detail: "serving_unit_id and quantity are required for serving-unit logging.",
      },
      { status: 400 },
    );
  }

  const endpoint = `${getApiBaseUrl()}/nutrition/${payload.user_id}/log-canonical`;
  const backendPayload = {
    canonical_food_id: payload.canonical_food_id,
    entry_date: payload.entry_date,
    meal_type: payload.meal_type,
    ...(hasGrams
      ? { grams: payload.grams }
      : {
          serving_unit_id: payload.serving_unit_id,
          quantity: payload.quantity,
        }),
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
