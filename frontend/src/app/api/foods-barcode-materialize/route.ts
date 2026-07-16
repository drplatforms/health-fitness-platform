import { NextRequest, NextResponse } from "next/server";

import { getApiBaseUrl } from "@/lib/dailyDriverApi";

export async function POST(request: NextRequest) {
  const body = await request.json().catch(() => null);
  if (
    !body ||
    !Number.isInteger(body.raw_food_source_record_id) ||
    typeof body.normalized_gtin !== "string"
  ) {
    return NextResponse.json(
      { detail: "raw_food_source_record_id and normalized_gtin are required." },
      { status: 400 },
    );
  }

  try {
    const response = await fetch(`${getApiBaseUrl()}/foods/barcode/materialize`, {
      method: "POST",
      cache: "no-store",
      headers: { Accept: "application/json", "Content-Type": "application/json" },
      body: JSON.stringify({
        raw_food_source_record_id: body.raw_food_source_record_id,
        normalized_gtin: body.normalized_gtin,
      }),
    });
    const payload = await response.json().catch(() => null);
    if (!response.ok) {
      return NextResponse.json(
        { detail: payload?.detail || "The backend could not save this product." },
        { status: response.status },
      );
    }
    return NextResponse.json(payload);
  } catch {
    return NextResponse.json(
      { detail: "Unable to reach the backend barcode endpoint." },
      { status: 502 },
    );
  }
}
