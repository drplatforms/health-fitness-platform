import {
  AvailableIngredientMutationResponse,
  AvailableIngredientStarterGroupsResponse,
  AvailableIngredientsResponse,
  CanonicalFoodLogDeleteRequest,
  CanonicalFoodLogDeleteResponse,
  CanonicalFoodLogRequest,
  CanonicalFoodLogResponse,
  CanonicalFoodLogUpdateRequest,
  CanonicalFoodLogUpdateResponse,
  CanonicalFoodLogsResponse,
  CanonicalFoodSearchResponse,
  CanonicalFoodServingUnitsResponse,
  PinnedFoodMutationResponse,
  PinnedFoodsResponse,
  PinnedFoodType,
  RecentCanonicalFoodsResponse,
} from "@/types/canonicalFood";
import type {
  BarcodeApiFormat,
  BarcodeResolveResponse,
} from "@/lib/barcodeFood";

async function readErrorMessage(response: Response, fallbackMessage: string) {
  const payload = (await response.json().catch(() => null)) as
    | { detail?: unknown }
    | null;

  return typeof payload?.detail === "string" ? payload.detail : fallbackMessage;
}

export async function fetchAvailableIngredientStarterGroups(): Promise<AvailableIngredientStarterGroupsResponse> {
  const response = await fetch(
    "/api/foods-canonical-available-ingredient-starters",
    {
      cache: "no-store",
      headers: { Accept: "application/json" },
    },
  );

  if (!response.ok) {
    throw new Error(
      await readErrorMessage(
        response,
        "Unable to load quick-start ingredients right now.",
      ),
    );
  }
  return (await response.json()) as AvailableIngredientStarterGroupsResponse;
}

export async function fetchAvailableIngredients(
  userId: number,
): Promise<AvailableIngredientsResponse> {
  const params = new URLSearchParams({ user_id: String(userId) });
  const response = await fetch(
    `/api/nutrition-available-ingredients?${params.toString()}`,
    {
      cache: "no-store",
      headers: { Accept: "application/json" },
    },
  );

  if (!response.ok) {
    throw new Error(
      await readErrorMessage(
        response,
        "Unable to load available ingredients right now.",
      ),
    );
  }
  return (await response.json()) as AvailableIngredientsResponse;
}

export async function setIngredientAvailable({
  userId,
  canonicalFoodId,
  available,
}: {
  userId: number;
  canonicalFoodId: number;
  available: boolean;
}): Promise<AvailableIngredientMutationResponse> {
  const params = new URLSearchParams({
    user_id: String(userId),
    canonical_food_id: String(canonicalFoodId),
  });
  const response = await fetch(
    `/api/nutrition-available-ingredients?${params.toString()}`,
    {
      method: available ? "PUT" : "DELETE",
      headers: { Accept: "application/json" },
    },
  );

  if (!response.ok) {
    throw new Error(
      await readErrorMessage(
        response,
        "Unable to update available ingredients.",
      ),
    );
  }
  return (await response.json()) as AvailableIngredientMutationResponse;
}

export async function fetchPinnedFoods(
  userId: number,
): Promise<PinnedFoodsResponse> {
  const params = new URLSearchParams({ user_id: String(userId) });
  const response = await fetch(`/api/nutrition-pinned-foods?${params.toString()}`, {
    cache: "no-store",
    headers: { Accept: "application/json" },
  });

  if (!response.ok) {
    throw new Error(
      await readErrorMessage(response, "Unable to load pinned foods right now."),
    );
  }
  return (await response.json()) as PinnedFoodsResponse;
}

