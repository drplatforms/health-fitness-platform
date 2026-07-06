import {
  CanonicalFoodLogRequest,
  CanonicalFoodLogResponse,
  CanonicalFoodSearchResponse,
} from "@/types/canonicalFood";

async function readErrorMessage(response: Response, fallbackMessage: string) {
  const payload = (await response.json().catch(() => null)) as
    | { detail?: unknown }
    | null;

  return typeof payload?.detail === "string" ? payload.detail : fallbackMessage;
}

export async function searchCanonicalFoods(
  query: string,
  limit = 8,
): Promise<CanonicalFoodSearchResponse> {
  const trimmedQuery = query.trim();

  if (!trimmedQuery || trimmedQuery.length < 2) {
    return {
      success: true,
      query: trimmedQuery,
      results: [],
    };
  }

  const params = new URLSearchParams({
    q: trimmedQuery,
    limit: String(limit),
  });
  const response = await fetch(`/api/foods-canonical-search?${params.toString()}`, {
    cache: "no-store",
    headers: {
      Accept: "application/json",
    },
  });

  if (!response.ok) {
    throw new Error(
      await readErrorMessage(response, "Unable to search foods right now."),
    );
  }

  return (await response.json()) as CanonicalFoodSearchResponse;
}

export async function logCanonicalFood(
  payload: CanonicalFoodLogRequest,
): Promise<CanonicalFoodLogResponse> {
  const response = await fetch("/api/nutrition-log-canonical", {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(
      await readErrorMessage(response, "Unable to log this food right now."),
    );
  }

  return (await response.json()) as CanonicalFoodLogResponse;
}
