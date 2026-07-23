"use client";

import {
  type KeyboardEvent,
  type MouseEvent,
  type ReactNode,
  type RefObject,
  useCallback,
  useEffect,
  useId,
  useMemo,
  useRef,
  useState,
} from "react";

import { ResponsiveSidecarDialog } from "@/components/ResponsiveSidecarDialog";
import {
  buildCalendarTicks,
  buildEffortSegments,
  buildPerformanceMetricScale,
  exerciseAnalyticsKey,
  fetchWorkoutExerciseHistoryAnalytics,
  fetchWorkoutExerciseHistorySessionDetail,
  formatPerformanceMetric,
  moveSessionIndex,
  nearestSessionIndex,
  PERFORMANCE_STUDIO_RANGES,
  performanceMetricPosition,
  performanceStudioEmptyMessage,
  type PerformanceStudioRangeDays,
  phaseBandCanShowLabel,
  resolveExerciseSelectionKey,
  splitMetricRuns,
  sustainedPhaseBand,
  timelineDatePosition,
  type WorkoutExerciseHistoryAnalyticsApiResult,
  type WorkoutExerciseHistorySessionDetailApiResult,
} from "@/lib/workoutExerciseHistoryApi";
import type {
  ExerciseHistoryAnalyticsSummary,
  ExerciseHistoryRecentSession,
  ExerciseHistoryRecordedSet,
  ExercisePerformanceComparison,
  ExercisePerformanceMetric,
  ExercisePerformanceMetricType,
  ExercisePerformancePhaseSegment,
} from "@/types/workoutExerciseHistory";

const PERFORMANCE_SESSION_LIMIT = 400;
const CHART_WIDTH = 1000;
const CHART_HEIGHT = 440;
const PLOT_LEFT = 74;
const PLOT_RIGHT = 974;
const PLOT_TOP = 34;
const PLOT_BOTTOM = 300;
const EFFORT_TOP = 330;
const EFFORT_BOTTOM = 366;

type DatedSession = ExerciseHistoryRecentSession & { performed_at: string };

export function WorkoutHistoryAnalytics({ userId }: { userId: number }) {
  return <WorkoutHistoryAnalyticsForUser key={userId} userId={userId} />;
}

