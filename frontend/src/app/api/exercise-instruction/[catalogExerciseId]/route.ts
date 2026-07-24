import { NextResponse } from "next/server";

import { getApiBaseUrl } from "@/lib/dailyDriverApi";
import {
  buildBackendUrl,
  parsePositiveIntegerId,
} from "@/lib/securityBoundary";

interface RouteContext {
  params: Promise<{
    catalogExerciseId: string;
  }>;
}

const MAX_BACKEND_DETAIL_LENGTH = 240;

function boundedBackendDetail(
  payload: Record<string, unknown> | null,
  fallback: string,
): string {
  const detail = payload?.detail;
  if (typeof detail !== "string") {
    return fallback;
  }

  const normalizedDetail = detail.trim();
  return normalizedDetail
    ? normalizedDetail.slice(0, MAX_BACKEND_DETAIL_LENGTH)
    : fallback;
}

export async function GET(_request: Request, context: RouteContext) {
  const { catalogExerciseId } = await context.params;
  const parsedCatalogExerciseId = parsePositiveIntegerId(catalogExerciseId);
  if (parsedCatalogExerciseId === null) {
    return NextResponse.json(
      { detail: "catalogExerciseId must be a positive integer." },
      { status: 400 },
    );
  }

  const endpoint = buildBackendUrl(getApiBaseUrl(), "exercise-catalog", [
    parsedCatalogExerciseId,
    "instruction",
  ]);

  try {
    const response = await fetch(endpoint, {
      cache: "no-store",
      headers: {
        Accept: "application/json",
      },
    });
    const responsePayload = (await response.json().catch(() => null)) as
      | Record<string, unknown>
      | null;

    if (!response.ok) {
      return NextResponse.json(
        {
          detail: boundedBackendDetail(
            responsePayload,
            "The backend could not return exercise instructions.",
          ),
        },
        { status: response.status },
      );
    }

    return NextResponse.json(responsePayload);
  } catch {
    return NextResponse.json(
      { detail: "Unable to reach the backend exercise instruction endpoint." },
      { status: 502 },
    );
  }
}
