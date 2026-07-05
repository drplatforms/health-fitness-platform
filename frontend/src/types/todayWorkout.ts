export type TodayWorkoutStatus =
  | "preview"
  | "selected"
  | "in_progress"
  | "completed"
  | "not_available";

export type TodayWorkoutSource =
  | "current_execution_state"
  | "deterministic_generation"
  | "none";

export interface TodayWorkoutExerciseItem {
  exercise_id: string | null;
  name: string;
  order: number;
  section: string | null;
  sets: number | null;
  reps: string | null;
  weight: number | null;
  weight_unit: string | null;
  rest_seconds: number | null;
  tempo: string | null;
  notes: string | null;
  substitution_notes: string | null;
}

export interface TodayWorkoutResponse {
  contract_version: string;
  user_id: number;
  target_date: string;
  status: TodayWorkoutStatus;
  title: string;
  summary: string;
  source: TodayWorkoutSource;
  workout_id: string | null;
  generated_at: string | null;
  estimated_duration_minutes: number | null;
  focus: string | null;
  equipment: string[];
  exercises: TodayWorkoutExerciseItem[];
  data_gaps: string[];
  limitations: string[];
}
