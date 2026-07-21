export type WorkingLoadTrendStatus =
  | "higher_recently"
  | "steady"
  | "lower_recently"
  | "insufficient_data";

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
  performed_at: string | null;
  completed_set_count: number;
  planned_set_count: number;
  summary: string;
  comparable_working_weight: number | null;
  average_actual_rir: number | null;
  completed_sets: ExerciseHistoryCompletedSet[];
}

export interface ExerciseHistoryCompletedSet {
  set_number: number;
  actual_reps: number | null;
  actual_weight: number | null;
  actual_rir: number | null;
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
  completed_session_count: number;
  last_performed_at: string | null;
  latest_completed_session_summary: string;
  recent_best_set: ExerciseHistoryBestSet | null;
  progression_recommendation: ExerciseHistoryProgressionRecommendation;
  logging_quality: "none" | "limited" | "incomplete" | "complete";
  limitation: string | null;
  recent_working_load_trend: RecentWorkingLoadTrend;
  recent_sessions: ExerciseHistoryRecentSession[];
}

export interface WorkoutExerciseHistoryAnalyticsResponse {
  success: boolean;
  user_id: number;
  lookback_days: number;
  exercise_limit: number;
  session_limit: number;
  overview: ExerciseHistoryAnalyticsOverview;
  exercises: ExerciseHistoryAnalyticsSummary[];
}
