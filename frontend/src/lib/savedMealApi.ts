import {
  SavedMealLogResponse,
  SavedMealMutation,
  SavedMealResponse,
  SavedMealsResponse,
} from "@/types/savedMeal";

async function requireJson<T>(response: Response, fallback: string): Promise<T> {
  const payload = (await response.json().catch(() => null)) as
    | { detail?: unknown }
    | null;
  if (!response.ok) {
    throw new Error(typeof payload?.detail === "string" ? payload.detail : fallback);
  }
  return payload as T;
}

export async function fetchSavedMeals({
  userId,
  includeArchived = false,
}: {
  userId: number;
  includeArchived?: boolean;
}): Promise<SavedMealsResponse> {
  const params = new URLSearchParams({
    user_id: String(userId),
    include_archived: String(includeArchived),
  });
  const response = await fetch(`/api/nutrition-saved-meals?${params.toString()}`, {
    cache: "no-store",
    headers: { Accept: "application/json" },
  });
  return requireJson(response, "Unable to load saved meals.");
}

export async function createSavedMeal(
  payload: SavedMealMutation,
): Promise<SavedMealResponse> {
  const response = await fetch("/api/nutrition-saved-meals", {
    method: "POST",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return requireJson(response, "Unable to save this meal.");
}

export async function updateSavedMeal(
  savedMealId: number,
  payload: SavedMealMutation,
): Promise<SavedMealResponse> {
  const response = await fetch(`/api/nutrition-saved-meals/${savedMealId}`, {
    method: "PATCH",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return requireJson(response, "Unable to update this meal.");
}

export async function archiveSavedMeal(
  userId: number,
  savedMealId: number,
): Promise<SavedMealResponse> {
  return savedMealAction(userId, savedMealId, "archive");
}

export async function restoreSavedMeal(
  userId: number,
  savedMealId: number,
): Promise<SavedMealResponse> {
  return savedMealAction(userId, savedMealId, "restore");
}

async function savedMealAction(
  userId: number,
  savedMealId: number,
  action: "archive" | "restore",
) {
  const response = await fetch(
    `/api/nutrition-saved-meals/${savedMealId}/${action}`,
    {
      method: "POST",
      headers: { Accept: "application/json", "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId }),
    },
  );
  return requireJson<SavedMealResponse>(response, `Unable to ${action} this meal.`);
}

export async function logSavedMeal({
  userId,
  savedMealId,
  entryDate,
  mealType,
}: {
  userId: number;
  savedMealId: number;
  entryDate: string;
  mealType?: string;
}): Promise<SavedMealLogResponse> {
  const response = await fetch(`/api/nutrition-saved-meals/${savedMealId}/log`, {
    method: "POST",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: JSON.stringify({
      user_id: userId,
      entry_date: entryDate,
      meal_type: mealType,
    }),
  });
  return requireJson(response, "Unable to log this saved meal.");
}
