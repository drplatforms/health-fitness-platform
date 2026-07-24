import type { DailyDriverApiError } from "@/lib/dailyDriverApi";
import type {
  ExerciseHistoryAnalyticsSummary,
  ExerciseHistoryRecentSession,
  ExercisePerformanceMetric,
  ExercisePerformanceMetricType,
  ExercisePerformancePhaseSegment,
  RecentWorkingLoadTrend,
  WorkoutExerciseHistoryAnalyticsResponse,
  WorkoutExerciseHistorySessionDetailResponse,
} from "@/types/workoutExerciseHistory";

interface RouteErrorPayload {
  detail?: string;
}

export interface WorkoutExerciseHistoryAnalyticsApiResult {
  data: WorkoutExerciseHistoryAnalyticsResponse | null;
  error: DailyDriverApiError | null;
}

export interface WorkoutExerciseHistorySessionDetailApiResult {
  data: WorkoutExerciseHistorySessionDetailResponse | null;
  error: DailyDriverApiError | null;
}

export interface WorkoutExerciseHistoryAnalyticsOptions {
  lookbackDays?: number;
  exerciseLimit?: number;
  sessionLimit?: number;
  includeSetDetails?: boolean;
}

export const PERFORMANCE_STUDIO_RANGES = [
  { days: 28, label: "4 weeks" },
  { days: 84, label: "12 weeks" },
  { days: 183, label: "6 months" },
  { days: 365, label: "1 year" },
] as const;

export type PerformanceStudioRangeDays =
  (typeof PERFORMANCE_STUDIO_RANGES)[number]["days"];

export function buildWorkoutHistoryHref(userId: number): string {
  return `/workout/history?user_id=${userId}`;
}

export function exerciseAnalyticsKey(
  exercise: Pick<
    ExerciseHistoryAnalyticsSummary,
    "catalog_exercise_id" | "exercise_name"
  >,
): string {
  return exercise.catalog_exercise_id !== null
    ? `catalog:${exercise.catalog_exercise_id}`
    : `name:${exercise.exercise_name.trim().toLowerCase().replace(/\s+/g, " ")}`;
}

export function resolveExerciseSelectionKey(
  exercises: ExerciseHistoryAnalyticsSummary[],
  preferredKey: string,
): string {
  if (
    preferredKey &&
    exercises.some(
      (exercise) => exerciseAnalyticsKey(exercise) === preferredKey,
    )
  ) {
    return preferredKey;
  }
  return exercises[0] ? exerciseAnalyticsKey(exercises[0]) : "";
}

export function performanceStudioEmptyMessage(
  hasHistory: boolean,
  rangeDays: PerformanceStudioRangeDays,
): string {
  if (!hasHistory && rangeDays === 365) {
    return "Complete and log a workout to build your performance history.";
  }
  const label =
    PERFORMANCE_STUDIO_RANGES.find((range) => range.days === rangeDays)?.label ??
    `${rangeDays} days`;
  return `No completed exercise sessions were found in the last ${label}. Try a longer range.`;
}

export function formatPerformanceMetric(
  metric: ExercisePerformanceMetric,
): string {
  if (metric.unit === "seconds") {
    return formatDuration(metric.value);
  }
  if (metric.unit === "meters") {
    if (metric.value >= 1000) {
      return `${formatNumber(metric.value / 1000)} km`;
    }
    return `${formatNumber(metric.value)} m`;
  }
  return `${formatNumber(metric.value)} ${metric.unit}`;
}

export function timelineDatePosition(
  value: string,
  startDate: string,
  endDate: string,
): number {
  const start = Date.parse(`${startDate}T00:00:00Z`);
  const end = Date.parse(`${endDate}T00:00:00Z`);
  const current = Date.parse(`${value}T00:00:00Z`);
  if (![start, end, current].every(Number.isFinite) || end <= start) {
    return 0.5;
  }
  return Math.min(1, Math.max(0, (current - start) / (end - start)));
}

export function nearestSessionIndex(
  positions: readonly number[],
  targetPosition: number,
  startIndex = 0,
  endIndex = positions.length,
): number {
  const start = Math.min(
    positions.length,
    Math.max(0, Math.floor(startIndex)),
  );
  const end = Math.min(
    positions.length,
    Math.max(start, Math.ceil(endIndex)),
  );
  if (end <= start) {
    return -1;
  }
  const target = Math.min(1, Math.max(0, targetPosition));
  let low = start;
  let high = end - 1;
  while (low < high) {
    const middle = Math.floor((low + high) / 2);
    if (positions[middle] < target) {
      low = middle + 1;
    } else {
      high = middle;
    }
  }
  if (low === start) {
    return start;
  }
  const left = low - 1;
  return target - positions[left] < positions[low] - target ? left : low;
}

