import { DailyDriverTodayResponse } from "@/types/dailyDriver";

export interface DailyDriverRequestOptions {
  date?: string;
  userId?: number;
}

export interface DailyDriverApiError {
  heading: string;
  message: string;
  statusCode?: number;
}

export interface DailyDriverApiResult {
  data: DailyDriverTodayResponse | null;
  error: DailyDriverApiError | null;
}

const DEFAULT_API_BASE_URL = "http://localhost:8000";
const DEFAULT_USER_ID = 101;

export function getApiBaseUrl(): string {
  return process.env.FITNESS_API_BASE_URL?.trim() || DEFAULT_API_BASE_URL;
}

export function getDefaultUserId(): number {
  const rawValue = process.env.FITNESS_DEFAULT_USER_ID?.trim();
  if (!rawValue) {
    return DEFAULT_USER_ID;
  }

  const parsed = Number.parseInt(rawValue, 10);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : DEFAULT_USER_ID;
}

export function resolveTodayQuery(
  searchParams: Record<string, string | string[] | undefined>,
): DailyDriverRequestOptions {
  const userIdValue = searchParams.user_id;
  const dateValue = searchParams.date;

  const userId =
    typeof userIdValue === "string"
      ? Number.parseInt(userIdValue, 10)
      : undefined;

  return {
    userId: Number.isInteger(userId) && (userId ?? 0) > 0 ? userId : undefined,
    date: typeof dateValue === "string" && dateValue.trim() ? dateValue : undefined,
  };
}

export async function fetchDailyDriverToday(
  options: DailyDriverRequestOptions = {},
): Promise<DailyDriverApiResult> {
  const userId = options.userId ?? getDefaultUserId();
  const params = new URLSearchParams({ user_id: String(userId) });

  if (options.date) {
    params.set("date", options.date);
  }

  const endpoint = `${getApiBaseUrl()}/api/today?${params.toString()}`;

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
          ? "Today is not available for that user or date yet."
          : "The backend could not return Today right now.";

      return {
        data: null,
        error: {
          heading: "Unable to load Today",
          message,
          statusCode: response.status,
        },
      };
    }

    const data = (await response.json()) as DailyDriverTodayResponse;

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
          "Start the FastAPI server, then refresh this page to load today's plan.",
      },
    };
  }
}
