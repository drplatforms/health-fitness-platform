const OUTER_DOMAIN_START = 0;
const OUTER_DOMAIN_END = 1;
const DAY_IN_MILLISECONDS = 86_400_000;
const TRANSFORM_MINIMUM_SPAN = Number.EPSILON * 16;

export const DEFAULT_MIN_VIEWPORT_SPAN = 1 / 32;
export const DEFAULT_MOUSE_DRAG_THRESHOLD = 6;
export const DEFAULT_TOUCH_MOVEMENT_THRESHOLD = 8;
export const MIN_NAVIGATOR_PAN_TARGET_PIXELS = 44;

export interface PerformanceViewport {
  start: number;
  end: number;
}

export interface IsoDateRange {
  startDate: string;
  endDate: string;
}

export interface SessionIndexRange {
  startIndex: number;
  endIndex: number;
}

export type NavigatorViewportEdge = "start" | "end";
export type MouseGesture = "click" | "drag";
export type TouchGesture = "tap" | "scrub" | "scroll" | "pinch";

export interface TouchGestureMeasurement {
  maximumTouchCount: number;
  deltaX: number;
  deltaY: number;
  movementThreshold?: number;
  horizontalDominance?: number;
}

export function fitViewport(): PerformanceViewport {
  return { start: OUTER_DOMAIN_START, end: OUTER_DOMAIN_END };
}

export function clampViewport(
  viewport: PerformanceViewport,
  minimumSpan = DEFAULT_MIN_VIEWPORT_SPAN,
): PerformanceViewport {
  const safeMinimumSpan = normalizeMinimumSpan(minimumSpan);
  if (!Number.isFinite(viewport.start) || !Number.isFinite(viewport.end)) {
    return fitViewport();
  }

  const lower = Math.min(viewport.start, viewport.end);
  const upper = Math.max(viewport.start, viewport.end);
  if (
    lower >= OUTER_DOMAIN_START &&
    upper <= OUTER_DOMAIN_END &&
    upper - lower >= safeMinimumSpan
  ) {
    return { start: lower, end: upper };
  }

  const center = (lower + upper) / 2;
  const span = Math.max(safeMinimumSpan, upper - lower);
  if (span >= OUTER_DOMAIN_END - OUTER_DOMAIN_START) {
    return fitViewport();
  }

  let start = center - span / 2;
  let end = center + span / 2;
  if (start < OUTER_DOMAIN_START) {
    end += OUTER_DOMAIN_START - start;
    start = OUTER_DOMAIN_START;
  }
  if (end > OUTER_DOMAIN_END) {
    start -= end - OUTER_DOMAIN_END;
    end = OUTER_DOMAIN_END;
  }

  return {
    start: clampUnitPosition(start),
    end: clampUnitPosition(end),
  };
}

export function zoomViewport(
  viewport: PerformanceViewport,
  zoomFactor: number,
  anchorOuterPosition: number,
  minimumSpan = DEFAULT_MIN_VIEWPORT_SPAN,
): PerformanceViewport {
  const current = clampViewport(viewport, minimumSpan);
  if (!Number.isFinite(zoomFactor) || zoomFactor <= 0) {
    return current;
  }

  const currentSpan = current.end - current.start;
  const nextSpan = Math.min(
    1,
    Math.max(normalizeMinimumSpan(minimumSpan), currentSpan / zoomFactor),
  );
  if (nextSpan >= 1) {
    return fitViewport();
  }

  const anchor = Number.isFinite(anchorOuterPosition)
    ? clampNumber(anchorOuterPosition, current.start, current.end)
    : (current.start + current.end) / 2;
  const anchorFraction = (anchor - current.start) / currentSpan;
  const nextStart = anchor - anchorFraction * nextSpan;
  return clampViewport(
    { start: nextStart, end: nextStart + nextSpan },
    minimumSpan,
  );
}