export function moveSessionIndex(
  currentIndex: number,
  sessionCount: number,
  direction: -1 | 1,
): number {
  if (sessionCount <= 0) {
    return -1;
  }
  const current = Math.min(
    sessionCount - 1,
    Math.max(0, currentIndex < 0 ? sessionCount - 1 : currentIndex),
  );
  return Math.min(sessionCount - 1, Math.max(0, current + direction));
}

export function buildCalendarTicks(
  startDate: string,
  endDate: string,
  tickCount = 5,
): string[] {
  const start = Date.parse(`${startDate}T00:00:00Z`);
  const end = Date.parse(`${endDate}T00:00:00Z`);
  if (!Number.isFinite(start) || !Number.isFinite(end) || end <= start) {
    return [startDate];
  }
  const count = Math.min(7, Math.max(2, Math.round(tickCount)));
  const ticks = new Set<string>();
  for (let index = 0; index < count; index += 1) {
    const value = start + ((end - start) * index) / (count - 1);
    ticks.add(new Date(value).toISOString().slice(0, 10));
  }
  return [...ticks];
}

export interface PerformanceMetricScale {
  minimum: number;
  maximum: number;
  ticks: number[];
}

export function buildPerformanceMetricScale(
  values: readonly number[],
): PerformanceMetricScale | null {
  const finiteValues = values.filter(Number.isFinite);
  if (finiteValues.length === 0) {
    return null;
  }
  const highest = Math.max(0, ...finiteValues);
  if (highest === 0) {
    return {
      minimum: 0,
      maximum: 1,
      ticks: [0, 0.5, 1],
    };
  }

  const step = niceMetricStep(highest / 4);
  const stepCount = Math.max(2, Math.ceil(highest / step));
  const maximum = roundMetricValue(stepCount * step);
  return {
    minimum: 0,
    maximum,
    ticks: Array.from({ length: stepCount + 1 }, (_, index) =>
      roundMetricValue(index * step),
    ),
  };
}

export function performanceMetricPosition(
  value: number,
  scale: PerformanceMetricScale,
): number {
  if (
    !Number.isFinite(value) ||
    !Number.isFinite(scale.minimum) ||
    !Number.isFinite(scale.maximum) ||
    scale.maximum <= scale.minimum
  ) {
    return 0.5;
  }
  return Math.min(
    1,
    Math.max(0, (value - scale.minimum) / (scale.maximum - scale.minimum)),
  );
}

export function splitMetricRuns(
  sessions: ReadonlyArray<
    Pick<ExerciseHistoryRecentSession, "session_key" | "performance_metric">
  >,
  metricType: ExercisePerformanceMetricType,
): string[][] {
  const runs: string[][] = [];
  let current: string[] = [];
  for (const session of sessions) {
    const metric = session.performance_metric;
    if (
      metric === null ||
      metric.metric_type !== metricType ||
      !Number.isFinite(metric.value)
    ) {
      if (current.length > 0) {
        runs.push(current);
        current = [];
      }
      continue;
    }
    current.push(session.session_key);
  }
  if (current.length > 0) {
    runs.push(current);
  }
  return runs;
}

export function buildEffortSegments(
  sessions: ReadonlyArray<
    Pick<ExerciseHistoryRecentSession, "session_key" | "average_actual_rir">
  >,
): string[][] {
  const segments: string[][] = [];
  let current: string[] = [];
  for (const session of sessions) {
    if (
      session.average_actual_rir === null ||
      !Number.isFinite(session.average_actual_rir)
    ) {
      if (current.length > 0) {
        segments.push(current);
        current = [];
      }
      continue;
    }
    current.push(session.session_key);
  }
  if (current.length > 0) {
    segments.push(current);
  }
  return segments;
}

export function sustainedPhaseBand(
  phase: ExercisePerformancePhaseSegment,
): boolean {
  const start = Date.parse(`${phase.start_date}T00:00:00Z`);
  const end = Date.parse(`${phase.end_date}T00:00:00Z`);
  return (
    phase.evidence_session_count >= 2 &&
    phase.start_session_key !== phase.end_session_key &&
    Number.isFinite(start) &&
    Number.isFinite(end) &&
    end > start
  );
}

export function phaseBandCanShowLabel(
  phase: ExercisePerformancePhaseSegment,
  rangeStartDate: string,
  rangeEndDate: string,
  plotWidth = 900,
): boolean {
  if (!sustainedPhaseBand(phase)) {
    return false;
  }
  const start = timelineDatePosition(
    phase.start_date,
    rangeStartDate,
    rangeEndDate,
  );
  const end = timelineDatePosition(
    phase.end_date,
    rangeStartDate,
    rangeEndDate,
  );
  const availableWidth = (end - start) * Math.max(0, plotWidth);
  const estimatedLabelWidth = phase.label.length * 7.5 + 24;
  return availableWidth >= Math.max(110, estimatedLabelWidth);
}

