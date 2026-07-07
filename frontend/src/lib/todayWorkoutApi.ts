import {
  DailyDriverApiError,
  DailyDriverRequestOptions,
  getApiBaseUrl,
  getDefaultUserId,
} from "@/lib/dailyDriverApi";
import {
  ApprovedWorkoutPlanPreview,
  WorkoutActualSetCreatePayload,
  WorkoutActualSetCreateResponse,
  WorkoutCompleteResponse,
  WorkoutCurrentResponse,
  WorkoutPlannedVsActualResponse,
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

export interface WorkoutPlannedVsActualApiResult {
  data: WorkoutPlannedVsActualResponse | null;
  error: DailyDriverApiError | null;
}

export interface WorkoutActionApiResult<T> {
  data: T | null;
  error: DailyDriverApiError | null;
}

export interface WorkoutCurrentApiResult {
  data: WorkoutCurrentResponse | null;
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

export async function fetchWorkoutCurrent(
  options: DailyDriverRequestOptions = {},
): Promise<WorkoutCurrentApiResult> {
  const userId = options.userId ?? getDefaultUserId();
  const params = new URLSearchParams({
    user_id: String(userId),
  });

  if (options.date) {
    params.set("date", options.date);
  }

  const endpoint = `/api/workout-current?${params.toString()}`;

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
          heading: "Unable to load current workout",
          message:
            payload?.detail ??
            payload?.message ??
            "The backend could not return the current workout state right now.",
          statusCode: response.status,
        },
      };
    }

    return {
      data: (await response.json()) as WorkoutCurrentResponse,
      error: null,
    };
  } catch {
    return {
      data: null,
      error: {
        heading: "Backend unavailable",
        message:
          "Start the FastAPI server, then refresh this page to load the current workout state.",
      },
    };
  }
}

export async function fetchWorkoutCurrentFromBackend(
  options: DailyDriverRequestOptions = {},
): Promise<WorkoutCurrentApiResult> {
  const userId = options.userId ?? getDefaultUserId();
  const params = new URLSearchParams();

  if (options.date) {
    params.set("target_date", options.date);
  }

  const query = params.toString();
  const endpoint = `${getApiBaseUrl()}/workout-plans/current/${userId}${query ? `?${query}` : ""}`;

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
        error: {
          heading: "Unable to load current workout",
          message: "The backend could not return the current workout state right now.",
          statusCode: response.status,
        },
      };
    }

    return {
      data: (await response.json()) as WorkoutCurrentResponse,
      error: null,
    };
  } catch {
    return {
      data: null,
      error: {
        heading: "Backend unavailable",
        message:
          "Start the FastAPI server, then refresh this page to load the current workout state.",
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

export async function logWorkoutActualSet(
  planInstanceId: number,
  payload: WorkoutActualSetCreatePayload,
): Promise<WorkoutActionApiResult<WorkoutActualSetCreateResponse>> {
  const endpoint = "/api/workout-actual-sets";

  try {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        plan_instance_id: planInstanceId,
        ...payload,
      }),
    });

    if (!response.ok) {
      const routePayload = (await response.json().catch(() => null)) as
        | RouteErrorPayload
        | null;
      return {
        data: null,
        error: {
          heading: "Unable to log set",
          message:
            routePayload?.detail ??
            routePayload?.message ??
            "The backend could not save that actual set.",
          statusCode: response.status,
        },
      };
    }

    return {
      data: (await response.json()) as WorkoutActualSetCreateResponse,
      error: null,
    };
  } catch {
    return {
      data: null,
      error: {
        heading: "Backend unavailable",
        message: "Start the FastAPI server, then try logging that set again.",
      },
    };
  }
}

export async function completeWorkout(
  planInstanceId: number,
): Promise<WorkoutActionApiResult<WorkoutCompleteResponse>> {
  const endpoint = "/api/workout-complete";

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
      const routePayload = (await response.json().catch(() => null)) as
        | RouteErrorPayload
        | null;
      return {
        data: null,
        error: {
          heading: "Unable to complete workout",
          message:
            routePayload?.detail ??
            routePayload?.message ??
            "The backend could not complete this workout.",
          statusCode: response.status,
        },
      };
    }

    return {
      data: (await response.json()) as WorkoutCompleteResponse,
      error: null,
    };
  } catch {
    return {
      data: null,
      error: {
        heading: "Backend unavailable",
        message:
          "Start the FastAPI server, then try completing this workout again.",
      },
    };
  }
}

export async function fetchWorkoutPlannedVsActual(
  planInstanceId: number,
): Promise<WorkoutPlannedVsActualApiResult> {
  const params = new URLSearchParams({
    plan_instance_id: String(planInstanceId),
  });
  const endpoint = `/api/workout-planned-vs-actual?${params.toString()}`;

  try {
    const response = await fetch(endpoint, {
      cache: "no-store",
      headers: {
        Accept: "application/json",
      },
    });

    if (!response.ok) {
      const routePayload = (await response.json().catch(() => null)) as
        | RouteErrorPayload
        | null;
      return {
        data: null,
        error: {
          heading: "Unable to load workout summary",
          message:
            routePayload?.detail ??
            routePayload?.message ??
            "The backend could not return the planned-vs-actual summary.",
          statusCode: response.status,
        },
      };
    }

    return {
      data: (await response.json()) as WorkoutPlannedVsActualResponse,
      error: null,
    };
  } catch {
    return {
      data: null,
      error: {
        heading: "Backend unavailable",
        message:
          "Start the FastAPI server, then refresh this page to load the workout summary.",
      },
    };
  }
}
