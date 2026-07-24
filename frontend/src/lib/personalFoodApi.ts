import {
  PersonalFoodLogDeleteResponse,
  PersonalFoodLogRequest,
  PersonalFoodLogResponse,
  PersonalFoodLogsResponse,
  PersonalFoodLogUpdateRequest,
  PersonalFoodLogUpdateResponse,
  PersonalFoodResponse,
  PersonalFoodsResponse,
  PersonalFoodUpsertRequest,
} from "@/types/personalFood";

async function readErrorMessage(response: Response, fallbackMessage: string) {
  const payload = (await response.json().catch(() => null)) as
    | { detail?: unknown }
    | null;
  return typeof payload?.detail === "string" ? payload.detail : fallbackMessage;
}

async function requireJson<T>(response: Response, fallbackMessage: string) {
  if (!response.ok) {
    throw new Error(await readErrorMessage(response, fallbackMessage));
  }
  return (await response.json()) as T;
}

export async function fetchPersonalFoods({
  userId,
  query = "",
  includeArchived = false,
  limit = 50,
}: {
  userId: number;
  query?: string;
  includeArchived?: boolean;
  limit?: number;
}): Promise<PersonalFoodsResponse> {
  const params = new URLSearchParams({
    user_id: String(userId),
    include_archived: String(includeArchived),
    limit: String(limit),
  });
  const trimmedQuery = query.trim();
  if (trimmedQuery) {
    params.set("q", trimmedQuery);
  }
  const response = await fetch(`/api/personal-foods?${params.toString()}`, {
    cache: "no-store",
    headers: { Accept: "application/json" },
  });
  return requireJson(response, "Unable to load personal foods right now.");
}

export async function searchPersonalFoods(
  userId: number,
  query: string,
  limit = 8,
): Promise<PersonalFoodsResponse> {
  const trimmedQuery = query.trim();
  if (trimmedQuery.length < 2) {
    return { success: true, user_id: userId, results: [] };
  }
  return fetchPersonalFoods({ userId, query: trimmedQuery, limit });
}

export async function fetchPersonalFood(
  userId: number,
  personalFoodId: number,
  signal?: AbortSignal,
): Promise<PersonalFoodResponse> {
  const params = new URLSearchParams({ user_id: String(userId) });
  const response = await fetch(
    `/api/personal-foods/${personalFoodId}?${params.toString()}`,
    { cache: "no-store", signal, headers: { Accept: "application/json" } },
  );
  return requireJson(response, "Unable to load this personal food.");
}

export async function createPersonalFood(
  payload: PersonalFoodUpsertRequest,
  signal?: AbortSignal,
): Promise<PersonalFoodResponse> {
  const response = await fetch("/api/personal-foods", {
    method: "POST",
    signal,
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return requireJson(response, "Unable to save this personal food.");
}

export async function updatePersonalFood(
  personalFoodId: number,
  payload: PersonalFoodUpsertRequest,
  signal?: AbortSignal,
): Promise<PersonalFoodResponse> {
  const response = await fetch(`/api/personal-foods/${personalFoodId}`, {
    method: "PATCH",
    signal,
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return requireJson(response, "Unable to update this personal food.");
}

export async function archivePersonalFood(
  userId: number,
  personalFoodId: number,
): Promise<PersonalFoodResponse> {
  const params = new URLSearchParams({ user_id: String(userId) });
  const response = await fetch(
    `/api/personal-foods/${personalFoodId}?${params.toString()}`,
    { method: "DELETE", headers: { Accept: "application/json" } },
  );
  return requireJson(response, "Unable to archive this personal food.");
}

export async function restorePersonalFood(
  userId: number,
  personalFoodId: number,
): Promise<PersonalFoodResponse> {
  const response = await fetch(`/api/personal-foods/${personalFoodId}/restore`, {
    method: "POST",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId }),
  });
  return requireJson(response, "Unable to restore this personal food.");
}

export async function logPersonalFood(
  payload: PersonalFoodLogRequest,
): Promise<PersonalFoodLogResponse> {
  const response = await fetch("/api/nutrition-log-personal", {
    method: "POST",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return requireJson(response, "Unable to log this personal food.");
}

export async function fetchPersonalFoodLogs({
  userId,
  date,
}: {
  userId: number;
  date: string;
}): Promise<PersonalFoodLogsResponse> {
  const params = new URLSearchParams({ user_id: String(userId), date });
  const response = await fetch(
    `/api/nutrition-personal-logs?${params.toString()}`,
    { cache: "no-store", headers: { Accept: "application/json" } },
  );
  return requireJson(response, "Unable to load personal food logs.");
}

export async function updatePersonalFoodLog(
  payload: PersonalFoodLogUpdateRequest,
): Promise<PersonalFoodLogUpdateResponse> {
  const response = await fetch(
    `/api/nutrition-personal-logs/${payload.entry_id}`,
    {
      method: "PATCH",
      headers: { Accept: "application/json", "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: payload.user_id,
        entry_date: payload.entry_date,
        grams: payload.grams,
        serving_quantity: payload.serving_quantity,
        meal_type: payload.meal_type,
      }),
    },
  );
  return requireJson(response, "Unable to update this personal food log.");
}

export async function deletePersonalFoodLog({
  userId,
  entryId,
  date,
}: {
  userId: number;
  entryId: number;
  date: string;
}): Promise<PersonalFoodLogDeleteResponse> {
  const params = new URLSearchParams({ user_id: String(userId), date });
  const response = await fetch(
    `/api/nutrition-personal-logs/${entryId}?${params.toString()}`,
    { method: "DELETE", headers: { Accept: "application/json" } },
  );
  return requireJson(response, "Unable to delete this personal food log.");
}
