export interface ExerciseInstructionExercise {
  id: number;
  name: string;
  exercise_type: string;
  movement_pattern: string;
  primary_muscle_groups: string[];
  equipment_required: string[];
  difficulty: string;
}

export interface ExerciseInstruction {
  catalog_exercise_id: number;
  overview: string;
  setup_steps: string[];
  execution_steps: string[];
  form_cues: string[];
  common_mistakes: string[];
  safety_notes: string[];
}

export interface ExerciseFormMediaAsset {
  catalog_exercise_id: number;
  media_key: string;
  media_type: "static_image";
  asset_path: string;
  alt_text: string;
  caption: string | null;
  sort_order: number;
  source_name: string;
  source_exercise_id: string;
  source_url: string;
  license_name: string;
  license_url: string;
  asset_sha256: string;
}

export type ExerciseVisualMediaType = "static_image" | "animated_image";
export type ExerciseVisualMediaResolutionMode =
  | "direct_local"
  | "shared_local_visual_identity"
  | "provider"
  | "none";
export type ExerciseVisualMediaSourceType =
  | "local"
  | "remote_provider"
  | "none";

export interface ExerciseVisualMediaItem {
  media_key: string;
  media_type: ExerciseVisualMediaType;
  role: string;
  url: string;
  alt_text: string;
  caption: string | null;
  source_type: ExerciseVisualMediaSourceType;
  source_catalog_exercise_id: number | null;
  provider: string | null;
  provider_exercise_id: string | null;
  attribution: string | null;
  provenance: string;
}

export interface ExerciseVisualMediaResolution {
  requested_catalog_exercise_id: number;
  visual_identity_slug: string | null;
  resolution_mode: ExerciseVisualMediaResolutionMode;
  source_type: ExerciseVisualMediaSourceType;
  source_catalog_exercise_id: number | null;
  provider: string | null;
  provider_exercise_id: string | null;
}

export interface ExerciseInstructionResponse {
  success: boolean;
  exercise: ExerciseInstructionExercise;
  instruction: ExerciseInstruction;
  form_media: ExerciseFormMediaAsset[];
  visual_media: ExerciseVisualMediaItem[];
  visual_media_resolution: ExerciseVisualMediaResolution;
}
