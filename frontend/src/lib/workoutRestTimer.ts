export const WORKOUT_REST_FALLBACK_SECONDS = 90;
export const WORKOUT_REST_EXTENSION_SECONDS = 30;

export function resolveWorkoutRestSeconds(
  prescribedRestSeconds?: number | null,
): number {
  if (
    prescribedRestSeconds !== null &&
    prescribedRestSeconds !== undefined &&
    Number.isFinite(prescribedRestSeconds) &&
    prescribedRestSeconds > 0
  ) {
    return Math.round(prescribedRestSeconds);
  }

  return WORKOUT_REST_FALLBACK_SECONDS;
}

export function startWorkoutRestTimer(
  nowMs: number,
  prescribedRestSeconds?: number | null,
): number {
  return nowMs + resolveWorkoutRestSeconds(prescribedRestSeconds) * 1_000;
}

export function extendWorkoutRestTimer(
  currentEndAtMs: number,
  nowMs: number,
  extensionSeconds = WORKOUT_REST_EXTENSION_SECONDS,
): number {
  return Math.max(currentEndAtMs, nowMs) + extensionSeconds * 1_000;
}

export function remainingWorkoutRestSeconds(
  endAtMs: number,
  nowMs: number,
): number {
  return Math.max(0, Math.ceil((endAtMs - nowMs) / 1_000));
}

export function formatWorkoutRestCountdown(remainingSeconds: number): string {
  const minutes = Math.floor(remainingSeconds / 60);
  const seconds = remainingSeconds % 60;

  return `${minutes}:${String(seconds).padStart(2, "0")}`;
}
