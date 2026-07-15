import { ExerciseInstructionResponse } from "@/types/exerciseInstruction";

export interface ExerciseInstructionApiError {
  message: string;
  statusCode?: number;
}

export interface ExerciseInstructionApiResult {
  data: ExerciseInstructionResponse | null;
  error: ExerciseInstructionApiError | null;
}

export async function fetchExerciseInstruction(
  catalogExerciseId: number,
): Promise<ExerciseInstructionApiResult> {
  if (!Number.isSafeInteger(catalogExerciseId) || catalogExerciseId <= 0) {
    return {
      data: null,
      error: { message: "Instructions aren't available for this exercise." },
    };
  }

  try {
    const response = await fetch(
      `/api/exercise-instruction/${catalogExerciseId}`,
      {
        cache: "no-store",
        headers: {
          Accept: "application/json",
        },
      },
    );

    if (!response.ok) {
      return {
        data: null,
        error: {
          message:
            response.status === 404
              ? "Instructions aren't available for this exercise."
              : "Instructions aren't available right now.",
          statusCode: response.status,
        },
      };
    }

    return {
      data: (await response.json()) as ExerciseInstructionResponse,
      error: null,
    };
  } catch {
    return {
      data: null,
      error: { message: "Instructions aren't available right now." },
    };
  }
}
