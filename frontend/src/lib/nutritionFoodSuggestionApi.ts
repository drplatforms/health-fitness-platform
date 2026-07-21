import { getApiBaseUrl } from "@/lib/dailyDriverApi";
import { NutritionFoodSuggestionsResponse } from "@/types/nutritionFoodSuggestion";

export interface NutritionFoodSuggestionsApiResult {
  data: NutritionFoodSuggestionsResponse | null;
  error: string | null;
}

export async function fetchNutritionFoodSuggestionsFromBackend({
  userId,
  date,
}: {
  userId: number;
  date: string;
}): Promise<NutritionFoodSuggestionsApiResult> {
  const backendParams = new URLSearchParams({ date, limit: "8" });
  const clientParams = new URLSearchParams({
    user_id: String(userId),
    date,
    limit: "8",
  });
  const endpoint =
    typeof window === "undefined"
      ? `${getApiBaseUrl()}/nutrition/${userId}/food-suggestions?${backendParams.toString()}`
      : `/api/nutrition-food-suggestions?${clientParams.toString()}`;

  try {
    const response = await fetch(endpoint, {
      cache: "no-store",
      headers: {
        Accept: "application/json",
      },
    });

    if (!response.ok) {
      return {
        data: null,
        error: "Nutrition gap actions are unavailable right now.",
      };
    }

    return {
      data: (await response.json()) as NutritionFoodSuggestionsResponse,
      error: null,
    };
  } catch {
    return {
      data: null,
      error: "Nutrition gap actions are unavailable right now.",
    };
  }
}
