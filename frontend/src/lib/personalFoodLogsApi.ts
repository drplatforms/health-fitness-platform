import { getApiBaseUrl } from "@/lib/dailyDriverApi";
import { PersonalFoodLogsResponse } from "@/types/personalFood";

export interface PersonalFoodLogsApiResult {
  data: PersonalFoodLogsResponse | null;
  error: string | null;
}

export async function fetchPersonalFoodLogsFromBackend({
  userId,
  date,
}: {
  userId: number;
  date: string;
}): Promise<PersonalFoodLogsApiResult> {
  const params = new URLSearchParams({ date });
  const endpoint = `${getApiBaseUrl()}/nutrition/${userId}/personal-logs?${params.toString()}`;
  try {
    const response = await fetch(endpoint, {
      cache: "no-store",
      headers: { Accept: "application/json" },
    });
    if (!response.ok) {
      return { data: null, error: "Personal food logs are unavailable right now." };
    }
    return {
      data: (await response.json()) as PersonalFoodLogsResponse,
      error: null,
    };
  } catch {
    return { data: null, error: "Personal food logs are unavailable right now." };
  }
}
