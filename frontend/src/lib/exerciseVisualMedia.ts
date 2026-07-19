import type { ExerciseInstructionResponse } from "@/types/exerciseInstruction";

export function selectCurrentExerciseInstructionResponse(
  response: ExerciseInstructionResponse | null,
  requestedCatalogExerciseId: number,
): ExerciseInstructionResponse | null {
  if (
    response === null ||
    response.exercise.id !== requestedCatalogExerciseId ||
    response.instruction.catalog_exercise_id !== requestedCatalogExerciseId ||
    response.visual_media_resolution.requested_catalog_exercise_id !==
      requestedCatalogExerciseId
  ) {
    return null;
  }

  return response;
}
