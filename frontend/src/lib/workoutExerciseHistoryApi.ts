import type { DailyDriverApiError } from "@/lib/dailyDriverApi";
import type {
  ExerciseHistoryAnalyticsSummary,
  RecentWorkingLoadTrend,
  WorkoutExerciseHistoryAnalyticsResponse,
} from "@/types/workoutExerciseHistory";

interface RouteErrorPayload {
  detail?: string;
}

export interface WorkoutExerciseHistoryAnalyticsApiResult {
  data: WorkoutExerciseHistoryAnalyticsResponse | null;
  error: DailyDriverApiError | null;
}

export interface WorkoutExerciseHistoryAnalyticsOptions {
  lookbackDays?: number;
  exerciseLimit?: number;
  sessionLimit?: number;
}

export function buildWorkoutHistoryHref(userId: number): string {
  return `/workout/history?user_id=${userId}`;
}

export function exerciseAnalyticsKey(
  exercise: Pick<
    ExerciseHistoryAnalyticsSummary,
    "catalog_exercise_id" | "exercise_name"
  >,
): string {
  return exercise.catalog_exercise_id !== null
    ? `catalog:${exercise.catalog_exercise_id}`
    : `name:${exercise.exercise_name.trim().toLowerCase().replace(/\s+/g, " ")}`;
}

export function describeWorkingLoadTrend(
  trend: RecentWorkingLoadTrend,
): string | null {
  if (trend.status === "insufficient_data") {
    return null;
  }
  if (trend.status === "steady") {
    return "Recent working load: steady";
  }
  if (trend.absolute_change_lb === null) {
    return null;
  }
  const direction = trend.status === "higher_recently" ? "higher" : "lower";
  return `Recent working load: ${formatNumber(trend.absolute_change_lb)} lb ${direction}`;
}

export async function fetchWorkoutExerciseHistoryAnalytics(
  userId: number,
  options: WorkoutExerciseHistoryAnalyticsOptions = {},
): Promise<WorkoutExerciseHistoryAnalyticsApiResult> {
  const params = new URLSearchParams({ user_id: String(userId) });
  if (options.lookbackDays !== undefined) {
    params.set("lookback_days", String(options.lookbackDays));
  }
  if (options.exerciseLimit !== undefined) {
    params.set("exercise_limit", String(options.exerciseLimit));
  }
  if (options.sessionLimit !== undefined) {
    params.set("session_limit", String(options.sessionLimit));
  }

  try {
    const response = await fetch(
      `/api/workout-exercise-history-analytics?${params.toString()}`,
      {
        cache: "no-store",
        headers: { Accept: "application/json" },
      },
    );
    const payload = (await response.json().catch(() => null)) as
      | WorkoutExerciseHistoryAnalyticsResponse
      | RouteErrorPayload
      | null;
    if (!response.ok) {
      return {
        data: null,
        error: {
          heading: "Unable to load training history",
          message:
            (payload && "detail" in payload ? payload.detail : null) ??
            "The backend could not return exercise history right now.",
          statusCode: response.status,
        },
      };
    }
    return {
      data: payload as WorkoutExerciseHistoryAnalyticsResponse,
      error: null,
    };
  } catch {
    return {
      data: null,
      error: {
        heading: "Backend unavailable",
        message: "Start the FastAPI server, then refresh training history.",
      },
    };
  }
}

function formatNumber(value: number): string {
  return Number.isInteger(value) ? String(value) : value.toFixed(1);
}
