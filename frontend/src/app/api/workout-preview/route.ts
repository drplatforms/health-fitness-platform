import { NextRequest, NextResponse } from "next/server";

import { getApiBaseUrl } from "@/lib/dailyDriverApi";

export async function GET(request: NextRequest) {
  const userId = request.nextUrl.searchParams.get("user_id");
  const workoutSizePreference =
    request.nextUrl.searchParams.get("workout_size_preference");
  const previewVariationIndex =
    request.nextUrl.searchParams.get("preview_variation_index") ?? "0";
  const targetDate = request.nextUrl.searchParams.get("target_date");
  const trainAnyway = request.nextUrl.searchParams.get("train_anyway");

  if (!userId) {
    return NextResponse.json(
      { detail: "user_id is required." },
      { status: 400 },
    );
  }

  const params = new URLSearchParams({
    preview_variation_index: previewVariationIndex,
  });
  if (workoutSizePreference) {
    params.set("workout_size_preference", workoutSizePreference);
  }
  if (targetDate) {
    params.set("target_date", targetDate);
  }
  if (trainAnyway === "true") {
    params.set("train_anyway", "true");
  }
  const endpoint = `${getApiBaseUrl()}/workout-plans/preview/${userId}?${params.toString()}`;

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
              : "The backend could not return a workout preview.",
        },
        { status: response.status },
      );
    }

    return NextResponse.json(payload);
  } catch {
    return NextResponse.json(
      { detail: "Unable to reach the backend workout preview endpoint." },
      { status: 502 },
    );
  }
}
