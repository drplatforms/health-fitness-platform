import {
  RecoveryCheckInResponse,
  SaveRecoveryCheckInPayload,
  SaveRecoveryCheckInResponse,
} from "@/types/recoveryCheckin";

function readDetail(payload: unknown): string | null {
  if (
    typeof payload === "object" &&
    payload !== null &&
    "detail" in payload &&
    typeof payload.detail === "string"
  ) {
    return payload.detail;
  }
  return null;
}

function buildRecoveryCheckInQuery(userId: number, targetDate?: string): string {
  const params = new URLSearchParams({ user_id: String(userId) });
  if (targetDate) {
    params.set("date", targetDate);
  }
  return params.toString();
}

export async function fetchRecoveryCheckIn(
  userId: number,
  targetDate?: string,
  signal?: AbortSignal,
): Promise<RecoveryCheckInResponse> {
  const response = await fetch(
    `/api/recovery-checkin?${buildRecoveryCheckInQuery(userId, targetDate)}`,
    {
      cache: "no-store",
      signal,
      headers: {
        Accept: "application/json",
      },
    },
  );

  const payload = (await response.json().catch(() => null)) as
    | RecoveryCheckInResponse
    | { detail?: string }
    | null;

  if (!response.ok) {
    throw new Error(
      readDetail(payload) ?? "Unable to load today's recovery check-in.",
    );
  }

  return payload as RecoveryCheckInResponse;
}

export async function saveRecoveryCheckIn(
  payload: SaveRecoveryCheckInPayload,
  signal?: AbortSignal,
): Promise<SaveRecoveryCheckInResponse> {
  const response = await fetch("/api/recovery-checkin", {
    method: "POST",
    signal,
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  const responsePayload = (await response.json().catch(() => null)) as
    | SaveRecoveryCheckInResponse
    | { detail?: string }
    | null;

  if (!response.ok) {
    throw new Error(
      readDetail(responsePayload) ?? "Unable to save today's recovery check-in.",
    );
  }

  return responsePayload as SaveRecoveryCheckInResponse;
}
