import { NextRequest, NextResponse } from "next/server";

import { getApiBaseUrl } from "@/lib/dailyDriverApi";
import {
  type SafeCoachFailure,
  buildBackendUrl,
  sanitizeCoachFailure,
} from "@/lib/securityBoundary";

export async function POST(request: NextRequest) {
  const body = await request.json().catch(() => null);
  if (!body || typeof body !== "object") {
    return NextResponse.json(
      safeCoachError(
        "invalid_request",
        "A valid Coach request is required.",
        false,
      ),
      { status: 400 },
    );
  }

  try {
    const response = await fetch(
      buildBackendUrl(getApiBaseUrl(), "coach", ["ask"]),
      {
        method: "POST",
        cache: "no-store",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify(body),
      },
    );
    const payload = await response.json().catch(() => null);
    if (!response.ok) {
      const safeBackendFailure = sanitizeCoachFailure(payload);
      return NextResponse.json(
        safeBackendFailure
          ? safeBackendFailure
          : safeCoachError(
              "coach_backend_failed",
              "Coach could not complete this request safely.",
              response.status >= 500,
            ),
        { status: response.status },
      );
    }
    return NextResponse.json(
      payload ??
        safeCoachError(
          "coach_backend_failed",
          "Coach returned an empty response.",
          true,
        ),
      { status: payload ? response.status : 502 },
    );
  } catch {
    return NextResponse.json(
      safeCoachError(
        "coach_unavailable",
        "Coach is unavailable right now.",
        true,
      ),
      { status: 502 },
    );
  }
}

function safeCoachError(
  code: string,
  message: string,
  retryable: boolean,
): SafeCoachFailure {
  return {
    success: false,
    error: {
      code,
      message,
      correlation_id: crypto.randomUUID(),
      retryable,
    },
  };
}
