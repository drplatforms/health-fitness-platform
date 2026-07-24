"use client";

import {
  type KeyboardEvent,
  type PointerEvent as ReactPointerEvent,
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
  type WorkoutExerciseHistoryAnalyticsApiResult,
  type WorkoutExerciseHistorySessionDetailApiResult,
} from "@/lib/workoutExerciseHistoryApi";
import {
  activeSelectionIndicatorsVisible,
  classifyMouseGesture,
  classifyTouchGesture,
  dragNavigatorViewport,
  fitViewport,
  isoDateRangeEndingOn,
  isoDateToOuterPosition,
  isoDateToViewportPosition,
  MIN_NAVIGATOR_PAN_TARGET_PIXELS,
  outerToViewportPosition,
  panViewport,
  pinchZoomViewport,
  resizeNavigatorViewport,
  revealOuterPosition,
  sessionTraversalIndices,
  spreadCoincidentSessionPositions,
  touchGestureOpensSession,
  type NavigatorViewportEdge,
  type PerformanceViewport,
  viewportPositionToIsoDate,
  viewportToOuterPosition,
  visibleSessionIndexRange,
  zoomViewport,
} from "@/lib/workoutPerformanceViewport";
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
const ZOOM_STEP = 1.6;
const WHEEL_ZOOM_SENSITIVITY = 0.0025;
const NAVIGATOR_HEIGHT = 72;
const NAVIGATOR_LINE_TOP = 12;
const NAVIGATOR_LINE_BOTTOM = 60;

type DatedSession = ExerciseHistoryRecentSession & { performed_at: string };

interface PointerSample {
  clientX: number;
  clientY: number;
  pointerType: string;
}

interface PinchSnapshot {
  viewport: PerformanceViewport;
  distance: number;
  anchorOuterPosition: number;
}

interface ChartGestureState {
  primaryPointerId: number;
  pointerType: string;
  startX: number;
  startY: number;
  startViewport: PerformanceViewport;
  maximumTouchCount: number;
  mode: "pending" | "pan" | "scrub" | "scroll" | "pinch";
  lastSessionIndex: number;
  pinch: PinchSnapshot | null;
}

