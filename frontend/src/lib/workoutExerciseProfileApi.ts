import type { DailyDriverApiError } from "@/lib/dailyDriverApi";
import type {
  WorkoutExerciseFamiliarity,
  WorkoutExercisePreference,
  WorkoutExerciseProfile,
  WorkoutExerciseProfileDeleteResponse,
  WorkoutExerciseProfileResolveResponse,
  WorkoutExerciseProfileResolution,
  WorkoutExerciseProfileSaveResponse,
} from "@/types/workoutExerciseProfile";

export const MAX_WORKOUT_EXERCISE_PROFILE_BATCH_SIZE = 24;

interface RouteErrorPayload {
  detail?: string;
  message?: string;
}

export interface WorkoutExerciseProfileApiResult<T> {
  data: T | null;
  error: DailyDriverApiError | null;
}

export function dedupeWorkoutExerciseProfileIds(
  catalogExerciseIds: Array<number | null>,
): number[] {
  const unique: number[] = [];
  const seen = new Set<number>();
  for (const catalogExerciseId of catalogExerciseIds) {
    if (
      catalogExerciseId === null ||
      !Number.isInteger(catalogExerciseId) ||
      catalogExerciseId <= 0 ||
      seen.has(catalogExerciseId)
    ) {
      continue;
    }
    seen.add(catalogExerciseId);
    unique.push(catalogExerciseId);
    if (unique.length >= MAX_WORKOUT_EXERCISE_PROFILE_BATCH_SIZE) {
      break;
    }
  }
  return unique;
}

export function mapWorkoutExerciseProfileResolutions(
  resolutions: WorkoutExerciseProfileResolution[],
): Record<number, WorkoutExerciseProfile | null> {
  return resolutions.reduce<Record<number, WorkoutExerciseProfile | null>>(
    (mapped, resolution) => {
      mapped[resolution.requested_catalog_exercise_id] = resolution.profile;
      return mapped;
    },
    {},
  );
}

export function exerciseInstructionAffordance(
  familiarity: WorkoutExerciseFamiliarity | null | undefined,
): "How To" | "Learn" | "Review" {
  if (familiarity === "unfamiliar") {
    return "Learn";
  }
  if (familiarity === "learning") {
    return "Review";
  }
  return "How To";
}

function routeError(
  payload: RouteErrorPayload | null,
  statusCode: number,
  fallbackMessage: string,
): DailyDriverApiError {
  return {
    heading: "Unable to update exercise profile",
    message: payload?.detail ?? payload?.message ?? fallbackMessage,
    statusCode,
  };
}

export async function fetchWorkoutExerciseProfiles(
  userId: number,
  catalogExerciseIds: Array<number | null>,
): Promise<WorkoutExerciseProfileApiResult<WorkoutExerciseProfileResolveResponse>> {
  const requestedIds = dedupeWorkoutExerciseProfileIds(catalogExerciseIds);
  if (!requestedIds.length) {
    return { data: null, error: null };
  }
  try {
    const response = await fetch("/api/workout-exercise-profiles", {
      method: "POST",
      cache: "no-store",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        user_id: userId,
        catalog_exercise_ids: requestedIds,
      }),
    });
    const payload = (await response.json().catch(() => null)) as
      | WorkoutExerciseProfileResolveResponse
      | RouteErrorPayload
      | null;
    if (!response.ok) {
      return {
        data: null,
        error: routeError(
          payload as RouteErrorPayload | null,
          response.status,
          "The backend could not load exercise profiles.",
        ),
      };
    }
    return {
      data: payload as WorkoutExerciseProfileResolveResponse,
      error: null,
    };
  } catch {
    return {
      data: null,
      error: {
        heading: "Backend unavailable",
        message: "Start the FastAPI server, then refresh to load profiles.",
      },
    };
  }
}

export async function saveWorkoutExerciseProfile(
  userId: number,
  catalogExerciseId: number,
  familiarityState: WorkoutExerciseFamiliarity | null,
  preferenceState: WorkoutExercisePreference | null,
): Promise<WorkoutExerciseProfileApiResult<WorkoutExerciseProfileSaveResponse>> {
  try {
    const response = await fetch("/api/workout-exercise-profiles", {
      method: "PUT",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        user_id: userId,
        catalog_exercise_id: catalogExerciseId,
        familiarity_state: familiarityState,
        preference_state: preferenceState,
      }),
    });
    const payload = (await response.json().catch(() => null)) as
      | WorkoutExerciseProfileSaveResponse
      | RouteErrorPayload
      | null;
    if (!response.ok) {
      return {
        data: null,
        error: routeError(
          payload as RouteErrorPayload | null,
          response.status,
          "The backend could not save this exercise profile.",
        ),
      };
    }
    return {
      data: payload as WorkoutExerciseProfileSaveResponse,
      error: null,
    };
  } catch {
    return {
      data: null,
      error: {
        heading: "Backend unavailable",
        message: "Start the FastAPI server, then try saving again.",
      },
    };
  }
}

export async function deleteWorkoutExerciseProfile(
  userId: number,
  catalogExerciseId: number,
): Promise<WorkoutExerciseProfileApiResult<WorkoutExerciseProfileDeleteResponse>> {
  try {
    const response = await fetch("/api/workout-exercise-profiles", {
      method: "DELETE",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        user_id: userId,
        catalog_exercise_id: catalogExerciseId,
      }),
    });
    const payload = (await response.json().catch(() => null)) as
      | WorkoutExerciseProfileDeleteResponse
      | RouteErrorPayload
      | null;
    if (!response.ok) {
      return {
        data: null,
        error: routeError(
          payload as RouteErrorPayload | null,
          response.status,
          "The backend could not reset this exercise profile.",
        ),
      };
    }
    return {
      data: payload as WorkoutExerciseProfileDeleteResponse,
      error: null,
    };
  } catch {
    return {
      data: null,
      error: {
        heading: "Backend unavailable",
        message: "Start the FastAPI server, then try resetting again.",
      },
    };
  }
}