export function pinchZoomViewport(
  viewport: PerformanceViewport,
  zoomFactor: number,
  anchorOuterPosition: number,
  gestureCenterViewportPosition: number,
  minimumSpan = DEFAULT_MIN_VIEWPORT_SPAN,
): PerformanceViewport {
  const zoomed = zoomViewport(
    viewport,
    zoomFactor,
    anchorOuterPosition,
    minimumSpan,
  );
  const span = zoomed.end - zoomed.start;
  const anchorViewportPosition = outerToViewportPosition(
    anchorOuterPosition,
    zoomed,
  );
  return panViewport(
    zoomed,
    (anchorViewportPosition -
      clampUnitPosition(gestureCenterViewportPosition)) *
      span,
    minimumSpan,
  );
}

export function panViewport(
  viewport: PerformanceViewport,
  deltaOuterPosition: number,
  minimumSpan = DEFAULT_MIN_VIEWPORT_SPAN,
): PerformanceViewport {
  const current = clampViewport(viewport, minimumSpan);
  if (!Number.isFinite(deltaOuterPosition) || deltaOuterPosition === 0) {
    return current;
  }

  const span = current.end - current.start;
  const start = clampNumber(
    current.start + deltaOuterPosition,
    OUTER_DOMAIN_START,
    OUTER_DOMAIN_END - span,
  );
  return { start, end: start + span };
}

export function revealOuterPosition(
  viewport: PerformanceViewport,
  outerPosition: number,
  paddingFraction = 0,
  minimumSpan = DEFAULT_MIN_VIEWPORT_SPAN,
): PerformanceViewport {
  const current = clampViewport(viewport, minimumSpan);
  if (!Number.isFinite(outerPosition)) {
    return current;
  }

  const position = clampUnitPosition(outerPosition);
  const span = current.end - current.start;
  const padding = clampNumber(
    Number.isFinite(paddingFraction) ? paddingFraction : 0,
    0,
    0.5,
  );
  const gutter = span * padding;
  const visibleStart = current.start + gutter;
  const visibleEnd = current.end - gutter;

  if (position < visibleStart) {
    return panViewport(
      current,
      position - visibleStart,
      minimumSpan,
    );
  }
  if (position > visibleEnd) {
    return panViewport(
      current,
      position - visibleEnd,
      minimumSpan,
    );
  }
  return current;
}

export function outerToViewportPosition(
  outerPosition: number,
  viewport: PerformanceViewport,
  clampResult = false,
): number {
  const current = clampViewport(viewport, TRANSFORM_MINIMUM_SPAN);
  const result =
    (outerPosition - current.start) / (current.end - current.start);
  return clampResult ? clampUnitPosition(result) : result;
}

export function viewportToOuterPosition(
  viewportPosition: number,
  viewport: PerformanceViewport,
  clampInput = false,
): number {
  const current = clampViewport(viewport, TRANSFORM_MINIMUM_SPAN);
  const position = clampInput
    ? clampUnitPosition(viewportPosition)
    : viewportPosition;
  return current.start + position * (current.end - current.start);
}

export function visibleSessionIndexRange(
  outerPositions: readonly number[],
  viewport: PerformanceViewport,
): SessionIndexRange {
  const current = clampViewport(viewport, TRANSFORM_MINIMUM_SPAN);
  const tolerance = Number.EPSILON * 8;
  let low = 0;
  let high = outerPositions.length;
  while (low < high) {
    const middle = Math.floor((low + high) / 2);
    if (outerPositions[middle] < current.start - tolerance) {
      low = middle + 1;
    } else {
      high = middle;
    }
  }
  const startIndex = low;
  high = outerPositions.length;
  while (low < high) {
    const middle = Math.floor((low + high) / 2);
    if (outerPositions[middle] <= current.end + tolerance) {
      low = middle + 1;
    } else {
      high = middle;
    }
  }
  return { startIndex, endIndex: low };
}

