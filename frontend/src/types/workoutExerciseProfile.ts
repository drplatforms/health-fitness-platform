export type WorkoutExerciseFamiliarity =
  | "unfamiliar"
  | "learning"
  | "familiar";

export type WorkoutExercisePreference = "favorite" | "disliked";

export interface WorkoutExerciseProfile {
  profile_id: number;
  catalog_exercise_id: number;
  familiarity_state: WorkoutExerciseFamiliarity | null;
  preference_state: WorkoutExercisePreference | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface WorkoutExerciseProfileResolution {
  requested_catalog_exercise_id: number;
  profile: WorkoutExerciseProfile | null;
}

export interface WorkoutExerciseProfileResolveResponse {
  success: boolean;
  user_id: number;
  resolved_exercises: WorkoutExerciseProfileResolution[];
}

export interface WorkoutExerciseProfileSaveResponse {
  success: boolean;
  user_id: number;
  profile: WorkoutExerciseProfile | null;
}

export interface WorkoutExerciseProfileDeleteResponse {
  success: boolean;
  user_id: number;
  catalog_exercise_id: number;
  deleted: boolean;
}
