import assert from "node:assert/strict";
import test from "node:test";

import { nearestSessionIndex } from "./workoutExerciseHistoryApi.ts";
import {
  activeSelectionIndicatorsVisible,
  clampViewport,
  classifyMouseGesture,
  classifyTouchGesture,
  DEFAULT_MIN_VIEWPORT_SPAN,
  dragNavigatorViewport,
  fitViewport,
  isoDateRangeEndingOn,
  isoDateToOuterPosition,
  isoDateToViewportPosition,
  MIN_NAVIGATOR_PAN_TARGET_PIXELS,
  outerPositionToIsoDate,
  outerToViewportPosition,
  panViewport,
  pinchZoomViewport,
  resizeNavigatorViewport,
  revealOuterPosition,
  sessionTraversalIndices,
  spreadCoincidentSessionPositions,
  touchGestureOpensSession,
  type PerformanceViewport,
  visibleSessionIndexRange,
  viewportPositionToIsoDate,
  viewportToOuterPosition,
  zoomViewport,
} from "./workoutPerformanceViewport.ts";

test("clamps viewports to the outer domain and enforces a minimum span", () => {
  assertViewportClose(
    clampViewport({ start: -0.2, end: 0.2 }, 0.1),
    { start: 0, end: 0.4 },
  );
  assertViewportClose(
    clampViewport({ start: 0.8, end: 1.2 }, 0.1),
    { start: 0.6, end: 1 },
  );
  assertViewportClose(
    clampViewport({ start: 0.52, end: 0.5 }, 0.1),
    { start: 0.46, end: 0.56 },
  );
  assertViewportClose(
    clampViewport({ start: 0.8, end: 0.2 }, 0.1),
    { start: 0.2, end: 0.8 },
  );
  assert.deepEqual(
    clampViewport({ start: Number.NaN, end: 0.4 }),
    fitViewport(),
  );
});

test("fit resets any zoomed viewport to the complete outer range", () => {
  const zoomed = zoomViewport(fitViewport(), 4, 0.5);
  assertViewportClose(zoomed, { start: 0.375, end: 0.625 });
  assert.deepEqual(fitViewport(), { start: 0, end: 1 });
});

test("zooms around the outer-domain anchor and respects zoom limits", () => {
  const anchor = 0.25;
  const before = fitViewport();
  const anchorViewportPosition = outerToViewportPosition(anchor, before);
  const zoomed = zoomViewport(before, 2, anchor, 0.05);

  assertViewportClose(zoomed, { start: 0.125, end: 0.625 });
  assertClose(
    outerToViewportPosition(anchor, zoomed),
    anchorViewportPosition,
  );
  assertViewportClose(
    zoomViewport(zoomed, 100, anchor, 0.1),
    { start: 0.225, end: 0.325 },
  );
  assert.deepEqual(zoomViewport(zoomed, 0.01, anchor), fitViewport());
});

test("pinch zoom keeps the anchor date under the moving gesture center", () => {
  const zoomed = pinchZoomViewport(
    fitViewport(),
    2,
    0.4,
    0.6,
    0.05,
  );

  assertViewportClose(zoomed, { start: 0.1, end: 0.6 });
  assertClose(outerToViewportPosition(0.4, zoomed), 0.6);
});

test("pans without changing span or leaving the outer-domain bounds", () => {
  const viewport = { start: 0.25, end: 0.5 };
  assertViewportClose(panViewport(viewport, 0.1), {
    start: 0.35,
    end: 0.6,
  });
  assertViewportClose(panViewport(viewport, -4), {
    start: 0,
    end: 0.25,
  });
  assertViewportClose(panViewport(viewport, 4), {
    start: 0.75,
    end: 1,
  });
});

test("maps outer and viewport coordinates as inverse linear transforms", () => {
  const viewport = { start: 0.25, end: 0.5 };
  for (const outerPosition of [0.25, 0.375, 0.5]) {
    assertClose(
      viewportToOuterPosition(
        outerToViewportPosition(outerPosition, viewport),
        viewport,
      ),
      outerPosition,
    );
  }

  assert.equal(outerToViewportPosition(0, viewport), -1);
  assert.equal(outerToViewportPosition(0.75, viewport), 2);
  assert.equal(outerToViewportPosition(0, viewport, true), 0);
  assert.equal(outerToViewportPosition(0.75, viewport, true), 1);
  assert.equal(viewportToOuterPosition(-1, viewport), 0);
  assert.equal(viewportToOuterPosition(2, viewport), 0.75);
  assert.equal(viewportToOuterPosition(-1, viewport, true), 0.25);
  assert.equal(viewportToOuterPosition(2, viewport, true), 0.5);
});

