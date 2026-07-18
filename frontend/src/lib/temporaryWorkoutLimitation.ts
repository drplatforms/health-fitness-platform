export interface TemporaryWorkoutLimitation {
  user_id: number;
  affected_regions: string[];
  restricted_movement_patterns: string[];
  excluded_catalog_exercise_ids: number[];
  expires_at: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface WorkoutLimitationConflict {
  planned_exercise_id: number | null;
  exercise_name: string;
  conflict_type: string;
  movement_pattern: string | null;
}

export interface TemporaryWorkoutLimitationResponse {
  success: boolean;
  user_id: number;
  active: boolean;
  limitation: TemporaryWorkoutLimitation | null;
  current_plan_conflicts: WorkoutLimitationConflict[];
  cleared?: boolean;
}

export interface LimitationCatalogExercise {
  id: number;
  name: string;
  movement_pattern: string;
}

export interface TemporaryWorkoutLimitationSavePayload {
  affected_regions: string[];
  restricted_movement_patterns: string[];
  excluded_catalog_exercise_ids: number[];
  expires_at: string | null;
}

export const AFFECTED_REGION_OPTIONS = [
  "neck",
  "shoulder",
  "elbow",
  "wrist_hand",
  "upper_back",
  "lower_back",
  "hip",
  "knee",
  "ankle_foot",
] as const;

export function limitationTokenLabel(value: string): string {
  return value
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

export function computeLimitationExpiresAt(
  duration: "until_cleared" | "3_days" | "7_days" | "14_days" | "existing",
  existing: string | null,
  now = new Date(),
): string | null {
  if (duration === "until_cleared") return null;
  if (duration === "existing") return existing;
  const days = duration === "3_days" ? 3 : duration === "7_days" ? 7 : 14;
  return new Date(now.getTime() + days * 86_400_000).toISOString();
}

export function limitationSummary(
  limitation: TemporaryWorkoutLimitation,
  locale = "en-US",
): string {
  const movementCount = limitation.restricted_movement_patterns.length;
  const exerciseCount = limitation.excluded_catalog_exercise_ids.length;
  const parts = [
    `${movementCount} movement restriction${movementCount === 1 ? "" : "s"}`,
    `${exerciseCount} exercise${exerciseCount === 1 ? "" : "s"}`,
  ];
  if (limitation.expires_at) {
    parts.push(
      `through ${new Intl.DateTimeFormat(locale, {
        month: "short",
        day: "numeric",
      }).format(new Date(limitation.expires_at))}`,
    );
  } else {
    parts.push("until cleared");
  }
  return parts.join(" · ");
}

async function limitationRequest(
  method: "GET" | "PUT" | "DELETE",
  userId: number,
  payload?: TemporaryWorkoutLimitationSavePayload,
): Promise<TemporaryWorkoutLimitationResponse> {
  const endpoint =
    method === "GET"
      ? `/api/temporary-workout-limitation?user_id=${encodeURIComponent(userId)}`
      : "/api/temporary-workout-limitation";
  const response = await fetch(endpoint, {
    method,
    cache: "no-store",
    headers: {
      Accept: "application/json",
      ...(method === "GET" ? {} : { "Content-Type": "application/json" }),
    },
    body:
      method === "GET"
        ? undefined
        : JSON.stringify({ user_id: userId, ...(payload ?? {}) }),
  });
  const body = (await response.json().catch(() => null)) as
    | TemporaryWorkoutLimitationResponse
    | { detail?: string }
    | null;
  if (!response.ok) {
    throw new Error(
      body && "detail" in body && body.detail
        ? body.detail
        : "Unable to update the temporary limitation.",
    );
  }
  return body as TemporaryWorkoutLimitationResponse;
}

export function fetchTemporaryWorkoutLimitation(userId: number) {
  return limitationRequest("GET", userId);
}

export function saveTemporaryWorkoutLimitation(
  userId: number,
  payload: TemporaryWorkoutLimitationSavePayload,
) {
  return limitationRequest("PUT", userId, payload);
}

export function clearTemporaryWorkoutLimitation(userId: number) {
  return limitationRequest("DELETE", userId);
}

export async function fetchLimitationExerciseCatalog(): Promise<
  LimitationCatalogExercise[]
> {
  const response = await fetch("/api/exercise-catalog", {
    cache: "no-store",
    headers: { Accept: "application/json" },
  });
  const payload = (await response.json().catch(() => null)) as
    | { exercises?: LimitationCatalogExercise[]; detail?: string }
    | null;
  if (!response.ok) {
    throw new Error(payload?.detail ?? "Unable to load the exercise catalog.");
  }
  return (payload?.exercises ?? []).filter(
    (exercise) =>
      Number.isInteger(exercise.id) &&
      exercise.id > 0 &&
      Boolean(exercise.name) &&
      Boolean(exercise.movement_pattern),
  );
}
