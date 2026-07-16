import { NextRequest, NextResponse } from "next/server";

import { getApiBaseUrl } from "@/lib/dailyDriverApi";

export async function POST(request: NextRequest) {
  const body = await request.json().catch(() => null);
  if (!body || typeof body.barcode !== "string") {
    return NextResponse.json({ detail: "barcode is required." }, { status: 400 });
  }

  try {
    const response = await fetch(`${getApiBaseUrl()}/foods/barcode/resolve`, {
      method: "POST",
      cache: "no-store",
      headers: { Accept: "application/json", "Content-Type": "application/json" },
      body: JSON.stringify({
        barcode: body.barcode,
        barcode_format:
          typeof body.barcode_format === "string" ? body.barcode_format : null,
      }),
    });
    const payload = await response.json().catch(() => null);
    if (!response.ok) {
      return NextResponse.json(
        { detail: payload?.detail || "The backend could not resolve this barcode." },
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