export function spreadCoincidentSessionPositions(
  outerPositions: readonly number[],
  requestedSeparation: number,
  maximumGroupWidth = Number.POSITIVE_INFINITY,
): number[] {
  const result = [...outerPositions];
  const separation =
    Number.isFinite(requestedSeparation) && requestedSeparation > 0
      ? requestedSeparation
      : 0;
  let groupStart = 0;
  while (groupStart < outerPositions.length) {
    let groupEnd = groupStart + 1;
    while (
      groupEnd < outerPositions.length &&
      outerPositions[groupEnd] === outerPositions[groupStart]
    ) {
      groupEnd += 1;
    }
    const count = groupEnd - groupStart;
    if (count > 1 && separation > 0) {
      const center = outerPositions[groupStart];
      const leftBoundary =
        groupStart > 0
          ? (outerPositions[groupStart - 1] + center) / 2
          : OUTER_DOMAIN_START;
      const rightBoundary =
        groupEnd < outerPositions.length
          ? (center + outerPositions[groupEnd]) / 2
          : OUTER_DOMAIN_END;
      const availableWidth = Math.max(0, rightBoundary - leftBoundary);
      const boundedGroupWidth =
        Number.isFinite(maximumGroupWidth) && maximumGroupWidth >= 0
          ? maximumGroupWidth
          : Number.POSITIVE_INFINITY;
      const spacing = Math.min(
        separation,
        availableWidth / count,
        boundedGroupWidth / (count - 1),
      );
      const groupWidth = spacing * (count - 1);
      const firstPosition = clampNumber(
        center - groupWidth / 2,
        leftBoundary,
        rightBoundary - groupWidth,
      );
      for (let index = 0; index < count; index += 1) {
        result[groupStart + index] = clampUnitPosition(
          firstPosition + index * spacing,
        );
      }
    }
    groupStart = groupEnd;
  }
  return result;
}

export function activeSelectionIndicatorsVisible(
  hovered: boolean,
  focused: boolean,
  detailOpen: boolean,
  scrubbing = false,
): boolean {
  return hovered || focused || detailOpen || scrubbing;
}

export function sessionTraversalIndices(
  fromIndex: number,
  toIndex: number,
  sessionCount: number,
): number[] {
  if (sessionCount <= 0) {
    return [];
  }
  const start = Math.min(
    sessionCount - 1,
    Math.max(0, Math.floor(fromIndex)),
  );
  const end = Math.min(
    sessionCount - 1,
    Math.max(0, Math.floor(toIndex)),
  );
  const direction = end >= start ? 1 : -1;
  return Array.from(
    { length: Math.abs(end - start) + 1 },
    (_, offset) => start + offset * direction,
  );
}

export function touchGestureOpensSession(gesture: TouchGesture): boolean {
  return gesture === "tap" || gesture === "scrub";
}

export function dragNavigatorViewport(
  viewport: PerformanceViewport,
  deltaOuterPosition: number,
  minimumSpan = DEFAULT_MIN_VIEWPORT_SPAN,
): PerformanceViewport {
  return panViewport(viewport, deltaOuterPosition, minimumSpan);
}

export function resizeNavigatorViewport(
  viewport: PerformanceViewport,
  edge: NavigatorViewportEdge,
  edgeOuterPosition: number,
  minimumSpan = DEFAULT_MIN_VIEWPORT_SPAN,
): PerformanceViewport {
  const safeMinimumSpan = normalizeMinimumSpan(minimumSpan);
  const current = clampViewport(viewport, safeMinimumSpan);
  if (!Number.isFinite(edgeOuterPosition)) {
    return current;
  }

  if (edge === "start") {
    return {
      start: clampNumber(
        edgeOuterPosition,
        OUTER_DOMAIN_START,
        current.end - safeMinimumSpan,
      ),
      end: current.end,
    };
  }
  return {
    start: current.start,
    end: clampNumber(
      edgeOuterPosition,
      current.start + safeMinimumSpan,
      OUTER_DOMAIN_END,
    ),
  };
}

export function classifyMouseGesture(
  deltaX: number,
  deltaY: number,
  movementThreshold = DEFAULT_MOUSE_DRAG_THRESHOLD,
): MouseGesture {
  const distance = Math.hypot(finiteOrZero(deltaX), finiteOrZero(deltaY));
  return distance >= normalizeThreshold(
    movementThreshold,
    DEFAULT_MOUSE_DRAG_THRESHOLD,
  )
    ? "drag"
    : "click";
}

