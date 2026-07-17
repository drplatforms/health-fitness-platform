export interface WorkoutExerciseMemoryIdentity {
  catalog_exercise_id: number | null;
  exercise_name: string;
}

export interface WorkoutExerciseMemory {
  memory_id: number;
  catalog_exercise_id: number | null;
  exercise_name: string;
  memory_text: string;
  created_at: string | null;
  updated_at: string | null;
}

export interface WorkoutExerciseMemoryResolution {
  requested_catalog_exercise_id: number | null;
  requested_exercise_name: string;
  memory: WorkoutExerciseMemory | null;
}

export interface WorkoutExerciseMemoryResolveResponse {
  success: boolean;
  user_id: number;
  resolved_exercises: WorkoutExerciseMemoryResolution[];
}

export interface WorkoutExerciseMemorySaveResponse {
  success: boolean;
  user_id: number;
  memory: WorkoutExerciseMemory;
}

export interface WorkoutExerciseMemoryDeleteResponse {
  success: boolean;
  user_id: number;
  deleted_memory_id: number;
}