interface NavigatorGestureState {
  pointerId: number;
  pointerType: string;
  mode: "pan" | NavigatorViewportEdge;
  startX: number;
  startY: number;
  startViewport: PerformanceViewport;
  committed: boolean;
  scrolling: boolean;
}

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
  const orderedSessions = chronologicalDatedSessions(
    selectedExercise?.recent_sessions ?? [],
  );
  const openSessionIndex = orderedSessions.findIndex(
    (session) => session.session_key === openSessionKey,
  );
  const openSummary =
    openSessionIndex >= 0 ? orderedSessions[openSessionIndex] : undefined;

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

  function moveOpenSession(direction: -1 | 1) {
    const nextIndex = moveSessionIndex(
      openSessionIndex,
      orderedSessions.length,
      direction,
    );
    const nextSession = orderedSessions[nextIndex];
    if (nextSession && nextIndex !== openSessionIndex) {
      openSession(nextSession.session_key);
    }
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
          key={`${exerciseAnalyticsKey(selectedExercise)}:${rangeDays}`}
          activeSessionKey={activeSessionKey}
          detailOpen={openSessionKey !== null}
          exercise={selectedExercise}
          graphControlRef={graphControlRef}
          onSessionActivate={setActiveSessionKey}
          onSessionOpen={openSession}
          rangeDays={rangeDays}
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
          canMoveNext={
            openSessionIndex >= 0 &&
            openSessionIndex < orderedSessions.length - 1
          }
          canMovePrevious={openSessionIndex > 0}
          onMoveSession={moveOpenSession}
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
  detailOpen,
  graphControlRef,
  onSessionActivate,
  onSessionOpen,
  rangeDays,
}: {
  exercise: ExerciseHistoryAnalyticsSummary;
  activeSessionKey: string;
  detailOpen: boolean;
  graphControlRef: RefObject<HTMLDivElement | null>;
  onSessionActivate: (sessionKey: string) => void;
  onSessionOpen: (sessionKey: string) => void;
  rangeDays: PerformanceStudioRangeDays;
}) {
  const [graphWidth, setGraphWidth] = useState(0);
  const [hovered, setHovered] = useState(false);
  const [focused, setFocused] = useState(false);
  const [scrubbing, setScrubbing] = useState(false);
  const [viewport, setViewportState] =
    useState<PerformanceViewport>(fitViewport);
  const viewportRef = useRef(viewport);
  const activePointersRef = useRef(new Map<number, PointerSample>());
  const chartGestureRef = useRef<ChartGestureState | null>(null);
  const navigatorGestureRef = useRef<NavigatorGestureState | null>(null);
  const navigatorRef = useRef<HTMLDivElement>(null);
  const chartId = useId();
  const instructionsId = `${chartId}-instructions`;
  const clipPathId = `${chartId.replaceAll(":", "")}-plot-clip`;
  const sessions = useMemo(
    () => chronologicalDatedSessions(exercise.recent_sessions),
    [exercise.recent_sessions],
  );
  const outerRange = useMemo(
    () => isoDateRangeEndingOn(localIsoDate(), rangeDays),
    [rangeDays],
  );
  const outerPositions = useMemo(
    () =>
      sessions.map((session) =>
        isoDateToOuterPosition(
          session.performed_at,
          outerRange.startDate,
          outerRange.endDate,
        ),
      ),
    [outerRange.endDate, outerRange.startDate, sessions],
  );
  const plottedOuterPositions = useMemo(
    () =>
      spreadCoincidentSessionPositions(
        outerPositions,
        0.2 / rangeDays,
        0.8 / rangeDays,
      ),
    [outerPositions, rangeDays],
  );
  const plottedPositionBySessionKey = useMemo(
    () =>
      new Map(
        sessions.map((session, index) => [
          session.session_key,
          plottedOuterPositions[index],
        ]),
      ),
    [plottedOuterPositions, sessions],
  );
  const applyViewport = useCallback((nextViewport: PerformanceViewport) => {
    viewportRef.current = nextViewport;
    setViewportState((current) =>
      current.start === nextViewport.start && current.end === nextViewport.end
        ? current
        : nextViewport,
    );
  }, []);

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

  useEffect(() => {
    const graph = graphControlRef.current;
    if (!graph) {
      return;
    }
    const handleWheel = (event: WheelEvent) => {
      if (!event.ctrlKey && !event.metaKey) {
        return;
      }
      event.preventDefault();
      const current = viewportRef.current;
      const pointerPosition = plotPositionFromClientX(event.clientX, graph);
      const anchor = viewportToOuterPosition(
        pointerPosition,
        current,
        true,
      );
      const delta =
        event.deltaMode === WheelEvent.DOM_DELTA_LINE
          ? event.deltaY * 16
          : event.deltaMode === WheelEvent.DOM_DELTA_PAGE
            ? event.deltaY * graph.clientHeight
            : event.deltaY;
      applyViewport(
        zoomViewport(
          current,
          Math.exp(-delta * WHEEL_ZOOM_SENSITIVITY),
          anchor,
        ),
      );
    };
    graph.addEventListener("wheel", handleWheel, { passive: false });
    return () => graph.removeEventListener("wheel", handleWheel);
  }, [applyViewport, graphControlRef]);

  useEffect(() => {
    const activeIndex = sessions.findIndex(
      (session) => session.session_key === activeSessionKey,
    );
    if (activeIndex < 0) {
      return;
    }
    const position = plottedOuterPositions[activeIndex];
    const current = viewportRef.current;
    if (position < current.start || position > current.end) {
      applyViewport(revealOuterPosition(current, position, 0.08));
    }
  }, [activeSessionKey, applyViewport, plottedOuterPositions, sessions]);

  if (sessions.length === 0) {
    return (
      <StudioState>
        Completed sessions in this range do not have usable dates.
      </StudioState>
    );
  }

  const visibleStartDate = viewportPositionToIsoDate(
    0,
    outerRange.startDate,
    outerRange.endDate,
    viewport,
  );
  const visibleEndDate = viewportPositionToIsoDate(
    1,
    outerRange.startDate,
    outerRange.endDate,
    viewport,
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
  const calendarTicks = buildCalendarTicks(
    visibleStartDate,
    visibleEndDate,
    tickCount,
  );
  const phaseBands = exercise.historical_phase_segments.filter(
    sustainedPhaseBand,
  );
  const latestSession = sessions[sessions.length - 1];
  const requestedActiveIndex = sessions.findIndex(
    (session) => session.session_key === activeSessionKey,
  );
  const activeIndex =
    requestedActiveIndex >= 0 ? requestedActiveIndex : sessions.length - 1;
  const activeSession = sessions[activeIndex] ?? latestSession;
  const activeOuterPosition = plottedOuterPositions[activeIndex] ?? 1;
  const activeIsVisible =
    activeOuterPosition >= viewport.start - Number.EPSILON &&
    activeOuterPosition <= viewport.end + Number.EPSILON;
  const showInteraction =
    activeSelectionIndicatorsVisible(
      hovered,
      focused,
      detailOpen,
      scrubbing,
    ) &&
    activeIsVisible;
  const viewportSpan = viewport.end - viewport.start;
  const isFitted = viewportSpan >= 1 - Number.EPSILON * 8;

  function sessionViewportPosition(session: DatedSession): number {
    const outerPosition =
      plottedPositionBySessionKey.get(session.session_key) ??
      isoDateToOuterPosition(
        session.performed_at,
        outerRange.startDate,
        outerRange.endDate,
      );
    return outerToViewportPosition(outerPosition, viewport);
  }

  function sessionPoint(session: DatedSession): { x: number; y: number } {
    const x =
      PLOT_LEFT +
      sessionViewportPosition(session) *
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

  function nearestVisibleIndexFromClientX(
    clientX: number,
    element: HTMLElement,
  ) {
    const current = viewportRef.current;
    const visibleRange = visibleSessionIndexRange(
      plottedOuterPositions,
      current,
    );
    return nearestSessionIndex(
      plottedOuterPositions,
      viewportToOuterPosition(
        plotPositionFromClientX(clientX, element),
        current,
        true,
      ),
      visibleRange.startIndex,
      visibleRange.endIndex,
    );
  }

  function activateAtClientX(
    clientX: number,
    element: HTMLDivElement,
    open: boolean,
  ) {
    const index = nearestVisibleIndexFromClientX(clientX, element);
    const session = sessions[index];
    if (!session) {
      return;
    }
    onSessionActivate(session.session_key);
    if (open) {
      element.focus({ preventScroll: true });
      onSessionOpen(session.session_key);
    }
  }

  function scrubAtClientX(
    clientX: number,
    element: HTMLDivElement,
    gesture: ChartGestureState,
  ): DatedSession | undefined {
    const nextIndex = nearestVisibleIndexFromClientX(clientX, element);
    const nextSession = sessions[nextIndex];
    if (!nextSession) {
      return undefined;
    }
    for (const index of sessionTraversalIndices(
      gesture.lastSessionIndex,
      nextIndex,
      sessions.length,
    )) {
      const session = sessions[index];
      if (session) {
        onSessionActivate(session.session_key);
      }
    }
    gesture.lastSessionIndex = nextIndex;
    return nextSession;
  }

  function revealSession(index: number, paddingFraction = 0.08) {
    const position = plottedOuterPositions[index];
    if (position === undefined) {
      return;
    }
    applyViewport(
      revealOuterPosition(
        viewportRef.current,
        position,
        paddingFraction,
      ),
    );
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
    } else if (event.key === "+" || event.key === "=") {
      event.preventDefault();
      applyViewport(
        zoomViewport(
          viewportRef.current,
          ZOOM_STEP,
          activeOuterPosition,
        ),
      );
      return;
    } else if (event.key === "-") {
      event.preventDefault();
      applyViewport(
        zoomViewport(
          viewportRef.current,
          1 / ZOOM_STEP,
          activeOuterPosition,
        ),
      );
      return;
    } else if (event.key === "0") {
      event.preventDefault();
      applyViewport(fitViewport());
      return;
    }
    if (nextIndex !== null && nextIndex >= 0) {
      event.preventDefault();
      revealSession(nextIndex);
      onSessionActivate(sessions[nextIndex].session_key);
    }
  }

  function beginPinch(element: HTMLDivElement) {
    const gesture = chartGestureRef.current;
    const touchPointers = [...activePointersRef.current.entries()].filter(
      ([, pointer]) => pointer.pointerType === "touch",
    );
    if (!gesture || touchPointers.length < 2) {
      return;
    }
    const [[, first], [, second]] = touchPointers;
    const centerX = (first.clientX + second.clientX) / 2;
    const current = viewportRef.current;
    gesture.mode = "pinch";
    gesture.maximumTouchCount = Math.max(
      gesture.maximumTouchCount,
      touchPointers.length,
    );
    gesture.pinch = {
      viewport: current,
      distance: Math.max(
        1,
        Math.hypot(
          second.clientX - first.clientX,
          second.clientY - first.clientY,
        ),
      ),
      anchorOuterPosition: viewportToOuterPosition(
        plotPositionFromClientX(centerX, element),
        current,
        true,
      ),
    };
    for (const [pointerId] of touchPointers) {
      capturePointer(element, pointerId);
    }
    setScrubbing(false);
    setHovered(false);
  }

  function updatePinch(element: HTMLDivElement) {
    const gesture = chartGestureRef.current;
    const pinch = gesture?.pinch;
    const touchPointers = [...activePointersRef.current.values()].filter(
      (pointer) => pointer.pointerType === "touch",
    );
    if (!gesture || !pinch || touchPointers.length < 2) {
      return;
    }
    const [first, second] = touchPointers;
    const distance = Math.max(
      1,
      Math.hypot(
        second.clientX - first.clientX,
        second.clientY - first.clientY,
      ),
    );
    const centerViewportPosition = plotPositionFromClientX(
      (first.clientX + second.clientX) / 2,
      element,
    );
    applyViewport(
      pinchZoomViewport(
        pinch.viewport,
        distance / pinch.distance,
        pinch.anchorOuterPosition,
        centerViewportPosition,
      ),
    );
  }

  function handleGraphPointerDown(
    event: ReactPointerEvent<HTMLDivElement>,
  ) {
    if (event.pointerType !== "touch" && event.button !== 0) {
      return;
    }
    activePointersRef.current.set(event.pointerId, {
      clientX: event.clientX,
      clientY: event.clientY,
      pointerType: event.pointerType,
    });
    const currentGesture = chartGestureRef.current;
    if (!currentGesture) {
      chartGestureRef.current = {
        primaryPointerId: event.pointerId,
        pointerType: event.pointerType,
        startX: event.clientX,
        startY: event.clientY,
        startViewport: viewportRef.current,
        maximumTouchCount: 1,
        mode: "pending",
        lastSessionIndex: nearestVisibleIndexFromClientX(
          event.clientX,
          event.currentTarget,
        ),
        pinch: null,
      };
      if (event.pointerType !== "touch") {
        capturePointer(event.currentTarget, event.pointerId);
        event.currentTarget.focus({ preventScroll: true });
      }
      return;
    }
    if (
      event.pointerType === "touch" &&
      currentGesture.pointerType === "touch"
    ) {
      event.preventDefault();
      beginPinch(event.currentTarget);
    }
  }

  function handleGraphPointerMove(
    event: ReactPointerEvent<HTMLDivElement>,
  ) {
    const tracked = activePointersRef.current.has(event.pointerId);
    if (!tracked) {
      if (
        (event.pointerType === "mouse" || event.pointerType === "pen") &&
        chartGestureRef.current === null
      ) {
        setHovered(true);
        activateAtClientX(event.clientX, event.currentTarget, false);
      }
      return;
    }

    activePointersRef.current.set(event.pointerId, {
      clientX: event.clientX,
      clientY: event.clientY,
      pointerType: event.pointerType,
    });
    const gesture = chartGestureRef.current;
    if (!gesture) {
      return;
    }
    gesture.maximumTouchCount = Math.max(
      gesture.maximumTouchCount,
      activePointersRef.current.size,
    );
    if (gesture.mode === "pinch") {
      event.preventDefault();
      updatePinch(event.currentTarget);
      return;
    }
    if (
      event.pointerId !== gesture.primaryPointerId ||
      gesture.mode === "scroll"
    ) {
      return;
    }

    const deltaX = event.clientX - gesture.startX;
    const deltaY = event.clientY - gesture.startY;
    if (gesture.mode === "pending") {
      if (gesture.pointerType === "touch") {
        const classification = classifyTouchGesture({
          maximumTouchCount: gesture.maximumTouchCount,
          deltaX,
          deltaY,
        });
        if (classification === "tap") {
          return;
        }
        if (classification === "scroll") {
          gesture.mode = "scroll";
          return;
        }
        if (classification !== "scrub") {
          return;
        }
        gesture.mode = "scrub";
        setScrubbing(true);
      } else if (classifyMouseGesture(deltaX, deltaY) === "click") {
        return;
      } else {
        gesture.mode = "pan";
      }
      capturePointer(event.currentTarget, event.pointerId);
    }

    event.preventDefault();
    if (gesture.mode === "scrub") {
      scrubAtClientX(event.clientX, event.currentTarget, gesture);
      return;
    }
    const plotWidth = Math.max(
      1,
      event.currentTarget.getBoundingClientRect().width *
        ((PLOT_RIGHT - PLOT_LEFT) / CHART_WIDTH),
    );
    const startingSpan =
      gesture.startViewport.end - gesture.startViewport.start;
    applyViewport(
      panViewport(
        gesture.startViewport,
        (-deltaX / plotWidth) * startingSpan,
      ),
    );
  }

  function releaseGraphPointer(
    event: ReactPointerEvent<HTMLDivElement>,
  ) {
    activePointersRef.current.delete(event.pointerId);
    releasePointer(event.currentTarget, event.pointerId);
  }

  function handleGraphPointerUp(event: ReactPointerEvent<HTMLDivElement>) {
    const gesture = chartGestureRef.current;
    if (!gesture || !activePointersRef.current.has(event.pointerId)) {
      return;
    }
    const deltaX = event.clientX - gesture.startX;
    const deltaY = event.clientY - gesture.startY;
    releaseGraphPointer(event);

    if (
      gesture.mode === "pinch" ||
      gesture.maximumTouchCount >= 2
    ) {
      setScrubbing(false);
      if (activePointersRef.current.size === 0) {
        chartGestureRef.current = null;
      }
      return;
    }
    if (event.pointerId !== gesture.primaryPointerId) {
      return;
    }

    const touchGesture =
      gesture.pointerType === "touch"
        ? gesture.mode === "scrub"
          ? "scrub"
          : gesture.mode === "scroll"
            ? "scroll"
            : classifyTouchGesture({
                maximumTouchCount: gesture.maximumTouchCount,
                deltaX,
                deltaY,
              })
        : null;
    const opensSession =
      gesture.pointerType === "touch"
        ? touchGesture !== null && touchGestureOpensSession(touchGesture)
        : gesture.mode === "pending" &&
          classifyMouseGesture(deltaX, deltaY) === "click";
    const scrubbedSession =
      gesture.mode === "scrub"
        ? scrubAtClientX(event.clientX, event.currentTarget, gesture)
        : undefined;
    chartGestureRef.current = null;
    setScrubbing(false);
    if (gesture.pointerType !== "touch") {
      setHovered(event.currentTarget.matches(":hover"));
    }
    if (opensSession) {
      if (scrubbedSession) {
        event.currentTarget.focus({ preventScroll: true });
        onSessionOpen(scrubbedSession.session_key);
      } else {
        activateAtClientX(event.clientX, event.currentTarget, true);
      }
    }
  }

  function handleGraphPointerCancel(
    event: ReactPointerEvent<HTMLDivElement>,
  ) {
    releaseGraphPointer(event);
    if (activePointersRef.current.size === 0) {
      chartGestureRef.current = null;
    }
    setScrubbing(false);
    if (event.pointerType === "touch") {
      setHovered(false);
    } else {
      setHovered(event.currentTarget.matches(":hover"));
    }
  }

  function handleGraphLostPointerCapture(
    event: ReactPointerEvent<HTMLDivElement>,
  ) {
    if (!activePointersRef.current.has(event.pointerId)) {
      return;
    }
    activePointersRef.current.delete(event.pointerId);
    chartGestureRef.current = null;
    setScrubbing(false);
  }

  function beginNavigatorGesture(
    event: ReactPointerEvent<HTMLDivElement>,
    mode: "pan" | NavigatorViewportEdge,
  ) {
    if (event.pointerType !== "touch" && event.button !== 0) {
      return;
    }
    event.stopPropagation();
    navigatorGestureRef.current = {
      pointerId: event.pointerId,
      pointerType: event.pointerType,
      mode,
      startX: event.clientX,
      startY: event.clientY,
      startViewport: viewportRef.current,
      committed: false,
      scrolling: false,
    };
    capturePointer(event.currentTarget, event.pointerId);
    if (event.pointerType !== "touch") {
      event.preventDefault();
    }
  }

  function handleNavigatorPointerMove(
    event: ReactPointerEvent<HTMLDivElement>,
  ) {
    const gesture = navigatorGestureRef.current;
    if (
      !gesture ||
      gesture.pointerId !== event.pointerId ||
      gesture.scrolling
    ) {
      return;
    }
    const deltaX = event.clientX - gesture.startX;
    const deltaY = event.clientY - gesture.startY;
    if (!gesture.committed) {
      if (gesture.pointerType === "touch") {
        const classification = classifyTouchGesture({
          maximumTouchCount: 1,
          deltaX,
          deltaY,
        });
        if (classification === "tap") {
          return;
        }
        if (classification === "scroll") {
          gesture.scrolling = true;
          releasePointer(event.currentTarget, event.pointerId);
          return;
        }
        if (classification !== "scrub") {
          return;
        }
      } else if (classifyMouseGesture(deltaX, deltaY) === "click") {
        return;
      }
      gesture.committed = true;
    }

    event.preventDefault();
    const navigator = navigatorRef.current;
    if (!navigator) {
      return;
    }
    const plotWidth = Math.max(
      1,
      navigator.getBoundingClientRect().width *
        ((PLOT_RIGHT - PLOT_LEFT) / CHART_WIDTH),
    );
    const deltaOuterPosition = deltaX / plotWidth;
    if (gesture.mode === "pan") {
      applyViewport(
        dragNavigatorViewport(
          gesture.startViewport,
          deltaOuterPosition,
        ),
      );
      return;
    }
    const startingEdge =
      gesture.mode === "start"
        ? gesture.startViewport.start
        : gesture.startViewport.end;
    applyViewport(
      resizeNavigatorViewport(
        gesture.startViewport,
        gesture.mode,
        startingEdge + deltaOuterPosition,
      ),
    );
  }

  function endNavigatorGesture(event: ReactPointerEvent<HTMLDivElement>) {
    const gesture = navigatorGestureRef.current;
    if (!gesture || gesture.pointerId !== event.pointerId) {
      return;
    }
    navigatorGestureRef.current = null;
    releasePointer(event.currentTarget, event.pointerId);
  }

  function handleNavigatorKeyDown(
    event: KeyboardEvent<HTMLDivElement>,
    mode: "pan" | NavigatorViewportEdge,
  ) {
    if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") {
      return;
    }
    event.preventDefault();
    const direction = event.key === "ArrowLeft" ? -1 : 1;
    const current = viewportRef.current;
    const span = current.end - current.start;
    const step = event.shiftKey ? 0.05 : Math.max(0.01, span * 0.1);
    if (mode === "pan") {
      applyViewport(dragNavigatorViewport(current, direction * step));
      return;
    }
    applyViewport(
      resizeNavigatorViewport(
        current,
        mode,
        (mode === "start" ? current.start : current.end) +
          direction * step,
      ),
    );
  }

  function navigatorPoint(session: DatedSession): { x: number; y: number } {
    const outerPosition =
      plottedPositionBySessionKey.get(session.session_key) ??
      isoDateToOuterPosition(
        session.performed_at,
        outerRange.startDate,
        outerRange.endDate,
      );
    const x =
      PLOT_LEFT +
      outerPosition *
        (PLOT_RIGHT - PLOT_LEFT);
    const value =
      metricType !== null &&
      session.performance_metric?.metric_type === metricType &&
      metricScale !== null
        ? session.performance_metric.value
        : null;
    const y =
      value === null || metricScale === null
        ? (NAVIGATOR_LINE_TOP + NAVIGATOR_LINE_BOTTOM) / 2
        : NAVIGATOR_LINE_BOTTOM -
          performanceMetricPosition(value, metricScale) *
            (NAVIGATOR_LINE_BOTTOM - NAVIGATOR_LINE_TOP);
    return { x, y };
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
  const navigatorStartX =
    PLOT_LEFT + viewport.start * (PLOT_RIGHT - PLOT_LEFT);
  const navigatorEndX =
    PLOT_LEFT + viewport.end * (PLOT_RIGHT - PLOT_LEFT);
  const navigatorValueText = `${formatHistoryDate(
    visibleStartDate,
    true,
  )} to ${formatHistoryDate(visibleEndDate, true)}`;

  return (
    <section className="min-w-0 overflow-hidden rounded-2xl bg-surface ring-1 ring-border">
      <div className="relative">
        <div
          ref={graphControlRef}
          aria-describedby={instructionsId}
          aria-label={`${exercise.exercise_name} performance graph`}
          aria-valuemax={sessions.length}
          aria-valuemin={1}
          aria-valuenow={activeIndex + 1}
          aria-valuetext={timelinePointLabel(
            exercise.exercise_name,
            activeSession,
          )}
          className={`relative h-[27rem] min-w-0 touch-pan-y select-none overflow-hidden bg-surface-subtle outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-focus-subtle sm:h-[32rem] lg:h-[38rem] ${
            isFitted ? "cursor-crosshair" : "cursor-grab active:cursor-grabbing"
          }`}
          onBlur={() => setFocused(false)}
          onFocus={() => setFocused(true)}
          onKeyDown={handleGraphKeyDown}
          onLostPointerCapture={handleGraphLostPointerCapture}
          onPointerCancel={handleGraphPointerCancel}
          onPointerDown={handleGraphPointerDown}
          onPointerLeave={(event) => {
            if (
              event.pointerType !== "touch" &&
              !activePointersRef.current.has(event.pointerId)
            ) {
              setHovered(false);
            }
          }}
          onPointerMove={handleGraphPointerMove}
          onPointerUp={handleGraphPointerUp}
          role="slider"
          tabIndex={0}
        >
        <span id={instructionsId} className="sr-only">
          Use Left and Right arrow keys to move between recorded sessions.
          Press Enter to open the selected session. Use Plus and Minus to zoom,
          press 0 to fit the full range, or use Control or Command plus the
          mouse wheel to zoom.
        </span>

        <svg
          aria-hidden="true"
          className="absolute inset-0 h-full w-full"
          preserveAspectRatio="none"
          viewBox={`0 0 ${CHART_WIDTH} ${CHART_HEIGHT}`}
        >
          <defs>
            <clipPath id={clipPathId}>
              <rect
                x={PLOT_LEFT}
                y={PLOT_TOP}
                width={PLOT_RIGHT - PLOT_LEFT}
                height={EFFORT_BOTTOM - PLOT_TOP}
              />
            </clipPath>
          </defs>
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
              isoDateToViewportPosition(
                phase.start_date,
                outerRange.startDate,
                outerRange.endDate,
                viewport,
              ) *
                (PLOT_RIGHT - PLOT_LEFT);
            const end =
              PLOT_LEFT +
              isoDateToViewportPosition(
                phase.end_date,
                outerRange.startDate,
                outerRange.endDate,
                viewport,
              ) *
                (PLOT_RIGHT - PLOT_LEFT);
            return (
              <rect
                key={`${phase.code}-${phase.start_session_key}-${index}`}
                x={start}
                y={PLOT_TOP}
                width={Math.max(0, end - start)}
                height={PLOT_BOTTOM - PLOT_TOP}
                clipPath={`url(#${clipPathId})`}
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
              isoDateToViewportPosition(
                tick,
                outerRange.startDate,
                outerRange.endDate,
                viewport,
              ) *
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
                clipPath={`url(#${clipPathId})`}
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
                  sessionViewportPosition(session) *
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
                  clipPath={`url(#${clipPathId})`}
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
                clipPath={`url(#${clipPathId})`}
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
            clipPath={`url(#${clipPathId})`}
            className="fill-action-primary"
            opacity="0.07"
          />
          <line
            x1={latestPoint.x}
            x2={latestPoint.x}
            y1={PLOT_TOP}
            y2={EFFORT_BOTTOM}
            clipPath={`url(#${clipPathId})`}
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
              clipPath={`url(#${clipPathId})`}
              className="stroke-text-strong"
              strokeDasharray="3 4"
              strokeWidth="1"
              vectorEffect="non-scaling-stroke"
            />
          ) : null}
        </svg>

        <div
          aria-hidden="true"
          className="type-chart-metadata pointer-events-none absolute left-1 top-3 font-semibold uppercase tracking-[0.08em] text-text-secondary sm:left-3"
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
              className="type-chart-metadata pointer-events-none absolute left-1 -translate-y-1/2 tabular-nums text-text-muted sm:left-3"
              style={{ top: `${(y / CHART_HEIGHT) * 100}%` }}
            >
              {formatHistoryNumber(tick)}
            </span>
          );
        })}

        <span
          aria-hidden="true"
          className="type-chart-metadata pointer-events-none absolute left-1 font-semibold uppercase tracking-[0.08em] text-text-secondary sm:left-3"
          style={{ top: `${(EFFORT_TOP / CHART_HEIGHT) * 100}%` }}
        >
          RIR
        </span>

        {calendarTicks.map((tick, index) => {
          const position = isoDateToViewportPosition(
            tick,
            outerRange.startDate,
            outerRange.endDate,
            viewport,
          );
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
              className="type-chart-metadata pointer-events-none absolute whitespace-nowrap text-text-secondary"
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
              visibleStartDate,
              visibleEndDate,
              plotPixelWidth,
            )
          ) {
            return null;
          }
          const start = isoDateToViewportPosition(
            phase.start_date,
            outerRange.startDate,
            outerRange.endDate,
            viewport,
            true,
          );
          const end = isoDateToViewportPosition(
            phase.end_date,
            outerRange.startDate,
            outerRange.endDate,
            viewport,
            true,
          );
          const left =
            PLOT_LEFT + start * (PLOT_RIGHT - PLOT_LEFT);
          const width = (end - start) * (PLOT_RIGHT - PLOT_LEFT);
          return (
            <span
              key={`${phase.code}-${index}`}
              aria-hidden="true"
              className="type-chart-metadata pointer-events-none absolute truncate px-2 pt-2 font-semibold text-text-secondary"
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
          <span
            aria-hidden="true"
            className="pointer-events-none absolute z-10 h-4 w-4 -translate-x-1/2 -translate-y-1/2 rounded-full bg-surface shadow-sm ring-2 ring-action-primary after:absolute after:inset-[0.3rem] after:rounded-full after:bg-action-primary"
            style={{
              left: `${(activePoint.x / CHART_WIDTH) * 100}%`,
              top: `${(activePoint.y / CHART_HEIGHT) * 100}%`,
            }}
          />
        ) : null}

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
      </div>

      <div className="border-t border-border-subtle bg-surface px-0 py-2">
        <div
          ref={navigatorRef}
          aria-label="Complete performance range navigator"
          className="relative min-w-0 touch-pan-y select-none overflow-hidden"
          style={{ height: `${NAVIGATOR_HEIGHT}px` }}
        >
          <svg
            aria-hidden="true"
            className="absolute inset-0 h-full w-full"
            preserveAspectRatio="none"
            viewBox={`0 0 ${CHART_WIDTH} ${NAVIGATOR_HEIGHT}`}
          >
            <rect
              x={PLOT_LEFT}
              y={NAVIGATOR_LINE_TOP}
              width={PLOT_RIGHT - PLOT_LEFT}
              height={NAVIGATOR_LINE_BOTTOM - NAVIGATOR_LINE_TOP}
              rx="5"
              className="fill-surface-subtle"
            />
            {metricRuns.map((run, index) => {
              const points = run
                .map((sessionKey) => sessionByKey.get(sessionKey)?.session)
                .filter(
                  (session): session is DatedSession =>
                    session !== undefined,
                )
                .map((session) => {
                  const point = navigatorPoint(session);
                  return `${point.x},${point.y}`;
                });
              return points.length >= 2 ? (
                <polyline
                  key={`navigator-${run[0]}-${index}`}
                  fill="none"
                  points={points.join(" ")}
                  className="stroke-action-primary"
                  opacity="0.48"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  vectorEffect="non-scaling-stroke"
                />
              ) : null;
            })}
          </svg>

          <span
            aria-hidden="true"
            className="pointer-events-none absolute bottom-[12px] top-[12px] bg-surface/70"
            style={{
              left: `${(PLOT_LEFT / CHART_WIDTH) * 100}%`,
              width: `${((navigatorStartX - PLOT_LEFT) / CHART_WIDTH) * 100}%`,
            }}
          />
          <span
            aria-hidden="true"
            className="pointer-events-none absolute bottom-[12px] top-[12px] bg-surface/70"
            style={{
              left: `${(navigatorEndX / CHART_WIDTH) * 100}%`,
              width: `${((PLOT_RIGHT - navigatorEndX) / CHART_WIDTH) * 100}%`,
            }}
          />
          <span
            aria-hidden="true"
            className="pointer-events-none absolute bottom-[9px] top-[9px] z-10 rounded-md border-2 border-action-primary/70 bg-action-primary/5"
            style={{
              left: `${(navigatorStartX / CHART_WIDTH) * 100}%`,
              width: `${((navigatorEndX - navigatorStartX) / CHART_WIDTH) * 100}%`,
            }}
          />
          <div
            aria-label="Pan visible date range"
            aria-valuemax={100}
            aria-valuemin={0}
            aria-valuenow={Math.round(viewport.start * 100)}
            aria-valuetext={navigatorValueText}
            className="absolute top-6 z-20 h-6 -translate-x-1/2 cursor-grab rounded-md outline-none active:cursor-grabbing focus-visible:ring-2 focus-visible:ring-focus-subtle"
            onKeyDown={(event) =>
              handleNavigatorKeyDown(event, "pan")
            }
            onLostPointerCapture={endNavigatorGesture}
            onPointerCancel={endNavigatorGesture}
            onPointerDown={(event) =>
              beginNavigatorGesture(event, "pan")
            }
            onPointerMove={handleNavigatorPointerMove}
            onPointerUp={endNavigatorGesture}
            role="slider"
            style={{
              left: `${(((navigatorStartX + navigatorEndX) / 2) / CHART_WIDTH) * 100}%`,
              minWidth: `${MIN_NAVIGATOR_PAN_TARGET_PIXELS}px`,
              width: `${((navigatorEndX - navigatorStartX) / CHART_WIDTH) * 100}%`,
            }}
            tabIndex={0}
          />
          <div
            aria-label="Resize visible date range start"
            aria-valuemax={Math.round(viewport.end * 100)}
            aria-valuemin={0}
            aria-valuenow={Math.round(viewport.start * 100)}
            aria-valuetext={formatHistoryDate(visibleStartDate, true)}
            className="absolute top-0 z-20 flex h-6 w-11 -translate-x-1/2 touch-pan-y cursor-ew-resize items-center justify-center rounded-md outline-none focus-visible:ring-2 focus-visible:ring-focus-subtle"
            onKeyDown={(event) =>
              handleNavigatorKeyDown(event, "start")
            }
            onLostPointerCapture={endNavigatorGesture}
            onPointerCancel={endNavigatorGesture}
            onPointerDown={(event) =>
              beginNavigatorGesture(event, "start")
            }
            onPointerMove={handleNavigatorPointerMove}
            onPointerUp={endNavigatorGesture}
            role="slider"
            style={{
              left: `${(navigatorStartX / CHART_WIDTH) * 100}%`,
            }}
            tabIndex={0}
          >
            <span className="h-4 w-1 rounded-full bg-action-primary/80" />
          </div>
          <div
            aria-label="Resize visible date range end"
            aria-valuemax={100}
            aria-valuemin={Math.round(viewport.start * 100)}
            aria-valuenow={Math.round(viewport.end * 100)}
            aria-valuetext={formatHistoryDate(visibleEndDate, true)}
            className="absolute bottom-0 z-20 flex h-6 w-11 -translate-x-1/2 touch-pan-y cursor-ew-resize items-center justify-center rounded-md outline-none focus-visible:ring-2 focus-visible:ring-focus-subtle"
            onKeyDown={(event) =>
              handleNavigatorKeyDown(event, "end")
            }
            onLostPointerCapture={endNavigatorGesture}
            onPointerCancel={endNavigatorGesture}
            onPointerDown={(event) =>
              beginNavigatorGesture(event, "end")
            }
            onPointerMove={handleNavigatorPointerMove}
            onPointerUp={endNavigatorGesture}
            role="slider"
            style={{
              left: `${(navigatorEndX / CHART_WIDTH) * 100}%`,
            }}
            tabIndex={0}
          >
            <span className="h-4 w-1 rounded-full bg-action-primary/80" />
          </div>
        </div>
      </div>
    </section>
  );
}