export function describeWorkingLoadTrend(
  trend: RecentWorkingLoadTrend,
): string | null {
  if (trend.status === "insufficient_data") {
    return null;
  }
  if (trend.status === "steady") {
    return "Recent load: steady";
  }
  if (trend.absolute_change_lb === null) {
    return null;
  }
  const direction = trend.status === "higher_recently" ? "higher" : "lower";
  return `Recent load: ${formatNumber(trend.absolute_change_lb)} lb ${direction}`;
}

export async function fetchWorkoutExerciseHistoryAnalytics(
  userId: number,
  options: WorkoutExerciseHistoryAnalyticsOptions = {},
): Promise<WorkoutExerciseHistoryAnalyticsApiResult> {
  const params = new URLSearchParams({ user_id: String(userId) });
  if (options.lookbackDays !== undefined) {
    params.set("lookback_days", String(options.lookbackDays));
  }
  if (options.exerciseLimit !== undefined) {
    params.set("exercise_limit", String(options.exerciseLimit));
  }
  if (options.sessionLimit !== undefined) {
    params.set("session_limit", String(options.sessionLimit));
  }
  if (options.includeSetDetails !== undefined) {
    params.set("include_set_details", String(options.includeSetDetails));
  }

  try {
    const response = await fetch(
      `/api/workout-exercise-history-analytics?${params.toString()}`,
      {
        cache: "no-store",
        headers: { Accept: "application/json" },
      },
    );
    const payload = (await response.json().catch(() => null)) as
      | WorkoutExerciseHistoryAnalyticsResponse
      | RouteErrorPayload
      | null;
    if (!response.ok) {
      return {
        data: null,
        error: {
          heading: "Unable to load training history",
          message:
            (payload && "detail" in payload ? payload.detail : null) ??
            "The backend could not return exercise history right now.",
          statusCode: response.status,
        },
      };
    }
    return {
      data: payload as WorkoutExerciseHistoryAnalyticsResponse,
      error: null,
    };
  } catch {
    return {
      data: null,
      error: {
        heading: "Backend unavailable",
        message: "Start the FastAPI server, then refresh training history.",
      },
    };
  }
}

export async function fetchWorkoutExerciseHistorySessionDetail(
  userId: number,
  sessionKey: string,
  lookbackDays: number,
): Promise<WorkoutExerciseHistorySessionDetailApiResult> {
  const params = new URLSearchParams({
    user_id: String(userId),
    session_key: sessionKey,
    lookback_days: String(lookbackDays),
  });
  try {
    const response = await fetch(
      `/api/workout-exercise-history-analytics?${params.toString()}`,
      {
        cache: "no-store",
        headers: { Accept: "application/json" },
      },
    );
    const payload = (await response.json().catch(() => null)) as
      | WorkoutExerciseHistorySessionDetailResponse
      | RouteErrorPayload
      | null;
    if (!response.ok) {
      return {
        data: null,
        error: {
          heading: "Unable to load session details",
          message:
            (payload && "detail" in payload ? payload.detail : null) ??
            "The selected completed session could not be loaded.",
          statusCode: response.status,
        },
      };
    }
    return {
      data: payload as WorkoutExerciseHistorySessionDetailResponse,
      error: null,
    };
  } catch {
    return {
      data: null,
      error: {
        heading: "Backend unavailable",
        message: "Start the FastAPI server, then select the session again.",
      },
    };
  }
}

function formatNumber(value: number): string {
  return Number.isInteger(value) ? String(value) : value.toFixed(1);
}

function niceMetricStep(value: number): number {
  if (!Number.isFinite(value) || value <= 0) {
    return 1;
  }
  const exponent = Math.floor(Math.log10(value));
  const magnitude = 10 ** exponent;
  const fraction = value / magnitude;
  const niceFraction =
    fraction <= 1
      ? 1
      : fraction <= 2
        ? 2
        : fraction <= 2.5
          ? 2.5
          : fraction <= 5
            ? 5
            : 10;
  return niceFraction * magnitude;
}

function roundMetricValue(value: number): number {
  return Number(value.toPrecision(12));
}

function formatDuration(value: number): string {
  const totalSeconds = Math.round(value);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  if (minutes === 0) {
    return `${seconds} sec`;
  }
  return seconds === 0 ? `${minutes} min` : `${minutes}:${String(seconds).padStart(2, "0")}`;
}
