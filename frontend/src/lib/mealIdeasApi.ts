import {
  GenerateMealIdeasInput,
  MealIdeaModelOptionsResponse,
  MealIdeasResponse,
} from "@/types/mealIdea";

export async function fetchMealIdeaModelOptions(): Promise<MealIdeaModelOptionsResponse> {
  const response = await fetch("/api/nutrition-meal-idea-models", {
    cache: "no-store",
    headers: { Accept: "application/json" },
  });
  const payload = (await response.json().catch(() => null)) as
    | MealIdeaModelOptionsResponse
    | { detail?: string }
    | null;
  if (!response.ok) {
    throw new Error(
      payload && "detail" in payload && typeof payload.detail === "string"
        ? payload.detail
        : "Meal idea models are unavailable.",
    );
  }
  return payload as MealIdeaModelOptionsResponse;
}

export async function generateMealIdeas(
  input: GenerateMealIdeasInput,
): Promise<MealIdeasResponse> {
  const params = new URLSearchParams({
    user_id: String(input.userId),
    target_date: input.targetDate,
  });
  const response = await fetch(`/api/nutrition-meal-ideas?${params.toString()}`, {
    method: "POST",
    cache: "no-store",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      provider: input.provider,
      model: input.model,
      creative_steering: input.creativeSteering,
      meal_type: input.mealType,
      intent: input.intent.trim() || null,
      generation_nonce: input.generationNonce,
      previous_idea_names: input.previousIdeaNames,
      recent_generated_food_names: input.recentGeneratedFoodNames,
    }),
  });
  const payload = (await response.json().catch(() => null)) as
    | MealIdeasResponse
    | {
        detail?: string | { code?: string; message?: string };
      }
    | null;
  if (!response.ok) {
    const detail = payload && "detail" in payload ? payload.detail : null;
    const message =
      typeof detail === "string"
        ? detail
        : typeof detail?.message === "string"
          ? detail.message
          : "Meal ideas could not be generated. Retry or switch providers.";
    throw new Error(message);
  }
  return payload as MealIdeasResponse;
}
