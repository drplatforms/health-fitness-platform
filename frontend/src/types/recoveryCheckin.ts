export interface RecoveryCheckInRecord {
  id: number;
  user_id: number;
  checkin_date: string;
  body_weight: number | null;
  sleep_hours: number | null;
  energy_level: number | null;
  soreness_level: number | null;
  mood: string | null;
  notes: string | null;
  created_at: string | null;
}

export interface RecoveryCheckInResponse {
  success: boolean;
  checkin: RecoveryCheckInRecord | null;
}

export interface SaveRecoveryCheckInPayload {
  user_id: number;
  target_date?: string;
  body_weight?: number | null;
  sleep_hours: number;
  energy_level: number;
  soreness_level: number;
  mood?: string | null;
  notes?: string | null;
}

export interface SaveRecoveryCheckInResponse {
  success: boolean;
  message: string;
  checkin_id: number;
}
