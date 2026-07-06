export type DailyDriverReadinessStatus =
  | "ready"
  | "light"
  | "recover"
  | "unknown";

export type DailyDriverWorkoutStatus =
  | "not_started"
  | "in_progress"
  | "completed"
  | "not_planned"
  | "unknown";

export type DailyDriverNutritionStatus =
  | "on_track"
  | "behind"
  | "complete"
  | "not_logged"
  | "unknown";

export type DailyDriverNextActionType =
  | "start_workout"
  | "continue_workout"
  | "log_workout"
  | "log_meal"
  | "review_recovery"
  | "review_today"
  | "done"
  | "unknown";

export type DailyDriverConfidence = "high" | "medium" | "low" | "unknown";

export interface DailyDriverReadinessSummary {
  status: DailyDriverReadinessStatus;
  headline: string;
  reason: string;
  confidence: DailyDriverConfidence;
  score: number | null;
}

export interface DailyDriverWorkoutSummary {
  planned: boolean;
  workout_id: string | null;
  title: string;
  summary: string;
  status: DailyDriverWorkoutStatus;
  first_action_label: string;
}

export interface DailyDriverNutritionSummary {
  status: DailyDriverNutritionStatus;
  calorie_target: number | null;
  protein_target_g: number | null;
  carbohydrate_target_g: number | null;
  fat_target_g: number | null;
  calories_logged: number | null;
  protein_logged_g: number | null;
  carbs_logged_g: number | null;
  fat_logged_g: number | null;
  today_mission: string;
}

export interface DailyDriverNextAction {
  type: DailyDriverNextActionType;
  label: string;
  context: string;
}

export interface DailyDriverCoachNote {
  enabled: boolean;
  text: string | null;
}

export interface DailyDriverTodayResponse {
  contract_version: string;
  user_id: number;
  target_date: string;
  readiness: DailyDriverReadinessSummary;
  workout: DailyDriverWorkoutSummary;
  nutrition: DailyDriverNutritionSummary;
  next_action: DailyDriverNextAction;
  coach_note: DailyDriverCoachNote;
  data_gaps: string[];
  limitations: string[];
}
