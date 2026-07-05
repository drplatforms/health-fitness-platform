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

export type WorkoutSizePreference = "quick" | "standard" | "full";

export interface WorkoutPreviewExercise {
  name: string;
  sets: number;
  reps_min: number;
  reps_max: number;
  rir_min: number;
  rir_max: number;
  notes: string;
  equipment_required: string[];
}

export interface ApprovedWorkoutPlanPreview {
  title: string;
  session_focus: string;
  duration_minutes: number;
  exercises: WorkoutPreviewExercise[];
  warmup: string;
  cooldown: string;
  progression_guidance: string;
  rationale: string;
  confidence: string;
  scenario: string;
  reason_codes: string[];
  workout_size_preference: WorkoutSizePreference;
  requested_exercise_count: number;
  final_target_exercise_count: number;
  exercise_count_reason: string;
  exercise_count_user_reason: string;
}

export interface WorkoutPreviewResponse {
  success: boolean;
  user_id: number;
  scenario: string;
  confidence: string;
  workout_exercise_count: {
    requested_size: WorkoutSizePreference;
    requested_count: number;
    final_count: number;
    final_target_count: number;
    reason: string;
    user_safe_reason: string;
  };
  approved_workout_plan: ApprovedWorkoutPlanPreview;
  rendered_workout_plan: string;
}

export interface WorkoutPlanInstanceSummary {
  id: number;
  user_id: number;
  status: string;
  scenario: string;
  confidence: string;
  title: string;
  selected_at: string | null;
  completed_at: string | null;
  abandoned_at: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface WorkoutExecutionSessionSummary {
  id: number;
  workout_plan_instance_id: number;
  user_id: number;
  status: string;
  workout_session_id: number | null;
  started_at: string | null;
  completed_at: string | null;
  abandoned_at: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface WorkoutSelectPreviewResponse {
  success: boolean;
  user_id: number;
  scenario: string;
  confidence: string;
  workout_plan_instance: WorkoutPlanInstanceSummary;
  execution_session: WorkoutExecutionSessionSummary;
  approved_workout_plan: ApprovedWorkoutPlanPreview;
}

export interface WorkoutStartResponse {
  success: boolean;
  workout_plan_instance_id: number;
  user_id: number;
  scenario: string;
  confidence: string;
  workout_plan_instance: WorkoutPlanInstanceSummary;
  execution_session: WorkoutExecutionSessionSummary;
  approved_workout_plan: ApprovedWorkoutPlanPreview;
}

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
