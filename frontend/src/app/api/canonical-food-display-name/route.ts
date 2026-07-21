import { NextRequest, NextResponse } from "next/server";

import { getApiBaseUrl } from "@/lib/dailyDriverApi";

interface DisplayNamePayload {
  user_id?: number;
  canonical_food_id?: number;
  display_name?: string;
}

async function mutate(request: NextRequest, method: "PUT" | "DELETE") {
  const payload = (await request.json().catch(() => null)) as DisplayNamePayload | null;
  if (!payload?.user_id || !payload.canonical_food_id) {
    return NextResponse.json(
      { detail: "user_id and canonical_food_id are required." },
      { status: 400 },
    );
  }
  if (method === "PUT" && typeof payload.display_name !== "string") {
    return NextResponse.json({ detail: "display_name is required." }, { status: 400 });
  }

  const endpoint = `${getApiBaseUrl()}/nutrition/${payload.user_id}/canonical-food-names/${payload.canonical_food_id}`;
  try {
    const response = await fetch(endpoint, {
      method,
      headers: { Accept: "application/json", "Content-Type": "application/json" },
      ...(method === "PUT"
        ? { body: JSON.stringify({ display_name: payload.display_name }) }
        : {}),
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
              : "The backend could not update this food name.",
        },
        { status: response.status },
      );
    }
    return NextResponse.json(responsePayload);
  } catch {
    return NextResponse.json(
      { detail: "Unable to reach the food name endpoint." },
      { status: 502 },
    );
  }
}

export async function PUT(request: NextRequest) {
  return mutate(request, "PUT");
}

export async function DELETE(request: NextRequest) {
  return mutate(request, "DELETE");
}