function FocusedSessionDetail({
  exercise,
  summary,
  detailResult,
  canMovePrevious,
  canMoveNext,
  onMoveSession,
}: {
  exercise: ExerciseHistoryAnalyticsSummary | undefined;
  summary: ExerciseHistoryRecentSession | undefined;
  detailResult: WorkoutExerciseHistorySessionDetailApiResult | null;
  canMovePrevious: boolean;
  canMoveNext: boolean;
  onMoveSession: (direction: -1 | 1) => void;
}) {
  if (!exercise || !summary) {
    return (
      <p className="text-sm text-text-secondary">
        The selected session is unavailable.
      </p>
    );
  }

  const handleKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    if (event.key === "ArrowLeft" && canMovePrevious) {
      event.preventDefault();
      onMoveSession(-1);
    } else if (event.key === "ArrowRight" && canMoveNext) {
      event.preventDefault();
      onMoveSession(1);
    }
  };
  const navigation = (
    <SessionDetailNavigation
      canMoveNext={canMoveNext}
      canMovePrevious={canMovePrevious}
      onMoveSession={onMoveSession}
    />
  );

  if (detailResult === null) {
    return (
      <div onKeyDown={handleKeyDown}>
        {navigation}
        <DetailHeading session={summary} />
        <p className="mt-4 text-sm text-text-secondary">
          Loading recorded sets…
        </p>
      </div>
    );
  }
  if (detailResult.error || !detailResult.data) {
    return (
      <div onKeyDown={handleKeyDown}>
        {navigation}
        <DetailHeading session={summary} />
        <p className="mt-4 rounded-xl bg-danger-surface px-3 py-3 text-sm text-danger-foreground">
          {detailResult.error?.message ?? "Session details are unavailable."}
        </p>
      </div>
    );
  }
  return (
    <div onKeyDown={handleKeyDown}>
      {navigation}
      <SessionDetail
        exercise={exercise}
        session={detailResult.data.session}
      />
    </div>
  );
}

