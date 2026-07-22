import {
  GenerateMealIdeasInput,
  GroundedMealIdea,
  MealIdeaGenerationHistoryResponse,
  MealIdeaModelOptionsResponse,
  MealIdeaProvider,
  MealIdeasResponse,
  MealInstructionsResponse,
} from "@/types/mealIdea";

export async function fetchMealIdeaHistory(
  userId: number,
): Promise<MealIdeaGenerationHistoryResponse> {
  const params = new URLSearchParams({ user_id: String(userId) });
  const response = await fetch(
    `/api/nutrition-meal-ideas/history?${params.toString()}`,
    { cache: "no-store", headers: { Accept: "application/json" } },
  );
  const payload = (await response.json().catch(() => null)) as
    | MealIdeaGenerationHistoryResponse
    | { detail?: string }
    | null;
  if (!response.ok) {
    throw new Error(
      payload && "detail" in payload && typeof payload.detail === "string"
        ? payload.detail
        : "Recent meal ideas are unavailable.",
    );
  }
  return payload as MealIdeaGenerationHistoryResponse;
}

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

export async function generateMealInstructions({
  userId,
  provider,
  model,
  idea,
}: {
  userId: number;
  provider: MealIdeaProvider;
  model: string;
  idea: GroundedMealIdea;
}): Promise<MealInstructionsResponse> {
  const response = await fetch("/api/nutrition-meal-instructions", {
    method: "POST",
    cache: "no-store",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_id: userId,
      provider,
      model,
      meal_name: idea.name,
      ingredients: idea.ingredients.map((ingredient) => ({
        canonical_food_id: ingredient.canonical_food_id,
        personal_food_id: null,
        display_name: ingredient.display_name,
        amount_grams: ingredient.amount_grams,
      })),
    }),
  });
  const payload = (await response.json().catch(() => null)) as
    | MealInstructionsResponse
    | { detail?: string | { message?: string } }
    | null;
  if (!response.ok) {
    const detail = payload && "detail" in payload ? payload.detail : null;
    throw new Error(
      typeof detail === "string"
        ? detail
        : typeof detail?.message === "string"
          ? detail.message
          : "Cooking instructions could not be generated.",
    );
  }
  return payload as MealInstructionsResponse;
}