test("selects adjacent sessions at their actual midpoint boundaries", () => {
  const positions = [0.1, 0.21, 0.9];
  assert.equal(nearestSessionIndex(positions, 0.154), 0);
  assert.equal(nearestSessionIndex(positions, 0.155), 1);
  assert.equal(nearestSessionIndex(positions, 0.554), 1);
  assert.equal(nearestSessionIndex(positions, 0.555), 2);
  assert.equal(nearestSessionIndex([], 0.5), -1);
});

test("selects every one of 160 dense sessions in a changed viewport", () => {
  const positions = Array.from({ length: 160 }, (_, index) => index / 159);
  const viewport = { start: 0.36, end: 0.44 };
  const maximallyZoomed = zoomViewport(fitViewport(), 10_000, 0.5);

  assertClose(
    maximallyZoomed.end - maximallyZoomed.start,
    DEFAULT_MIN_VIEWPORT_SPAN,
  );
  assert.ok(
    positions.filter(
      (position) =>
        position >= maximallyZoomed.start && position <= maximallyZoomed.end,
    ).length <= 6,
  );

  positions.forEach((position, index) => {
    assert.equal(nearestSessionIndex(positions, position), index);
  });

  for (let index = 58; index <= 68; index += 1) {
    const pointerPosition = outerToViewportPosition(
      positions[index],
      viewport,
    );
    assert.equal(
      nearestSessionIndex(
        positions,
        viewportToOuterPosition(pointerPosition, viewport, true),
      ),
      index,
    );
  }
});

test("selects the nearest visible session at viewport boundaries", () => {
  const positions = [0.35, 0.6];
  const viewport = { start: 0.4, end: 0.8 };
  const range = visibleSessionIndexRange(positions, viewport);

  assert.deepEqual(range, { startIndex: 1, endIndex: 2 });
  assert.equal(
    nearestSessionIndex(
      positions,
      viewportToOuterPosition(0, viewport, true),
      range.startIndex,
      range.endIndex,
    ),
    1,
  );
});

test("spreads same-date sessions minimally so each has a midpoint region", () => {
  const requestedSeparation = 0.2 / 365;
  const positions = spreadCoincidentSessionPositions(
    [0.1, 0.5, 0.5, 0.5, 0.9],
    requestedSeparation,
  );

  assert.equal(positions[0], 0.1);
  assert.equal(positions[4], 0.9);
  assert.ok(positions[1] < positions[2]);
  assert.ok(positions[2] < positions[3]);
  assertClose(positions[2], 0.5);
  for (let index = 1; index <= 3; index += 1) {
    assert.equal(nearestSessionIndex(positions, positions[index]), index);
  }

  const maximumZoomPixelGap =
    ((positions[2] - positions[1]) / (1 / 32)) * 900;
  assert.ok(maximumZoomPixelGap >= 12);

  const crowded = spreadCoincidentSessionPositions(
    Array.from({ length: 10 }, () => 0.5),
    requestedSeparation,
    0.8 / 365,
  );
  assertClose(crowded.at(-1)! - crowded[0], 0.8 / 365);
});

test("reveals an active outer position with the smallest bounded pan", () => {
  const viewport = { start: 0.3, end: 0.5 };
  assert.deepEqual(revealOuterPosition(viewport, 0.4), viewport);
  assertViewportClose(revealOuterPosition(viewport, 0.62), {
    start: 0.42,
    end: 0.62,
  });
  assertViewportClose(revealOuterPosition(viewport, 0.28, 0.1), {
    start: 0.26,
    end: 0.46,
  });
  assertViewportClose(revealOuterPosition(viewport, 1, 0.1), {
    start: 0.8,
    end: 1,
  });
});

test("drags and resizes the navigator viewport within the outer range", () => {
  const viewport = { start: 0.2, end: 0.6 };
  assertViewportClose(dragNavigatorViewport(viewport, 0.25), {
    start: 0.45,
    end: 0.85,
  });
  assertViewportClose(dragNavigatorViewport(viewport, -1), {
    start: 0,
    end: 0.4,
  });
  assertViewportClose(
    resizeNavigatorViewport(viewport, "start", 0.35, 0.1),
    { start: 0.35, end: 0.6 },
  );
  assertViewportClose(
    resizeNavigatorViewport(viewport, "start", 0.9, 0.1),
    { start: 0.5, end: 0.6 },
  );
  assertViewportClose(
    resizeNavigatorViewport(viewport, "end", 0.3, 0.1),
    { start: 0.2, end: 0.3 },
  );
  assertViewportClose(
    resizeNavigatorViewport(viewport, "end", 4, 0.1),
    { start: 0.2, end: 1 },
  );

  const compactMinimumWindowWidth = 390 * 0.9 * (1 / 32);
  assert.ok(compactMinimumWindowWidth < MIN_NAVIGATOR_PAN_TARGET_PIXELS);
  assert.ok(MIN_NAVIGATOR_PAN_TARGET_PIXELS >= 44);
});

