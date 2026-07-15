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

export interface ExerciseInstructionResponse {
  success: boolean;
  exercise: ExerciseInstructionExercise;
  instruction: ExerciseInstruction;
}
