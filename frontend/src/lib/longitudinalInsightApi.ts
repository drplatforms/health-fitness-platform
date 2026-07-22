import { getApiBaseUrl } from "@/lib/dailyDriverApi";
import type { DailyDriverApiError } from "@/lib/dailyDriverApi";
import type { LongitudinalInsightResponse } from "@/types/longitudinalInsight";

export interface LongitudinalInsightApiResult {
  data: LongitudinalInsightResponse | null;
  error: DailyDriverApiError | null;
}

export async function fetchLongitudinalInsightsFromBackend(
  userId: number,
  targetDate: string,
): Promise<LongitudinalInsightApiResult> {
  const params = new URLSearchParams({ as_of_date: targetDate });
  const endpoint = `${getApiBaseUrl()}/insights/longitudinal/${userId}?${params.toString()}`;

  try {
    const response = await fetch(endpoint, {
      cache: "no-store",
      headers: { Accept: "application/json" },
    });
    if (!response.ok) {
      return {
        data: null,
        error: {
          heading: "Insights are unavailable",
          message: "The backend could not evaluate historical patterns right now.",
          statusCode: response.status,
        },
      };
    }
    return {
      data: (await response.json()) as LongitudinalInsightResponse,
      error: null,
    };
  } catch {
    return {
      data: null,
      error: {
        heading: "Insights are unavailable",
        message: "Historical patterns will appear when the backend is available.",
      },
    };
  }
}
