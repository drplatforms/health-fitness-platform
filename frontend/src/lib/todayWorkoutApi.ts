import {
  DailyDriverApiError,
  DailyDriverRequestOptions,
  getApiBaseUrl,
  getDefaultUserId,
} from "@/lib/dailyDriverApi";
import {
  ApprovedWorkoutPlanPreview,
  TodayWorkoutResponse,
  WorkoutPreviewResponse,
  WorkoutSelectPreviewResponse,
  WorkoutSizePreference,
  WorkoutStartResponse,
} from "@/types/todayWorkout";

interface RouteErrorPayload {
  detail?: string;
  message?: string;
}

export interface TodayWorkoutApiResult {
  data: TodayWorkoutResponse | null;
  error: DailyDriverApiError | null;
}

export interface WorkoutPreviewApiResult {
  data: WorkoutPreviewResponse | null;
  error: DailyDriverApiError | null;
}

export interface WorkoutActionApiResult<T> {
  data: T | null;
  error: DailyDriverApiError | null;
}

export interface WorkoutPreviewRequestOptions
  extends DailyDriverRequestOptions {
  workoutSizePreference?: WorkoutSizePreference;
  previewVariationIndex?: number;
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

    return {
      data: (await response.json()) as TodayWorkoutResponse,
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

export async function fetchWorkoutPreview(
  options: WorkoutPreviewRequestOptions = {},
): Promise<WorkoutPreviewApiResult> {
  const userId = options.userId ?? getDefaultUserId();
  const params = new URLSearchParams({
    user_id: String(userId),
    workout_size_preference: options.workoutSizePreference ?? "standard",
    preview_variation_index: String(options.previewVariationIndex ?? 0),
  });
  const endpoint = `/api/workout-preview?${params.toString()}`;

  try {
    const response = await fetch(endpoint, {
      cache: "no-store",
      headers: {
        Accept: "application/json",
      },
    });

    if (!response.ok) {
      const payload = (await response.json().catch(() => null)) as
        | RouteErrorPayload
        | null;
      return {
        data: null,
        error: {
          heading: "Unable to load workout preview",
          message:
            payload?.detail ??
            payload?.message ??
            "The backend could not return a workout preview right now.",
          statusCode: response.status,
        },
      };
    }

    return {
      data: (await response.json()) as WorkoutPreviewResponse,
      error: null,
    };
  } catch {
    return {
      data: null,
      error: {
        heading: "Backend unavailable",
        message:
          "Start the FastAPI server, then refresh this page to load a workout preview.",
      },
    };
  }
}

export async function selectWorkoutPreview(
  userId: number,
  approvedWorkoutPlan: ApprovedWorkoutPlanPreview,
): Promise<WorkoutActionApiResult<WorkoutSelectPreviewResponse>> {
  const endpoint = "/api/workout-select";

  try {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        user_id: userId,
        approved_workout_plan: approvedWorkoutPlan,
      }),
    });

    if (!response.ok) {
      const payload = (await response.json().catch(() => null)) as
        | RouteErrorPayload
        | null;
      return {
        data: null,
        error: {
          heading: "Unable to select workout",
          message:
            payload?.detail ??
            payload?.message ??
            "The backend could not save the visible workout preview.",
          statusCode: response.status,
        },
      };
    }

    return {
      data: (await response.json()) as WorkoutSelectPreviewResponse,
      error: null,
    };
  } catch {
    return {
      data: null,
      error: {
        heading: "Backend unavailable",
        message:
          "Start the FastAPI server, then try selecting this workout again.",
      },
    };
  }
}

export async function startWorkoutPlan(
  planInstanceId: number,
): Promise<WorkoutActionApiResult<WorkoutStartResponse>> {
  const endpoint = "/api/workout-start";

  try {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        plan_instance_id: planInstanceId,
      }),
    });

    if (!response.ok) {
      const payload = (await response.json().catch(() => null)) as
        | RouteErrorPayload
        | null;
      return {
        data: null,
        error: {
          heading: "Unable to start workout",
          message:
            payload?.detail ??
            payload?.message ??
            "The backend could not start the selected workout.",
          statusCode: response.status,
        },
      };
    }

    return {
      data: (await response.json()) as WorkoutStartResponse,
      error: null,
    };
  } catch {
    return {
      data: null,
      error: {
        heading: "Backend unavailable",
        message:
          "Start the FastAPI server, then try starting the selected workout again.",
      },
    };
  }
}
