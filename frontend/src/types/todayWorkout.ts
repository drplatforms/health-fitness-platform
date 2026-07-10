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

export interface PlannedWorkoutExerciseSummary {
  id: number;
  workout_plan_instance_id: number;
  exercise_order: number;
  name: string;
  sets: number;
  reps_min: number;
  reps_max: number;
  rir_min: number;
  rir_max: number;
  notes: string;
  equipment_required: string[];
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
  planned_exercises: PlannedWorkoutExerciseSummary[];
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
  planned_exercises: PlannedWorkoutExerciseSummary[];
  execution_session: WorkoutExecutionSessionSummary;
  approved_workout_plan: ApprovedWorkoutPlanPreview;
}

export interface WorkoutDailyStateSummary {
  user_id: number;
  target_date: string;
  state: string;
  selected_plan_id: number | null;
  selected_plan_date: string | null;
  active_plan_id: number | null;
  active_plan_date: string | null;
  completed_workout_id: number | null;
  completed_plan_date: string | null;
  expired_plan_id: number | null;
  expired_plan_date: string | null;
  stale_state_detected: boolean;
  substitution_state_should_clear: boolean;
  user_safe_message: string | null;
  developer_metadata: Record<string, unknown>;
  selected_at: string | null;
  started_at: string | null;
  completed_at: string | null;
  updated_at: string | null;
}

export interface WorkoutActualSetSummary {
  id: number;
  workout_execution_session_id: number;
  planned_workout_exercise_id: number | null;
  workout_session_id: number | null;
  workout_set_id: number | null;
  exercise_name: string;
  set_number: number;
  planned_reps_min: number | null;
  planned_reps_max: number | null;
  planned_rir_min: number | null;
  planned_rir_max: number | null;
  actual_reps: number | null;
  actual_weight: number | null;
  actual_rir: number | null;
  completed: boolean;
  skipped: boolean;
  substitution_for_planned_exercise_id: number | null;
  notes: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface WorkoutActiveSubstitutionSummary {
  id: number;
  workout_plan_instance_id: number;
  workout_execution_session_id: number | null;
  planned_workout_exercise_id: number;
  original_exercise_name: string;
  replacement_exercise_name: string;
  replacement_catalog_exercise_id: number;
  original_movement_pattern: string;
  replacement_movement_pattern: string;
  substitution_reason: string;
  status: string;
  created_at: string | null;
  updated_at: string | null;
}

export interface WorkoutPlannedVsActualSummary {
  workout_plan_instance_id: number;
  workout_execution_session_id: number | null;
  planned_exercise_count: number;
  completed_exercise_count: number;
  skipped_exercise_count: number;
  substituted_exercise_count: number;
  planned_set_count: number;
  actual_set_count: number;
  completed_set_count: number;
  skipped_set_count: number;
  completion_percentage: number;
  average_planned_rir: number | null;
  average_actual_rir: number | null;
  rir_deviation: number | null;
  rep_deviation: {
    sets_below_planned_reps: number;
    sets_inside_planned_reps: number;
    sets_above_planned_reps: number;
  };
  sets_below_planned_reps: number;
  sets_inside_planned_reps: number;
  sets_above_planned_reps: number;
  notes: string[];
  deviation_flags: string[];
}

export interface WorkoutCurrentExecutionState {
  workout_plan_instance: WorkoutPlanInstanceSummary;
  execution_session: WorkoutExecutionSessionSummary;
  planned_exercises: PlannedWorkoutExerciseSummary[];
  actual_sets: WorkoutActualSetSummary[];
  active_substitutions: WorkoutActiveSubstitutionSummary[];
  approved_workout_plan: ApprovedWorkoutPlanPreview;
}

export interface WorkoutCurrentResponse {
  success: boolean;
  user_id: number;
  workout_daily_state: WorkoutDailyStateSummary;
  current_execution_state: WorkoutCurrentExecutionState | null;
}

export interface WorkoutActualSetCreatePayload {
  planned_workout_exercise_id?: number;
  exercise_name?: string;
  set_number?: number;
  actual_reps?: number;
  actual_weight?: number;
  actual_rir?: number;
  completed?: boolean;
  skipped?: boolean;
  substitution_for_planned_exercise_id?: number;
  notes?: string;
}

export interface WorkoutActualSetCreateResponse {
  success: boolean;
  workout_plan_instance_id: number;
  actual_set: WorkoutActualSetSummary;
  workout_plan_instance: WorkoutPlanInstanceSummary;
  execution_session: WorkoutExecutionSessionSummary;
  actual_sets: WorkoutActualSetSummary[];
}

export type WorkoutActualSetUpdatePayload = WorkoutActualSetCreatePayload;

export interface WorkoutActualSetUpdateResponse {
  success: boolean;
  workout_plan_instance_id: number;
  actual_set: WorkoutActualSetSummary;
  workout_plan_instance: WorkoutPlanInstanceSummary;
  execution_session: WorkoutExecutionSessionSummary;
  planned_vs_actual_summary: WorkoutPlannedVsActualSummary;
}

export interface WorkoutActualSetDeleteResponse {
  success: boolean;
  workout_plan_instance_id: number;
  workout_plan_instance: WorkoutPlanInstanceSummary;
  execution_session: WorkoutExecutionSessionSummary;
  actual_sets: WorkoutActualSetSummary[];
  planned_vs_actual_summary: WorkoutPlannedVsActualSummary;
}

export interface WorkoutCompleteResponse {
  success: boolean;
  workout_plan_instance_id: number;
  workout_plan_instance: WorkoutPlanInstanceSummary;
  execution_session: WorkoutExecutionSessionSummary;
  planned_vs_actual_summary: WorkoutPlannedVsActualSummary;
}

export interface WorkoutPlannedVsActualResponse {
  success: boolean;
  workout_plan_instance_id: number;
  workout_plan_instance: WorkoutPlanInstanceSummary;
  execution_session: WorkoutExecutionSessionSummary;
  planned_vs_actual_summary: WorkoutPlannedVsActualSummary;
  planned_exercises: PlannedWorkoutExerciseSummary[];
  actual_sets: WorkoutActualSetSummary[];
}

export interface WorkoutExerciseBestSet {
  performed_at: string | null;
  actual_reps: number | null;
  actual_weight: number | null;
  actual_rir: number | null;
  summary: string;
}

export interface WorkoutExerciseHistorySummary {
  exercise_name: string;
  has_history: boolean;
  completed_session_count: number;
  last_performed_at: string | null;
  last_session_summary: string | null;
  recent_best_set: WorkoutExerciseBestSet | null;
  logging_quality: string;
  message: string;
}

export interface WorkoutProgressionHistoryResponse {
  success: boolean;
  user_id: number;
  lookback_days: number;
  exercise_histories: WorkoutExerciseHistorySummary[];
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
