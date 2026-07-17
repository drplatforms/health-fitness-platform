export type WeeklyWorkoutSizePreference = "quick" | "standard" | "extended";
export type WeeklyTrainingDayType = "training" | "rest";
export type WeeklyTrainingDayStatus =
  | "rest"
  | "planned"
  | "today"
  | "selected"
  | "in_progress"
  | "completed"
  | "missed"
  | "extra_workout";

export interface WeeklySessionDirective {
  session_type: string;
  session_title: string;
  session_focus: string;
  ordered_slot_families: string[];
  optional_extension_slot_families: string[];
  sequence_index: number;
}

export interface WeeklyTrainingPlanDay {
  id: number;
  weekly_training_plan_id: number;
  training_date: string;
  day_index: number;
  day_type: WeeklyTrainingDayType;
  session_sequence_index: number | null;
  session_type: string | null;
  session_title: string | null;
  session_focus: string | null;
  session_directive: WeeklySessionDirective | null;
  derived_status: WeeklyTrainingDayStatus;
  is_protected: boolean;
  protection_reason: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface WeeklyTrainingPlan {
  id: number;
  user_id: number;
  week_start_date: string;
  week_end_date: string;
  target_session_count: number;
  default_workout_size_preference: WeeklyWorkoutSizePreference;
  status: "active" | "completed";
  days: WeeklyTrainingPlanDay[];
  created_at: string | null;
  updated_at: string | null;
}

export interface WeeklyTrainingPlanResponse {
  success: boolean;
  user_id: number;
  week_start_date?: string;
  plan: WeeklyTrainingPlan | null;
}
