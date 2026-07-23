export type WorkingLoadTrendStatus =
  | "higher_recently"
  | "steady"
  | "lower_recently"
  | "insufficient_data";

export type ExerciseMeasurementType = "reps" | "duration" | "distance";

export type ExercisePerformanceModality =
  | "externally_weighted"
  | "bodyweight"
  | "timed"
  | "carry"
  | "cardio"
  | "distance";

export type ExercisePerformanceMetricType =
  | "load"
  | "reps"
  | "duration"
  | "distance";

export type ExercisePerformanceMetricUnit =
  | "lb"
  | "reps"
  | "seconds"
  | "meters";

export interface ExerciseHistoryAnalyticsOverview {
  has_history: boolean;
  completed_workout_count: number;
  completed_set_count: number;
  distinct_effective_exercise_count: number;
  most_recent_completed_workout_date: string | null;
}

export interface ExerciseHistoryBestSet {
  performed_at: string | null;
  actual_reps: number | null;
  actual_weight: number | null;
  actual_rir: number | null;
  summary: string;
}

export interface ExerciseHistoryRecentSession {
  session_key: string;
  performed_at: string | null;
  completed_set_count: number;
  planned_set_count: number;
  summary: string;
  measurement_type: ExerciseMeasurementType;
  modality: ExercisePerformanceModality;
  comparable_working_weight: number | null;
  average_actual_rir: number | null;
  performance_metric: ExercisePerformanceMetric | null;
  relative_position: number | null;
  previous_comparison: ExercisePerformanceComparison | null;
  phase: ExercisePerformancePhase | null;
  milestones: ExercisePerformanceMilestone[];
  has_set_details: boolean;
  recorded_sets: ExerciseHistoryRecordedSet[];
  completed_sets: ExerciseHistoryCompletedSet[];
}

export interface ExerciseHistoryCompletedSet {
  set_number: number;
  measurement_type: ExerciseMeasurementType;
  actual_reps: number | null;
  actual_duration_seconds: number | null;
  actual_distance_meters: number | null;
  actual_weight: number | null;
  actual_rir: number | null;
}

export interface ExerciseHistoryRecordedSet extends ExerciseHistoryCompletedSet {
  completed: boolean;
  skipped: boolean;
}

export interface ExercisePerformanceMetric {
  metric_type: ExercisePerformanceMetricType;
  label: string;
  value: number;
  unit: ExercisePerformanceMetricUnit;
}

export interface ExercisePerformanceComparison {
  metric_type: ExercisePerformanceMetricType;
  unit: ExercisePerformanceMetricUnit;
  then_performed_at: string | null;
  then_value: number;
  now_performed_at: string | null;
  now_value: number;
  absolute_change: number;
  percent_change: number | null;
  direction: "higher" | "lower" | "steady";
  comparable_session_count: number;
}

export interface ExercisePerformancePhase {
  code:
    | "progression"
    | "stable_effort_rise"
    | "plateau"
    | "deload"
    | "rebound";
  label: string;
  evidence: string;
  evidence_session_count: number;
}

export interface ExercisePerformancePhaseSegment
  extends ExercisePerformancePhase {
  start_date: string;
  end_date: string;
  start_session_key: string;
  end_session_key: string;
}

export interface ExercisePerformanceMilestone {
  code: "personal_best";
  label: string;
  evidence: string;
  performed_at: string;
  session_key: string;
}

export interface ExerciseHistoryProgressionRecommendation {
  decision:
    | "increase_load"
    | "increase_reps"
    | "hold"
    | "decrease_load"
    | "build_baseline";
  headline: string;
  target_guidance: string;
  evidence_session_count: number;
  confidence: string;
}

export interface RecentWorkingLoadTrend {
  status: WorkingLoadTrendStatus;
  latest_comparable_working_weight: number | null;
  comparison_working_weight: number | null;
  absolute_change_lb: number | null;
  qualifying_session_count: number;
}

export interface ExerciseHistoryAnalyticsSummary {
  catalog_exercise_id: number | null;
  exercise_name: string;
  measurement_type: ExerciseMeasurementType;
  modality: ExercisePerformanceModality;
  completed_session_count: number;
  last_performed_at: string | null;
  latest_completed_session_summary: string;
  recent_best_set: ExerciseHistoryBestSet | null;
  progression_recommendation: ExerciseHistoryProgressionRecommendation;
  logging_quality: "none" | "limited" | "incomplete" | "complete";
  limitation: string | null;
  recent_working_load_trend: RecentWorkingLoadTrend;
  then_vs_now: ExercisePerformanceComparison | null;
  performance_phase: ExercisePerformancePhase | null;
  current_trend: ExercisePerformancePhase | null;
  historical_phase_segments: ExercisePerformancePhaseSegment[];
  milestones: ExercisePerformanceMilestone[];
  recent_sessions: ExerciseHistoryRecentSession[];
}

export interface WorkoutExerciseHistoryAnalyticsResponse {
  success: boolean;
  user_id: number;
  lookback_days: number;
  exercise_limit: number;
  session_limit: number;
  include_set_details: boolean;
  overview: ExerciseHistoryAnalyticsOverview;
  exercises: ExerciseHistoryAnalyticsSummary[];
}

export interface WorkoutExerciseHistorySessionDetailResponse {
  success: boolean;
  user_id: number;
  lookback_days: number;
  session: ExerciseHistoryRecentSession;
}
