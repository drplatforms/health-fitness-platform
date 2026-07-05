import {
  DailyDriverApiError,
  DailyDriverRequestOptions,
  getApiBaseUrl,
  getDefaultUserId,
} from "@/lib/dailyDriverApi";
import { TodayWorkoutResponse } from "@/types/todayWorkout";

export interface TodayWorkoutApiResult {
  data: TodayWorkoutResponse | null;
  error: DailyDriverApiError | null;
}

export function buildTodayWorkoutHref(
  options: DailyDriverRequestOptions = {},
): string {
  const userId = options.userId ?? getDefaultUserId();
  const params = new URLSearchParams({ user_id: String(userId) });

  if (options.date) {
    params.set("date", options.date);
  }

  return `/today/workout?${params.toString()}`;
}

export async function fetchTodayWorkout(
  options: DailyDriverRequestOptions = {},
): Promise<TodayWorkoutApiResult> {
  const userId = options.userId ?? getDefaultUserId();
  const params = new URLSearchParams({ user_id: String(userId) });

  if (options.date) {
    params.set("date", options.date);
  }

  const endpoint = `${getApiBaseUrl()}/api/today/workout?${params.toString()}`;

  try {
    const response = await fetch(endpoint, {
      cache: "no-store",
      headers: {
        Accept: "application/json",
      },
    });

    if (!response.ok) {
      const message =
        response.status === 404
          ? "Today workout is not available for that user or date yet."
          : "The backend could not return today's workout right now.";

      return {
        data: null,
        error: {
          heading: "Unable to load workout",
          message,
          statusCode: response.status,
        },
      };
    }

    const data = (await response.json()) as TodayWorkoutResponse;

    return {
      data,
      error: null,
    };
  } catch {
    return {
      data: null,
      error: {
        heading: "Backend unavailable",
        message:
          "Start the FastAPI server, then refresh this page to load today's workout.",
      },
    };
  }
}