test("classifies mouse clicks separately from drags", () => {
  assert.equal(classifyMouseGesture(2, 2), "click");
  assert.equal(classifyMouseGesture(6, 0), "drag");
  assert.equal(classifyMouseGesture(0, 9), "drag");
});

test("classifies taps, horizontal scrubs, page scrolls, and pinches", () => {
  assert.equal(
    classifyTouchGesture({
      maximumTouchCount: 1,
      deltaX: 3,
      deltaY: 2,
    }),
    "tap",
  );
  assert.equal(
    classifyTouchGesture({
      maximumTouchCount: 1,
      deltaX: 20,
      deltaY: 3,
    }),
    "scrub",
  );
  assert.equal(
    classifyTouchGesture({
      maximumTouchCount: 1,
      deltaX: 6,
      deltaY: 20,
    }),
    "scroll",
  );
  assert.equal(
    classifyTouchGesture({
      maximumTouchCount: 2,
      deltaX: 0,
      deltaY: 0,
    }),
    "pinch",
  );
});

test("opens taps and deliberate scrubs but never scrolls or pinches", () => {
  assert.equal(touchGestureOpensSession("tap"), true);
  assert.equal(touchGestureOpensSession("scrub"), true);
  assert.equal(touchGestureOpensSession("scroll"), false);
  assert.equal(touchGestureOpensSession("pinch"), false);
});

test("traverses every adjacent session in either scrub direction", () => {
  assert.deepEqual(sessionTraversalIndices(2, 6, 10), [2, 3, 4, 5, 6]);
  assert.deepEqual(sessionTraversalIndices(6, 2, 10), [6, 5, 4, 3, 2]);
  assert.deepEqual(sessionTraversalIndices(4, 4, 10), [4]);
  assert.deepEqual(sessionTraversalIndices(-4, 99, 4), [0, 1, 2, 3]);
  assert.deepEqual(sessionTraversalIndices(0, 1, 0), []);
});

test("keeps active indicators visible while scrubbing or detail navigates", () => {
  assert.equal(
    activeSelectionIndicatorsVisible(false, false, false),
    false,
  );
  assert.equal(
    activeSelectionIndicatorsVisible(false, false, true),
    true,
  );
  assert.equal(
    activeSelectionIndicatorsVisible(true, false, false),
    true,
  );
  assert.equal(
    activeSelectionIndicatorsVisible(false, false, false, true),
    true,
  );
});

test("keeps phase, effort, and date-axis transforms aligned after zoom", () => {
  const outerRange = isoDateRangeEndingOn("2026-07-23", 28);
  const viewport = { start: 0.25, end: 0.75 };

  assert.deepEqual(outerRange, {
    startDate: "2026-06-25",
    endDate: "2026-07-23",
  });
  assert.equal(
    isoDateToViewportPosition(
      "2026-07-02",
      outerRange.startDate,
      outerRange.endDate,
      viewport,
    ),
    0,
  );
  assert.equal(
    isoDateToViewportPosition(
      "2026-07-16",
      outerRange.startDate,
      outerRange.endDate,
      viewport,
    ),
    1,
  );

  const effortOuterPosition = isoDateToOuterPosition(
    "2026-07-09",
    outerRange.startDate,
    outerRange.endDate,
  );
  assert.equal(effortOuterPosition, 0.5);
  assert.equal(
    outerToViewportPosition(effortOuterPosition, viewport),
    isoDateToViewportPosition(
      "2026-07-09",
      outerRange.startDate,
      outerRange.endDate,
      viewport,
    ),
  );
  assert.equal(
    viewportPositionToIsoDate(
      0.5,
      outerRange.startDate,
      outerRange.endDate,
      viewport,
    ),
    "2026-07-09",
  );
  assert.equal(
    outerPositionToIsoDate(
      effortOuterPosition,
      outerRange.startDate,
      outerRange.endDate,
    ),
    "2026-07-09",
  );
  assert.equal(
    isoDateToViewportPosition(
      outerRange.startDate,
      outerRange.startDate,
      outerRange.endDate,
      viewport,
    ),
    -0.5,
  );
});

function assertViewportClose(
  actual: PerformanceViewport,
  expected: PerformanceViewport,
): void {
  assertClose(actual.start, expected.start);
  assertClose(actual.end, expected.end);
}

function assertClose(actual: number, expected: number): void {
  assert.ok(
    Math.abs(actual - expected) < 1e-12,
    `Expected ${actual} to be close to ${expected}`,
  );
}
