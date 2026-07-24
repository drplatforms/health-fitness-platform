import { NextRequest, NextResponse } from "next/server";

import { getApiBaseUrl } from "@/lib/dailyDriverApi";
import {
  buildBackendUrl,
  parsePositiveIntegerId,
} from "@/lib/securityBoundary";

interface ServingUnitsRouteContext {
  params: Promise<{
    canonicalFoodId: string;
  }>;
}

export async function GET(
  _request: NextRequest,
  context: ServingUnitsRouteContext,
) {
  const { canonicalFoodId } = await context.params;
  const parsedCanonicalFoodId = parsePositiveIntegerId(canonicalFoodId);

  if (parsedCanonicalFoodId === null) {
    return NextResponse.json(
      { detail: "canonical_food_id must be a positive integer." },
      { status: 400 },
    );
  }

  const endpoint = buildBackendUrl(getApiBaseUrl(), "foods", [
    "canonical",
    parsedCanonicalFoodId,
    "serving-units",
  ]);

  try {
    const response = await fetch(endpoint, {
      cache: "no-store",
      headers: {
        Accept: "application/json",
      },
    });
    const payload = (await response.json().catch(() => null)) as
      | Record<string, unknown>
      | null;

    if (!response.ok) {
      return NextResponse.json(
        {
          detail:
            typeof payload?.detail === "string"
              ? payload.detail
              : "The backend could not return serving units.",
        },
        { status: response.status },
      );
    }

    return NextResponse.json(payload);
  } catch {
    return NextResponse.json(
      { detail: "Unable to reach the backend serving-unit endpoint." },
      { status: 502 },
    );
  }
}