export function classifyTouchGesture({
  maximumTouchCount,
  deltaX,
  deltaY,
  movementThreshold = DEFAULT_TOUCH_MOVEMENT_THRESHOLD,
  horizontalDominance = 1.15,
}: TouchGestureMeasurement): TouchGesture {
  if (maximumTouchCount >= 2) {
    return "pinch";
  }

  const horizontalDistance = Math.abs(finiteOrZero(deltaX));
  const verticalDistance = Math.abs(finiteOrZero(deltaY));
  const movement = Math.hypot(horizontalDistance, verticalDistance);
  if (
    movement <
    normalizeThreshold(
      movementThreshold,
      DEFAULT_TOUCH_MOVEMENT_THRESHOLD,
    )
  ) {
    return "tap";
  }

  const dominance =
    Number.isFinite(horizontalDominance) && horizontalDominance >= 1
      ? horizontalDominance
      : 1.15;
  return horizontalDistance >= verticalDistance * dominance
    ? "scrub"
    : "scroll";
}

export function isoDateRangeEndingOn(
  endDate: string,
  lookbackDays: number,
): IsoDateRange {
  const end = parseIsoDate(endDate);
  if (!Number.isFinite(end)) {
    return { startDate: endDate, endDate };
  }

  const days = Number.isFinite(lookbackDays)
    ? Math.max(0, Math.floor(lookbackDays))
    : 0;
  return {
    startDate: formatIsoDate(end - days * DAY_IN_MILLISECONDS),
    endDate: formatIsoDate(end),
  };
}

export function isoDateToOuterPosition(
  value: string,
  outerStartDate: string,
  outerEndDate: string,
): number {
  const start = parseIsoDate(outerStartDate);
  const end = parseIsoDate(outerEndDate);
  const current = parseIsoDate(value);
  if (
    !Number.isFinite(start) ||
    !Number.isFinite(end) ||
    !Number.isFinite(current) ||
    end <= start
  ) {
    return 0.5;
  }
  return clampUnitPosition((current - start) / (end - start));
}

export function outerPositionToIsoDate(
  outerPosition: number,
  outerStartDate: string,
  outerEndDate: string,
): string {
  const start = parseIsoDate(outerStartDate);
  const end = parseIsoDate(outerEndDate);
  if (!Number.isFinite(start) || !Number.isFinite(end) || end <= start) {
    return outerStartDate;
  }

  const dayCount = Math.round((end - start) / DAY_IN_MILLISECONDS);
  const dayOffset = Math.round(dayCount * clampUnitPosition(outerPosition));
  return formatIsoDate(start + dayOffset * DAY_IN_MILLISECONDS);
}

export function isoDateToViewportPosition(
  value: string,
  outerStartDate: string,
  outerEndDate: string,
  viewport: PerformanceViewport,
  clampResult = false,
): number {
  return outerToViewportPosition(
    isoDateToOuterPosition(value, outerStartDate, outerEndDate),
    viewport,
    clampResult,
  );
}

export function viewportPositionToIsoDate(
  viewportPosition: number,
  outerStartDate: string,
  outerEndDate: string,
  viewport: PerformanceViewport,
): string {
  return outerPositionToIsoDate(
    viewportToOuterPosition(viewportPosition, viewport),
    outerStartDate,
    outerEndDate,
  );
}

function normalizeMinimumSpan(minimumSpan: number): number {
  if (!Number.isFinite(minimumSpan) || minimumSpan <= 0) {
    return DEFAULT_MIN_VIEWPORT_SPAN;
  }
  return Math.min(1, minimumSpan);
}

function normalizeThreshold(value: number, fallback: number): number {
  return Number.isFinite(value) && value > 0 ? value : fallback;
}

function clampUnitPosition(value: number): number {
  return clampNumber(
    Number.isFinite(value) ? value : OUTER_DOMAIN_START,
    OUTER_DOMAIN_START,
    OUTER_DOMAIN_END,
  );
}

function clampNumber(value: number, minimum: number, maximum: number): number {
  return Math.min(maximum, Math.max(minimum, value));
}

function finiteOrZero(value: number): number {
  return Number.isFinite(value) ? value : 0;
}

function parseIsoDate(value: string): number {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) {
    return Number.NaN;
  }
  const timestamp = Date.parse(`${value}T00:00:00Z`);
  return Number.isFinite(timestamp) && formatIsoDate(timestamp) === value
    ? timestamp
    : Number.NaN;
}

function formatIsoDate(timestamp: number): string {
  return new Date(timestamp).toISOString().slice(0, 10);
}