export async function setFoodPinned({
  userId,
  foodType,
  foodId,
  pinned,
}: {
  userId: number;
  foodType: PinnedFoodType;
  foodId: number;
  pinned: boolean;
}): Promise<PinnedFoodMutationResponse> {
  const params = new URLSearchParams({
    user_id: String(userId),
    food_type: foodType,
    food_id: String(foodId),
  });
  const response = await fetch(`/api/nutrition-pinned-foods?${params.toString()}`, {
    method: pinned ? "PUT" : "DELETE",
    headers: { Accept: "application/json" },
  });

  if (!response.ok) {
    throw new Error(
      await readErrorMessage(response, "Unable to update this pinned food."),
    );
  }
  return (await response.json()) as PinnedFoodMutationResponse;
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

export async function resolveFoodBarcode(
  barcode: string,
  barcodeFormat?: BarcodeApiFormat | null,
): Promise<BarcodeResolveResponse> {
  const response = await fetch("/api/foods-barcode-resolve", {
    method: "POST",
    cache: "no-store",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: JSON.stringify({ barcode, barcode_format: barcodeFormat || null }),
  });
  if (!response.ok) {
    throw new Error(
      await readErrorMessage(response, "Unable to look up this barcode right now."),
    );
  }
  return (await response.json()) as BarcodeResolveResponse;
}

export async function materializeFoodBarcode(
  rawFoodSourceRecordId: number,
  normalizedGtin: string,
): Promise<BarcodeResolveResponse> {
  const response = await fetch("/api/foods-barcode-materialize", {
    method: "POST",
    cache: "no-store",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: JSON.stringify({
      raw_food_source_record_id: rawFoodSourceRecordId,
      normalized_gtin: normalizedGtin,
    }),
  });
  if (!response.ok) {
    throw new Error(
      await readErrorMessage(response, "Unable to save this barcode product."),
    );
  }
  return (await response.json()) as BarcodeResolveResponse;
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

export async function fetchCanonicalFoodServingUnits(
  canonicalFoodId: number,
): Promise<CanonicalFoodServingUnitsResponse> {
  const response = await fetch(
    `/api/foods-canonical-serving-units/${canonicalFoodId}`,
    {
      cache: "no-store",
      headers: {
        Accept: "application/json",
      },
    },
  );

  if (!response.ok) {
    throw new Error(
      await readErrorMessage(
        response,
        "Unable to load serving units for this food.",
      ),
    );
  }

  return (await response.json()) as CanonicalFoodServingUnitsResponse;
}

export async function fetchRecentCanonicalFoods({
  userId,
  limit = 10,
}: {
  userId: number;
  limit?: number;
}): Promise<RecentCanonicalFoodsResponse> {
  const params = new URLSearchParams({
    user_id: String(userId),
    limit: String(limit),
  });
  const response = await fetch(
    `/api/nutrition-recent-canonical-foods?${params.toString()}`,
    {
      cache: "no-store",
      headers: {
        Accept: "application/json",
      },
    },
  );

  if (!response.ok) {
    throw new Error(
      await readErrorMessage(response, "Unable to load recent foods right now."),
    );
  }

  return (await response.json()) as RecentCanonicalFoodsResponse;
}

export async function fetchCanonicalFoodLogs({
  userId,
  date,
}: {
  userId: number;
  date: string;
}): Promise<CanonicalFoodLogsResponse> {
  const params = new URLSearchParams({
    user_id: String(userId),
    date,
  });
  const response = await fetch(`/api/nutrition-canonical-logs?${params.toString()}`, {
    cache: "no-store",
    headers: {
      Accept: "application/json",
    },
  });

  if (!response.ok) {
    throw new Error(
      await readErrorMessage(response, "Unable to load logged foods right now."),
    );
  }

  return (await response.json()) as CanonicalFoodLogsResponse;
}

export async function updateCanonicalFoodLog(
  payload: CanonicalFoodLogUpdateRequest,
): Promise<CanonicalFoodLogUpdateResponse> {
  const response = await fetch(
    `/api/nutrition-canonical-logs/${payload.entry_id}`,
    {
      method: "PATCH",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        user_id: payload.user_id,
        grams: payload.grams,
        serving_unit_id: payload.serving_unit_id,
        quantity: payload.quantity,
        meal_type: payload.meal_type,
        entry_date: payload.entry_date,
      }),
    },
  );

  if (!response.ok) {
    throw new Error(
      await readErrorMessage(response, "Unable to update this food right now."),
    );
  }

  return (await response.json()) as CanonicalFoodLogUpdateResponse;
}

export async function deleteCanonicalFoodLog(
  payload: CanonicalFoodLogDeleteRequest,
): Promise<CanonicalFoodLogDeleteResponse> {
  const params = new URLSearchParams({
    user_id: String(payload.user_id),
    date: payload.entry_date,
  });
  const response = await fetch(
    `/api/nutrition-canonical-logs/${payload.entry_id}?${params.toString()}`,
    {
      method: "DELETE",
      headers: {
        Accept: "application/json",
      },
    },
  );

  if (!response.ok) {
    throw new Error(
      await readErrorMessage(response, "Unable to delete this food right now."),
    );
  }

  return (await response.json()) as CanonicalFoodLogDeleteResponse;
}