function WorkoutHistoryAnalyticsForUser({ userId }: { userId: number }) {
  const [result, setResult] =
    useState<WorkoutExerciseHistoryAnalyticsApiResult | null>(null);
  const [rangeDays, setRangeDays] =
    useState<PerformanceStudioRangeDays>(84);
  const [selectedExerciseKey, setSelectedExerciseKey] = useState("");
  const selectedExerciseKeyRef = useRef("");
  const [activeSessionKey, setActiveSessionKey] = useState("");
  const [openSessionKey, setOpenSessionKey] = useState<string | null>(null);
  const [sessionDetail, setSessionDetail] =
    useState<WorkoutExerciseHistorySessionDetailApiResult | null>(null);
  const graphControlRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let isCurrent = true;
    void fetchWorkoutExerciseHistoryAnalytics(userId, {
      lookbackDays: rangeDays,
      sessionLimit: PERFORMANCE_SESSION_LIMIT,
      includeSetDetails: false,
    }).then((nextResult) => {
      if (!isCurrent) {
        return;
      }
      const exercises = nextResult.data?.exercises ?? [];
      const nextExerciseKey = resolveExerciseSelectionKey(
        exercises,
        selectedExerciseKeyRef.current,
      );
      const nextExercise = exercises.find(
        (exercise) => exerciseAnalyticsKey(exercise) === nextExerciseKey,
      );
      setResult(nextResult);
      selectedExerciseKeyRef.current = nextExerciseKey;
      setSelectedExerciseKey(nextExerciseKey);
      setActiveSessionKey(
        latestDatedSession(nextExercise?.recent_sessions ?? [])?.session_key ??
          "",
      );
      setOpenSessionKey(null);
      setSessionDetail(null);
    });
    return () => {
      isCurrent = false;
    };
  }, [rangeDays, userId]);

  useEffect(() => {
    if (!openSessionKey) {
      return;
    }
    let isCurrent = true;
    void fetchWorkoutExerciseHistorySessionDetail(
      userId,
      openSessionKey,
      rangeDays,
    ).then((nextResult) => {
      if (isCurrent) {
        setSessionDetail(nextResult);
      }
    });
    return () => {
      isCurrent = false;
    };
  }, [openSessionKey, rangeDays, userId]);

  const closeDetail = useCallback(() => {
    setOpenSessionKey(null);
  }, []);

  if (result === null) {
    return (
      <StudioState>
        <p className="font-medium text-text-primary">
          Loading performance history…
        </p>
      </StudioState>
    );
  }

  if (result.error || !result.data) {
    return (
      <section className="rounded-2xl bg-danger-surface px-4 py-5">
        <h2 className="font-semibold text-danger-foreground">
          {result.error?.heading ?? "Unable to load performance history"}
        </h2>
        <p className="mt-1 text-sm text-text-body">
          {result.error?.message ?? "Refresh the page to try again."}
        </p>
      </section>
    );
  }

  const exercises = result.data.exercises;
  const selectedExercise =
    exercises.find(
      (exercise) => exerciseAnalyticsKey(exercise) === selectedExerciseKey,
    ) ?? exercises[0];
  const openSummary = selectedExercise?.recent_sessions.find(
    (session) => session.session_key === openSessionKey,
  );

  function activateExercise(key: string) {
    const exercise = exercises.find(
      (item) => exerciseAnalyticsKey(item) === key,
    );
    selectedExerciseKeyRef.current = key;
    setSelectedExerciseKey(key);
    setActiveSessionKey(
      latestDatedSession(exercise?.recent_sessions ?? [])?.session_key ?? "",
    );
    setOpenSessionKey(null);
    setSessionDetail(null);
  }

  function openSession(sessionKey: string) {
    setActiveSessionKey(sessionKey);
    setSessionDetail(null);
    setOpenSessionKey(sessionKey);
  }

  return (
    <div className="min-w-0 space-y-3 sm:space-y-4">
      <StudioControls
        exercises={exercises}
        rangeDays={rangeDays}
        selectedExercise={selectedExercise}
        onRangeChange={(value) => {
          setResult(null);
          setOpenSessionKey(null);
          setRangeDays(value);
        }}
        onExerciseChange={activateExercise}
      />

      {!selectedExercise ? (
        <StudioState>
          <p className="font-medium text-text-primary">
            {performanceStudioEmptyMessage(
              result.data.overview.has_history,
              rangeDays,
            )}
          </p>
        </StudioState>
      ) : (
        <PerformanceTimeline
          activeSessionKey={activeSessionKey}
          exercise={selectedExercise}
          graphControlRef={graphControlRef}
          onSessionActivate={setActiveSessionKey}
          onSessionOpen={openSession}
        />
      )}

      <ResponsiveSidecarDialog
        eyebrow="Session detail"
        onClose={closeDetail}
        open={openSessionKey !== null}
        returnFocusRef={graphControlRef}
        title={selectedExercise?.exercise_name ?? "Session detail"}
      >
        <FocusedSessionDetail
          detailResult={sessionDetail}
          exercise={selectedExercise}
          summary={openSummary}
        />
      </ResponsiveSidecarDialog>
    </div>
  );
}

