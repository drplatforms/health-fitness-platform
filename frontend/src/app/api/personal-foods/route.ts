import { NextRequest, NextResponse } from "next/server";

import { getApiBaseUrl } from "@/lib/dailyDriverApi";

interface PersonalFoodPayload {
  user_id?: number;
  display_name?: string;
  brand_name?: string;
  input_basis?: string;
  serving_name?: string;
  serving_grams?: number;
  calories?: number;
  protein_g?: number;
  carbs_g?: number;
  fat_g?: number;
}

async function backendJson(response: Response) {
  return (await response.json().catch(() => null)) as
    | Record<string, unknown>
    | null;
}

function backendError(payload: Record<string, unknown> | null, fallback: string) {
  return {
    detail: typeof payload?.detail === "string" ? payload.detail : fallback,
  };
}

export async function GET(request: NextRequest) {
  const params = request.nextUrl.searchParams;
  const userId = params.get("user_id");
  const query = params.get("q")?.trim();
  if (!userId) {
    return NextResponse.json({ detail: "user_id is required." }, { status: 400 });
  }

  const backendParams = new URLSearchParams();
  if (params.has("include_archived")) {
    backendParams.set("include_archived", params.get("include_archived") ?? "false");
  }
  if (params.has("limit")) {
    backendParams.set("limit", params.get("limit") ?? "50");
  }
  if (query) {
    backendParams.set("q", query);
  }
  const operation = query ? "search" : "";
  const endpoint = `${getApiBaseUrl()}/nutrition/${userId}/personal-foods${operation ? `/${operation}` : ""}?${backendParams.toString()}`;

  try {
    const response = await fetch(endpoint, {
      cache: "no-store",
      headers: { Accept: "application/json" },
    });
    const payload = await backendJson(response);
    if (!response.ok) {
      return NextResponse.json(
        backendError(payload, "The backend could not return personal foods."),
        { status: response.status },
      );
    }
    return NextResponse.json(payload);
  } catch {
    return NextResponse.json(
      { detail: "Unable to reach the personal foods endpoint." },
      { status: 502 },
    );
  }
}

export async function POST(request: NextRequest) {
  const payload = (await request.json().catch(() => null)) as
    | PersonalFoodPayload
    | null;
  if (!payload?.user_id || !payload.display_name || !payload.input_basis) {
    return NextResponse.json(
      { detail: "user_id, display_name, and input_basis are required." },
      { status: 400 },
    );
  }

  const { user_id: userId, ...backendPayload } = payload;
  const endpoint = `${getApiBaseUrl()}/nutrition/${userId}/personal-foods`;
  try {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: { Accept: "application/json", "Content-Type": "application/json" },
      body: JSON.stringify(backendPayload),
    });
    const responsePayload = await backendJson(response);
    if (!response.ok) {
      return NextResponse.json(
        backendError(responsePayload, "The backend could not save this food."),
        { status: response.status },
      );
    }
    return NextResponse.json(responsePayload);
  } catch {
    return NextResponse.json(
      { detail: "Unable to reach the personal food save endpoint." },
      { status: 502 },
    );
  }
}