function SessionDetailNavigation({
  canMovePrevious,
  canMoveNext,
  onMoveSession,
}: {
  canMovePrevious: boolean;
  canMoveNext: boolean;
  onMoveSession: (direction: -1 | 1) => void;
}) {
  return (
    <div
      aria-label="Session navigation"
      className="mb-4 grid grid-cols-2 gap-2"
      role="group"
    >
      <button
        type="button"
        disabled={!canMovePrevious}
        onClick={() => onMoveSession(-1)}
        className="min-h-10 rounded-xl border border-border bg-surface px-3 py-2 text-sm font-semibold text-text-primary transition hover:bg-surface-muted disabled:cursor-not-allowed disabled:opacity-45"
      >
        Previous
      </button>
      <button
        type="button"
        disabled={!canMoveNext}
        onClick={() => onMoveSession(1)}
        className="min-h-10 rounded-xl border border-border bg-surface px-3 py-2 text-sm font-semibold text-text-primary transition hover:bg-surface-muted disabled:cursor-not-allowed disabled:opacity-45"
      >
        Next
      </button>
    </div>
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
      <p className="type-compact-metadata font-semibold uppercase tracking-[0.1em] text-text-muted">
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
  return chronologicalDatedSessions(sessions).at(-1);
}

function chronologicalDatedSessions(
  sessions: ExerciseHistoryRecentSession[],
): DatedSession[] {
  const dated = sessions.flatMap((session, sourceIndex) =>
    session.performed_at === null
      ? []
      : [{ session: session as DatedSession, sourceIndex }],
  );
  return dated
    .sort(
      (left, right) =>
        left.session.performed_at.localeCompare(
          right.session.performed_at,
        ) || right.sourceIndex - left.sourceIndex,
    )
    .map((entry) => entry.session);
}

function localIsoDate(date = new Date()): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function plotPositionFromClientX(
  clientX: number,
  element: HTMLElement,
): number {
  const bounds = element.getBoundingClientRect();
  const viewX =
    ((clientX - bounds.left) / Math.max(bounds.width, 1)) * CHART_WIDTH;
  return Math.min(
    1,
    Math.max(0, (viewX - PLOT_LEFT) / (PLOT_RIGHT - PLOT_LEFT)),
  );
}

function capturePointer(element: HTMLElement, pointerId: number) {
  if (element.hasPointerCapture(pointerId)) {
    return;
  }
  try {
    element.setPointerCapture(pointerId);
  } catch {
    return;
  }
}

function releasePointer(element: HTMLElement, pointerId: number) {
  if (!element.hasPointerCapture(pointerId)) {
    return;
  }
  try {
    element.releasePointerCapture(pointerId);
  } catch {
    return;
  }
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
