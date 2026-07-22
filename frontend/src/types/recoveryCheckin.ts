export interface RecoveryCheckInRecord {
  id: number;
  user_id: number;
  checkin_date: string;
  body_weight: number | null;
  sleep_hours: number | null;
  sleep_quality: number | null;
  energy_level: number | null;
  soreness_level: number | null;
  stress_level: number | null;
  training_motivation: number | null;
  pain_concern: PainConcern | null;
  pain_area: PainArea | null;
  mood: string | null;
  notes: string | null;
  created_at: string | null;
}

export interface RecoveryCheckInResponse {
  success: boolean;
  checkin: RecoveryCheckInRecord | null;
  recent_checkins: RecoveryCheckInRecord[];
}

export type PainConcern = "none" | "mild" | "significant";

export type PainArea =
  | "neck"
  | "shoulder"
  | "elbow"
  | "wrist_hand"
  | "upper_back"
  | "lower_back"
  | "hip"
  | "knee"
  | "ankle_foot"
  | "other";

export interface SaveRecoveryCheckInPayload {
  user_id: number;
  target_date?: string;
  body_weight?: number | null;
  sleep_hours: number;
  sleep_quality?: number | null;
  energy_level: number;
  soreness_level: number;
  stress_level?: number | null;
  training_motivation?: number | null;
  pain_concern?: PainConcern | null;
  pain_area?: PainArea | null;
  mood?: string | null;
  notes?: string | null;
}

export interface SaveRecoveryCheckInResponse {
  success: boolean;
  message: string;
  checkin_id: number;
}
