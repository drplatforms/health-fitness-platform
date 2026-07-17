import type { DailyDriverApiError } from "@/lib/dailyDriverApi";
import type {
  WorkoutExerciseMemory,
  WorkoutExerciseMemoryDeleteResponse,
  WorkoutExerciseMemoryIdentity,
  WorkoutExerciseMemoryResolveResponse,
  WorkoutExerciseMemoryResolution,
  WorkoutExerciseMemorySaveResponse,
} from "@/types/workoutExerciseMemory";

export const MAX_WORKOUT_EXERCISE_MEMORY_CHARACTERS = 500;
export const MAX_WORKOUT_EXERCISE_MEMORY_BATCH_SIZE = 24;

interface RouteErrorPayload {
  detail?: string;
  message?: string;
}

export interface WorkoutExerciseMemoryApiResult<T> {
  data: T | null;
  error: DailyDriverApiError | null;
}

export function normalizeWorkoutExerciseMemoryName(value: string): string {
  return value.trim().toLowerCase().replace(/\s+/g, " ");
}

export function workoutExerciseMemoryIdentityKey(
  identity: WorkoutExerciseMemoryIdentity,
): string {
  return identity.catalog_exercise_id !== null
    ? `catalog:${identity.catalog_exercise_id}`
    : `name:${normalizeWorkoutExerciseMemoryName(identity.exercise_name)}`;
}

export function dedupeWorkoutExerciseMemoryRequests(
  exercises: WorkoutExerciseMemoryIdentity[],
): WorkoutExerciseMemoryIdentity[] {
  const unique: WorkoutExerciseMemoryIdentity[] = [];
  const seen = new Set<string>();

  for (const exercise of exercises) {
    const exerciseName = exercise.exercise_name.trim();
    if (!exerciseName) {
      continue;
    }
    const normalizedExercise = {
      catalog_exercise_id: exercise.catalog_exercise_id,
      exercise_name: exerciseName,
    };
    const key = workoutExerciseMemoryIdentityKey(normalizedExercise);
    if (seen.has(key)) {
      continue;
    }
    seen.add(key);
    unique.push(normalizedExercise);
    if (unique.length >= MAX_WORKOUT_EXERCISE_MEMORY_BATCH_SIZE) {
      break;
    }
  }

  return unique;
}

export function mapWorkoutExerciseMemoryResolutions(
  resolutions: WorkoutExerciseMemoryResolution[],
): Record<string, WorkoutExerciseMemory | null> {
  return resolutions.reduce<Record<string, WorkoutExerciseMemory | null>>(
    (mapped, resolution) => {
      mapped[
        workoutExerciseMemoryIdentityKey({
          catalog_exercise_id: resolution.requested_catalog_exercise_id,
          exercise_name: resolution.requested_exercise_name,
        })
      ] = resolution.memory;
      return mapped;
    },
    {},
  );
}

function routeError(
  payload: RouteErrorPayload | null,
  statusCode: number,
  fallbackMessage: string,
): DailyDriverApiError {
  return {
    heading: "Unable to update exercise memory",
    message: payload?.detail ?? payload?.message ?? fallbackMessage,
    statusCode,
  };
}

export async function fetchWorkoutExerciseMemories(
  userId: number,
  exercises: WorkoutExerciseMemoryIdentity[],
): Promise<
  WorkoutExerciseMemoryApiResult<WorkoutExerciseMemoryResolveResponse>
> {
  const requestedExercises = dedupeWorkoutExerciseMemoryRequests(exercises);
  if (!requestedExercises.length) {
    return { data: null, error: null };
  }

  try {
    const response = await fetch("/api/workout-exercise-memories", {
      method: "POST",
      cache: "no-store",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ user_id: userId, exercises: requestedExercises }),
    });
    const payload = (await response.json().catch(() => null)) as
      | WorkoutExerciseMemoryResolveResponse
      | RouteErrorPayload
      | null;
    if (!response.ok) {
      return {
        data: null,
        error: routeError(
          payload as RouteErrorPayload | null,
          response.status,
          "The backend could not load exercise memories.",
        ),
      };
    }
    return {
      data: payload as WorkoutExerciseMemoryResolveResponse,
      error: null,
    };
  } catch {
    return {
      data: null,
      error: {
        heading: "Backend unavailable",
        message: "Start the FastAPI server, then refresh to load exercise memories.",
      },
    };
  }
}

export async function saveWorkoutExerciseMemory(
  userId: number,
  identity: WorkoutExerciseMemoryIdentity,
  memoryText: string,
  memoryId?: number,
): Promise<WorkoutExerciseMemoryApiResult<WorkoutExerciseMemorySaveResponse>> {
  try {
    const response = await fetch("/api/workout-exercise-memories", {
      method: "PUT",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        user_id: userId,
        memory_id: memoryId,
        ...identity,
        memory_text: memoryText,
      }),
    });
    const payload = (await response.json().catch(() => null)) as
      | WorkoutExerciseMemorySaveResponse
      | RouteErrorPayload
      | null;
    if (!response.ok) {
      return {
        data: null,
        error: routeError(
          payload as RouteErrorPayload | null,
          response.status,
          "The backend could not save this exercise memory.",
        ),
      };
    }
    return {
      data: payload as WorkoutExerciseMemorySaveResponse,
      error: null,
    };
  } catch {
    return {
      data: null,
      error: {
        heading: "Backend unavailable",
        message: "Start the FastAPI server, then try saving this memory again.",
      },
    };
  }
}

export async function deleteWorkoutExerciseMemory(
  userId: number,
  memoryId: number,
): Promise<WorkoutExerciseMemoryApiResult<WorkoutExerciseMemoryDeleteResponse>> {
  try {
    const response = await fetch("/api/workout-exercise-memories", {
      method: "DELETE",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ user_id: userId, memory_id: memoryId }),
    });
    const payload = (await response.json().catch(() => null)) as
      | WorkoutExerciseMemoryDeleteResponse
      | RouteErrorPayload
      | null;
    if (!response.ok) {
      return {
        data: null,
        error: routeError(
          payload as RouteErrorPayload | null,
          response.status,
          "The backend could not delete this exercise memory.",
        ),
      };
    }
    return {
      data: payload as WorkoutExerciseMemoryDeleteResponse,
      error: null,
    };
  } catch {
    return {
      data: null,
      error: {
        heading: "Backend unavailable",
        message: "Start the FastAPI server, then try deleting this memory again.",
      },
    };
  }
}
