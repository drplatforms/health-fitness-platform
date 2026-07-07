import { getApiBaseUrl } from "@/lib/dailyDriverApi";
import { CanonicalFoodLogsResponse } from "@/types/canonicalFood";

export interface CanonicalFoodLogsApiResult {
  data: CanonicalFoodLogsResponse | null;
  error: string | null;
}

export async function fetchCanonicalFoodLogsFromBackend({
  userId,
  date,
}: {
  userId: number;
  date: string;
}): Promise<CanonicalFoodLogsApiResult> {
  const params = new URLSearchParams({ date });
  const endpoint = `${getApiBaseUrl()}/nutrition/${userId}/canonical-logs?${params.toString()}`;

  try {
    const response = await fetch(endpoint, {
      cache: "no-store",
      headers: {
        Accept: "application/json",
      },
    });

    if (!response.ok) {
      return {
        data: null,
        error: "Logged foods are unavailable right now.",
      };
    }

    return {
      data: (await response.json()) as CanonicalFoodLogsResponse,
      error: null,
    };
  } catch {
    return {
      data: null,
      error: "Logged foods are unavailable right now.",
    };
  }
}