function StudioControls({
  exercises,
  rangeDays,
  selectedExercise,
  onRangeChange,
  onExerciseChange,
}: {
  exercises: ExerciseHistoryAnalyticsSummary[];
  rangeDays: PerformanceStudioRangeDays;
  selectedExercise: ExerciseHistoryAnalyticsSummary | undefined;
  onRangeChange: (value: PerformanceStudioRangeDays) => void;
  onExerciseChange: (value: string) => void;
}) {
  return (
    <section className="rounded-2xl bg-surface px-4 py-3 ring-1 ring-border sm:px-5">
      <div className="grid gap-3 md:grid-cols-[minmax(14rem,1fr)_auto] md:items-end">
        <label className="space-y-1 text-xs font-semibold text-text-secondary">
          <span>Exercise</span>
          <select
            aria-label="Performance history exercise"
            value={
              selectedExercise ? exerciseAnalyticsKey(selectedExercise) : ""
            }
            disabled={exercises.length === 0}
            onChange={(event) => onExerciseChange(event.target.value)}
            className="min-h-10 w-full rounded-xl border border-border bg-surface-subtle px-3 text-base text-text-strong outline-none focus:border-focus-subtle disabled:cursor-not-allowed disabled:opacity-60 sm:text-sm"
          >
            {exercises.length === 0 ? (
              <option value="">No exercises in this range</option>
            ) : null}
            {exercises.map((exercise) => (
              <option
                key={exerciseAnalyticsKey(exercise)}
                value={exerciseAnalyticsKey(exercise)}
              >
                {exercise.exercise_name}
              </option>
            ))}
          </select>
        </label>

        <div>
          <p
            id="performance-range-label"
            className="text-xs font-semibold text-text-secondary"
          >
            Date range
          </p>
          <div
            aria-labelledby="performance-range-label"
            className="mt-1 grid grid-cols-4 gap-1 rounded-xl bg-surface-subtle p-1"
            role="group"
          >
            {PERFORMANCE_STUDIO_RANGES.map((range) => (
              <button
                key={range.days}
                type="button"
                aria-pressed={rangeDays === range.days}
                onClick={() => onRangeChange(range.days)}
                className={`min-h-9 rounded-lg px-2 text-xs font-semibold transition sm:px-3 sm:text-sm ${
                  rangeDays === range.days
                    ? "bg-action-primary text-action-primary-foreground"
                    : "text-text-body hover:bg-surface-muted"
                }`}
              >
                {range.label}
              </button>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

function PerformanceTimeline({
  exercise,
  activeSessionKey,
  graphControlRef,
  onSessionActivate,
  onSessionOpen,
}: {
  exercise: ExerciseHistoryAnalyticsSummary;
  activeSessionKey: string;
  graphControlRef: RefObject<HTMLDivElement | null>;
  onSessionActivate: (sessionKey: string) => void;
  onSessionOpen: (sessionKey: string) => void;
}) {
  const [graphWidth, setGraphWidth] = useState(0);
  const [hovered, setHovered] = useState(false);
  const [focused, setFocused] = useState(false);
  const instructionsId = useId();
  const sessions = useMemo(
    () =>
      [...exercise.recent_sessions]
        .filter(
          (session): session is DatedSession => session.performed_at !== null,
        )
        .sort((left, right) =>
          left.performed_at.localeCompare(right.performed_at),
        ),
    [exercise.recent_sessions],
  );

  useEffect(() => {
    const graph = graphControlRef.current;
    if (!graph) {
      return;
    }
    const updateWidth = () => setGraphWidth(graph.getBoundingClientRect().width);
    updateWidth();
    const observer = new ResizeObserver(updateWidth);
    observer.observe(graph);
    return () => observer.disconnect();
  }, [graphControlRef]);

  if (sessions.length === 0) {
    return (
      <StudioState>
        Completed sessions in this range do not have usable dates.
      </StudioState>
    );
  }

  const startDate = sessions[0].performed_at;
  const endDate = sessions[sessions.length - 1].performed_at;
  const positions = sessions.map((session) =>
    timelineDatePosition(session.performed_at, startDate, endDate),
  );
  const primaryMetric =
    [...sessions]
      .reverse()
      .find((session) => session.performance_metric !== null)
      ?.performance_metric ?? null;
  const metricType = primaryMetric?.metric_type ?? null;
  const metricValues = sessions.flatMap((session) =>
    metricType !== null &&
    session.performance_metric?.metric_type === metricType
      ? [session.performance_metric.value]
      : [],
  );
  const metricScale = buildPerformanceMetricScale(metricValues);
  const sessionByKey = new Map(
    sessions.map((session, index) => [session.session_key, { session, index }]),
  );
  const metricRuns =
    metricType === null ? [] : splitMetricRuns(sessions, metricType);
  const effortSegments = buildEffortSegments(sessions);
  const plotPixelWidth =
    graphWidth * ((PLOT_RIGHT - PLOT_LEFT) / CHART_WIDTH);
  const tickCount = Math.max(
    2,
    Math.min(7, Math.floor(Math.max(plotPixelWidth, 220) / 110)),
  );
  const calendarTicks = buildCalendarTicks(startDate, endDate, tickCount);
  const phaseBands = exercise.historical_phase_segments.filter(
    sustainedPhaseBand,
  );
  const latestSession = sessions[sessions.length - 1];
  const activeIndex = Math.max(
    0,
    sessions.findIndex((session) => session.session_key === activeSessionKey),
  );
  const activeSession = sessions[activeIndex] ?? latestSession;
  const showInteraction = hovered || focused;

  function sessionPoint(session: DatedSession): { x: number; y: number } {
    const x =
      PLOT_LEFT +
      timelineDatePosition(session.performed_at, startDate, endDate) *
        (PLOT_RIGHT - PLOT_LEFT);
    const value =
      metricType !== null &&
      session.performance_metric?.metric_type === metricType &&
      metricScale !== null
        ? session.performance_metric.value
        : null;
    let y = (PLOT_TOP + PLOT_BOTTOM) / 2;
    if (value !== null && metricScale !== null) {
      y =
        PLOT_BOTTOM -
        performanceMetricPosition(value, metricScale) *
          (PLOT_BOTTOM - PLOT_TOP);
    }
    return { x, y };
  }

  function nearestIndexFromClientX(clientX: number, element: HTMLElement) {
    const bounds = element.getBoundingClientRect();
    const viewX = ((clientX - bounds.left) / Math.max(bounds.width, 1)) * CHART_WIDTH;
    const normalized = (viewX - PLOT_LEFT) / (PLOT_RIGHT - PLOT_LEFT);
    return nearestSessionIndex(positions, normalized);
  }

  function activateFromPointer(
    event: MouseEvent<HTMLDivElement>,
    open: boolean,
  ) {
    const index = nearestIndexFromClientX(
      event.clientX,
      event.currentTarget,
    );
    const session = sessions[index];
    if (!session) {
      return;
    }
    onSessionActivate(session.session_key);
    if (open) {
      event.currentTarget.focus();
      onSessionOpen(session.session_key);
    }
  }

  function handleGraphKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    let nextIndex: number | null = null;
    if (event.key === "ArrowLeft" || event.key === "ArrowDown") {
      nextIndex = moveSessionIndex(activeIndex, sessions.length, -1);
    } else if (event.key === "ArrowRight" || event.key === "ArrowUp") {
      nextIndex = moveSessionIndex(activeIndex, sessions.length, 1);
    } else if (event.key === "Home") {
      nextIndex = 0;
    } else if (event.key === "End") {
      nextIndex = sessions.length - 1;
    } else if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      onSessionOpen(activeSession.session_key);
      return;
    }
    if (nextIndex !== null && nextIndex >= 0) {
      event.preventDefault();
      onSessionActivate(sessions[nextIndex].session_key);
    }
  }

  const activePoint = sessionPoint(activeSession);
  const latestPoint = sessionPoint(latestSession);
  const tooltipBelowPoint = activePoint.y < PLOT_TOP + 74;
  const tooltipHorizontalTransform =
    activePoint.x > CHART_WIDTH * 0.72
      ? "translateX(-100%)"
      : activePoint.x < CHART_WIDTH * 0.28
        ? "translateX(0)"
        : "translateX(-50%)";

  return (
    <section className="min-w-0 overflow-hidden rounded-2xl bg-surface ring-1 ring-border">
      <div
        ref={graphControlRef}
        aria-describedby={instructionsId}
        aria-label={`${exercise.exercise_name} performance graph`}
        aria-valuemax={sessions.length}
        aria-valuemin={1}
        aria-valuenow={activeIndex + 1}
        aria-valuetext={timelinePointLabel(exercise.exercise_name, activeSession)}
        className="relative h-[27rem] min-w-0 touch-pan-y overflow-hidden bg-surface-subtle outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-focus-subtle sm:h-[32rem] lg:h-[38rem]"
        onBlur={() => setFocused(false)}
        onClick={(event) => activateFromPointer(event, true)}
        onFocus={() => setFocused(true)}
        onKeyDown={handleGraphKeyDown}
        onMouseLeave={() => setHovered(false)}
        onMouseMove={(event) => {
          setHovered(true);
          activateFromPointer(event, false);
        }}
        role="slider"
        tabIndex={0}
      >
        <span id={instructionsId} className="sr-only">
          Use arrow keys to move between recorded sessions. Press Enter to open
          the selected session.
        </span>

        <svg
          aria-hidden="true"
          className="absolute inset-0 h-full w-full"
          preserveAspectRatio="none"
          viewBox={`0 0 ${CHART_WIDTH} ${CHART_HEIGHT}`}
        >
          <rect
            x={PLOT_LEFT}
            y={PLOT_TOP}
            width={PLOT_RIGHT - PLOT_LEFT}
            height={PLOT_BOTTOM - PLOT_TOP}
            className="fill-surface"
          />

          {phaseBands.map((phase, index) => {
            const start =
              PLOT_LEFT +
              timelineDatePosition(phase.start_date, startDate, endDate) *
                (PLOT_RIGHT - PLOT_LEFT);
            const end =
              PLOT_LEFT +
              timelineDatePosition(phase.end_date, startDate, endDate) *
                (PLOT_RIGHT - PLOT_LEFT);
            return (
              <rect
                key={`${phase.code}-${phase.start_session_key}-${index}`}
                x={start}
                y={PLOT_TOP}
                width={Math.max(0, end - start)}
                height={PLOT_BOTTOM - PLOT_TOP}
                className={phaseBandClass(phase.code)}
                opacity="0.26"
              />
            );
          })}

          {metricScale?.ticks.map((tick) => {
            const y =
              PLOT_BOTTOM -
              performanceMetricPosition(tick, metricScale) *
                (PLOT_BOTTOM - PLOT_TOP);
            return (
              <line
                key={tick}
                x1={PLOT_LEFT}
                x2={PLOT_RIGHT}
                y1={y}
                y2={y}
                className="stroke-border"
                strokeDasharray="4 7"
                strokeWidth="1"
              />
            );
          })}

          {calendarTicks.map((tick) => {
            const x =
              PLOT_LEFT +
              timelineDatePosition(tick, startDate, endDate) *
                (PLOT_RIGHT - PLOT_LEFT);
            return (
              <line
                key={tick}
                x1={x}
                x2={x}
                y1={PLOT_TOP}
                y2={EFFORT_BOTTOM}
                className="stroke-border-subtle"
                strokeWidth="1"
              />
            );
          })}

          {metricRuns.map((run, index) => {
            const points = run
              .map((sessionKey) => sessionByKey.get(sessionKey)?.session)
              .filter((session): session is DatedSession => session !== undefined)
              .map((session) => {
                const point = sessionPoint(session);
                return `${point.x},${point.y}`;
              });
            return points.length >= 2 ? (
              <polyline
                key={`${run[0]}-${index}`}
                fill="none"
                points={points.join(" ")}
                className="stroke-action-primary"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="3"
                vectorEffect="non-scaling-stroke"
              />
            ) : null;
          })}

          <rect
            x={PLOT_LEFT}
            y={EFFORT_TOP}
            width={PLOT_RIGHT - PLOT_LEFT}
            height={EFFORT_BOTTOM - EFFORT_TOP}
            rx="5"
            className="fill-surface"
          />
          {effortSegments.map((segment, index) => {
            const points = segment
              .map((sessionKey) => sessionByKey.get(sessionKey)?.session)
              .filter((session): session is DatedSession => session !== undefined)
              .map((session) => {
                const x =
                  PLOT_LEFT +
                  timelineDatePosition(
                    session.performed_at,
                    startDate,
                    endDate,
                  ) *
                    (PLOT_RIGHT - PLOT_LEFT);
                const rir = Math.min(
                  5,
                  Math.max(0, session.average_actual_rir ?? 0),
                );
                const y =
                  EFFORT_BOTTOM -
                  (rir / 5) * (EFFORT_BOTTOM - EFFORT_TOP);
                return { x, y };
              });
            if (points.length === 1) {
              return (
                <line
                  key={`${segment[0]}-${index}`}
                  x1={points[0].x - 4}
                  x2={points[0].x + 4}
                  y1={points[0].y}
                  y2={points[0].y}
                  className="stroke-accent-text"
                  strokeLinecap="round"
                  strokeWidth="2"
                  vectorEffect="non-scaling-stroke"
                />
              );
            }
            return points.length >= 2 ? (
              <polyline
                key={`${segment[0]}-${index}`}
                fill="none"
                points={points.map((point) => `${point.x},${point.y}`).join(" ")}
                className="stroke-accent-text"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                vectorEffect="non-scaling-stroke"
              />
            ) : null;
          })}

          <rect
            x={latestPoint.x - 4}
            y={PLOT_TOP}
            width="8"
            height={EFFORT_BOTTOM - PLOT_TOP}
            className="fill-action-primary"
            opacity="0.07"
          />
          <line
            x1={latestPoint.x}
            x2={latestPoint.x}
            y1={PLOT_TOP}
            y2={EFFORT_BOTTOM}
            className="stroke-action-primary"
            opacity="0.28"
            strokeWidth="1"
            vectorEffect="non-scaling-stroke"
          />

          {showInteraction ? (
            <line
              x1={activePoint.x}
              x2={activePoint.x}
              y1={PLOT_TOP}
              y2={EFFORT_BOTTOM}
              className="stroke-text-strong"
              strokeDasharray="3 4"
              strokeWidth="1"
              vectorEffect="non-scaling-stroke"
            />
          ) : null}
        </svg>

        <div
          aria-hidden="true"
          className="pointer-events-none absolute left-1 top-3 text-[0.65rem] font-semibold uppercase tracking-[0.08em] text-text-secondary sm:left-3 sm:text-xs"
        >
          {primaryMetric
            ? `${primaryMetric.label} · ${displayUnit(primaryMetric.unit)}`
            : "Recorded performance"}
        </div>

        {metricScale?.ticks.map((tick) => {
          const y =
            PLOT_BOTTOM -
            performanceMetricPosition(tick, metricScale) *
              (PLOT_BOTTOM - PLOT_TOP);
          return (
            <span
              key={tick}
              aria-hidden="true"
              className="pointer-events-none absolute left-1 -translate-y-1/2 text-[0.62rem] tabular-nums text-text-muted sm:left-3 sm:text-[0.7rem]"
              style={{ top: `${(y / CHART_HEIGHT) * 100}%` }}
            >
              {formatHistoryNumber(tick)}
            </span>
          );
        })}

        <span
          aria-hidden="true"
          className="pointer-events-none absolute left-1 text-[0.62rem] font-semibold uppercase tracking-[0.08em] text-text-secondary sm:left-3 sm:text-[0.7rem]"
          style={{ top: `${(EFFORT_TOP / CHART_HEIGHT) * 100}%` }}
        >
          RIR
        </span>

        {calendarTicks.map((tick, index) => {
          const position = timelineDatePosition(tick, startDate, endDate);
          const x =
            PLOT_LEFT + position * (PLOT_RIGHT - PLOT_LEFT);
          const transform =
            index === 0
              ? "translateX(0)"
              : index === calendarTicks.length - 1
                ? "translateX(-100%)"
                : "translateX(-50%)";
          return (
            <span
              key={tick}
              aria-hidden="true"
              className="pointer-events-none absolute whitespace-nowrap text-[0.62rem] text-text-secondary sm:text-[0.7rem]"
              style={{
                left: `${(x / CHART_WIDTH) * 100}%`,
                top: `${((EFFORT_BOTTOM + 15) / CHART_HEIGHT) * 100}%`,
                transform,
              }}
            >
              {formatHistoryDate(tick)}
            </span>
          );
        })}

        {phaseBands.map((phase, index) => {
          if (
            !phaseBandCanShowLabel(
              phase,
              startDate,
              endDate,
              plotPixelWidth,
            )
          ) {
            return null;
          }
          const start = timelineDatePosition(
            phase.start_date,
            startDate,
            endDate,
          );
          const end = timelineDatePosition(
            phase.end_date,
            startDate,
            endDate,
          );
          const left =
            PLOT_LEFT + start * (PLOT_RIGHT - PLOT_LEFT);
          const width = (end - start) * (PLOT_RIGHT - PLOT_LEFT);
          return (
            <span
              key={`${phase.code}-${index}`}
              aria-hidden="true"
              className="pointer-events-none absolute truncate px-2 pt-2 text-[0.65rem] font-semibold text-text-secondary"
              style={{
                left: `${(left / CHART_WIDTH) * 100}%`,
                top: `${(PLOT_TOP / CHART_HEIGHT) * 100}%`,
                width: `${(width / CHART_WIDTH) * 100}%`,
              }}
            >
              {phase.label}
            </span>
          );
        })}

        {showInteraction ? (
          <div
            className="pointer-events-none absolute z-10 max-w-[15rem] rounded-lg bg-surface px-3 py-2 text-xs text-text-primary shadow-lg ring-1 ring-border"
            style={{
              left: `${(activePoint.x / CHART_WIDTH) * 100}%`,
              top: `${((tooltipBelowPoint ? activePoint.y + 12 : activePoint.y - 12) / CHART_HEIGHT) * 100}%`,
              transform: `${tooltipHorizontalTransform} ${
                tooltipBelowPoint ? "translateY(0)" : "translateY(-100%)"
              }`,
            }}
          >
            <p className="font-semibold">
              {formatHistoryDate(activeSession.performed_at, true)}
            </p>
            <p className="mt-0.5 leading-4 text-text-body">
              {activeSession.summary}
            </p>
            {activeSession.phase ? (
              <p className="mt-1 font-semibold text-text-secondary">
                {activeSession.phase.label}
              </p>
            ) : null}
          </div>
        ) : null}
      </div>
    </section>
  );
}

function FocusedSessionDetail({
  exercise,
  summary,
  detailResult,
}: {
  exercise: ExerciseHistoryAnalyticsSummary | undefined;
  summary: ExerciseHistoryRecentSession | undefined;
  detailResult: WorkoutExerciseHistorySessionDetailApiResult | null;
}) {
  if (!exercise || !summary) {
    return (
      <p className="text-sm text-text-secondary">
        The selected session is unavailable.
      </p>
    );
  }
  if (detailResult === null) {
    return (
      <div>
        <DetailHeading session={summary} />
        <p className="mt-4 text-sm text-text-secondary">
          Loading recorded sets…
        </p>
      </div>
    );
  }
  if (detailResult.error || !detailResult.data) {
    return (
      <div>
        <DetailHeading session={summary} />
        <p className="mt-4 rounded-xl bg-danger-surface px-3 py-3 text-sm text-danger-foreground">
          {detailResult.error?.message ?? "Session details are unavailable."}
        </p>
      </div>
    );
  }
  return (
    <SessionDetail
      exercise={exercise}
      session={detailResult.data.session}
    />
  );
}

function DetailHeading({ session }: { session: ExerciseHistoryRecentSession }) {
  return (
    <div>
      <p className="text-sm font-semibold text-text-secondary">
        {formatHistoryDate(session.performed_at, true)}
      </p>
      <p className="mt-1 text-base leading-6 text-text-primary">
        {session.summary}
      </p>
    </div>
  );
}

function SessionDetail({
  exercise,
  session,
}: {
  exercise: ExerciseHistoryAnalyticsSummary;
  session: ExerciseHistoryRecentSession;
}) {
  const completion =
    session.planned_set_count > 0 &&
    session.completed_set_count >= session.planned_set_count
      ? "Complete"
      : session.completed_set_count > 0
        ? "Partially complete"
        : "Not completed";

  return (
    <div>
      <DetailHeading session={session} />

      <dl className="mt-4 grid grid-cols-2 gap-2">
        <DetailMetric
          label="Completion"
          value={`${completion} · ${session.completed_set_count} of ${session.planned_set_count} sets`}
        />
        <DetailMetric
          label="Effort"
          value={
            session.average_actual_rir === null
              ? "RIR not fully recorded"
              : `Average RIR ${formatHistoryNumber(session.average_actual_rir)}`
          }
        />
      </dl>

      <section className="mt-5">
        <h3 className="text-sm font-semibold text-text-strong">Recorded sets</h3>
        {session.recorded_sets.length === 0 ? (
          <p className="mt-2 rounded-xl bg-surface px-3 py-3 text-sm text-text-body ring-1 ring-border-subtle">
            No recorded set rows are available for this session.
          </p>
        ) : (
          <ol
            aria-label={`Recorded sets from ${formatHistoryDate(session.performed_at, true)}`}
            className="mt-2 divide-y divide-border-subtle rounded-xl bg-surface px-3 ring-1 ring-border-subtle"
          >
            {session.recorded_sets.map((set) => (
              <li
                key={set.set_number}
                className="grid grid-cols-[3.75rem_minmax(0,1fr)] gap-3 py-3 text-sm"
              >
                <span className="font-semibold text-text-secondary">
                  Set {set.set_number}
                </span>
                <div className="min-w-0">
                  <p className="text-xs font-semibold text-text-secondary">
                    {recordedSetStatus(set)}
                  </p>
                  <p className="mt-0.5 text-text-primary">
                    {formatRecordedSet(set)}
                  </p>
                </div>
              </li>
            ))}
          </ol>
        )}
      </section>

      <section className="mt-5 space-y-3">
        <DetailFact
          label="Change from previous comparable session"
          value={
            session.previous_comparison
              ? formatPreviousComparison(session.previous_comparison)
              : "No earlier comparable session in this range"
          }
        />
        <DetailFact
          label="Containing phase"
          value={session.phase?.label ?? "No sustained phase"}
          detail={session.phase?.evidence}
        />
        <DetailFact
          label="Milestone"
          value={
            session.milestones.length > 0
              ? session.milestones.map((milestone) => milestone.label).join(", ")
              : "No milestone recorded"
          }
          detail={session.milestones
            .map((milestone) => milestone.evidence)
            .join(" ")}
        />
      </section>

      <details className="mt-5 rounded-xl bg-surface ring-1 ring-border-subtle">
        <summary className="cursor-pointer px-3 py-3 text-sm font-semibold text-text-primary">
          Context
        </summary>
        <div className="space-y-4 border-t border-border-subtle px-3 py-4">
          <ContextComparison comparison={exercise.then_vs_now} />
          <DetailFact
            label="Current pattern"
            value={exercise.current_trend?.label ?? "No clear current pattern"}
            detail={exercise.current_trend?.evidence}
          />
          <DetailFact
            label="Relevant longer context"
            value={
              exercise.recent_best_set?.summary ??
              exercise.latest_completed_session_summary
            }
            detail={exercise.progression_recommendation.target_guidance}
          />
          {exercise.limitation ? (
            <p className="rounded-lg bg-caution-surface px-3 py-2 text-xs leading-5 text-caution-foreground">
              {exercise.limitation}
            </p>
          ) : null}
        </div>
      </details>
    </div>
  );
}

function DetailMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl bg-surface px-3 py-2 ring-1 ring-border-subtle">
      <dt className="text-xs text-text-secondary">{label}</dt>
      <dd className="mt-0.5 text-sm font-semibold text-text-primary">{value}</dd>
    </div>
  );
}

function DetailFact({
  label,
  value,
  detail,
}: {
  label: string;
  value: string;
  detail?: string | null;
}) {
  return (
    <div>
      <p className="text-[0.68rem] font-semibold uppercase tracking-[0.1em] text-text-muted">
        {label}
      </p>
      <p className="mt-1 text-sm font-semibold text-text-primary">{value}</p>
      {detail ? (
        <p className="mt-1 text-xs leading-5 text-text-secondary">{detail}</p>
      ) : null}
    </div>
  );
}

function ContextComparison({
  comparison,
}: {
  comparison: ExercisePerformanceComparison | null;
}) {
  if (!comparison) {
    return (
      <DetailFact
        label="Then versus now"
        value="More comparable history is needed"
      />
    );
  }
  return (
    <DetailFact
      label="Then versus now"
      value={`${formatComparisonMetric(comparison, comparison.then_value)} → ${formatComparisonMetric(comparison, comparison.now_value)}`}
      detail={`${formatHistoryDate(comparison.then_performed_at)} to ${formatHistoryDate(comparison.now_performed_at)} · ${formatSignedChange(comparison)}`}
    />
  );
}

function StudioState({ children }: { children: ReactNode }) {
  return (
    <section className="rounded-2xl bg-surface px-4 py-6 text-text-body ring-1 ring-border sm:px-5">
      {children}
    </section>
  );
}

function latestDatedSession(
  sessions: ExerciseHistoryRecentSession[],
): DatedSession | undefined {
  return sessions
    .filter((session): session is DatedSession => session.performed_at !== null)
    .sort((left, right) =>
      right.performed_at.localeCompare(left.performed_at),
    )[0];
}

function timelinePointLabel(
  exerciseName: string,
  session: ExerciseHistoryRecentSession,
): string {
  return [
    exerciseName,
    formatHistoryDate(session.performed_at, true),
    session.summary,
  ].join(", ");
}

function phaseBandClass(
  code: ExercisePerformancePhaseSegment["code"],
): string {
  return {
    progression: "fill-positive-surface",
    stable_effort_rise: "fill-caution-surface",
    plateau: "fill-surface-muted",
    deload: "fill-surface-highlighted",
    rebound: "fill-positive-surface",
  }[code];
}

function displayUnit(unit: ExercisePerformanceMetric["unit"]): string {
  return {
    lb: "lb",
    reps: "reps",
    seconds: "seconds",
    meters: "meters",
  }[unit];
}

function comparisonMetricLabel(
  metricType: ExercisePerformanceMetricType,
): string {
  return {
    load: "Load",
    reps: "Best set",
    duration: "Longest set",
    distance: "Longest set",
  }[metricType];
}

function recordedSetStatus(set: ExerciseHistoryRecordedSet): string {
  if (set.completed) {
    return "Completed";
  }
  return set.skipped ? "Skipped" : "Incomplete";
}

function formatRecordedSet(set: ExerciseHistoryRecordedSet): string {
  const parts = [
    set.actual_reps === null ? null : `${set.actual_reps} reps`,
    set.actual_duration_seconds === null
      ? null
      : formatPerformanceMetric({
          metric_type: "duration",
          label: "Duration",
          value: set.actual_duration_seconds,
          unit: "seconds",
        }),
    set.actual_distance_meters === null
      ? null
      : formatPerformanceMetric({
          metric_type: "distance",
          label: "Distance",
          value: set.actual_distance_meters,
          unit: "meters",
        }),
    set.actual_weight === null
      ? null
      : `${formatHistoryNumber(set.actual_weight)} lb`,
    set.actual_rir === null ? null : `RIR ${formatHistoryNumber(set.actual_rir)}`,
  ].filter((part): part is string => part !== null);
  return parts.length > 0 ? parts.join(" · ") : "No values recorded";
}

function formatPreviousComparison(
  comparison: ExercisePerformanceComparison,
): string {
  const current = formatComparisonMetric(comparison, comparison.now_value);
  const previous = formatComparisonMetric(comparison, comparison.then_value);
  return `${current} vs ${previous} on ${formatHistoryDate(comparison.then_performed_at, true)} · ${formatSignedChange(comparison)}`;
}

function formatComparisonMetric(
  comparison: ExercisePerformanceComparison,
  value: number,
): string {
  return formatPerformanceMetric({
    metric_type: comparison.metric_type,
    label: comparisonMetricLabel(comparison.metric_type),
    unit: comparison.unit,
    value,
  });
}

function formatSignedChange(
  comparison: ExercisePerformanceComparison,
): string {
  if (comparison.direction === "steady") {
    return "no change";
  }
  const value = formatComparisonMetric(
    comparison,
    Math.abs(comparison.absolute_change),
  );
  return `${value} ${comparison.direction === "higher" ? "higher" : "lower"}`;
}

function formatHistoryNumber(value: number): string {
  return Number.isInteger(value) ? String(value) : value.toFixed(1);
}

function formatHistoryDate(value: string | null, includeYear = false): string {
  if (!value) {
    return "Date unavailable";
  }
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    ...(includeYear ? { year: "numeric" as const } : {}),
  }).format(new Date(`${value}T00:00:00`));
}
