import assert from "node:assert/strict";
import test from "node:test";

import {
  buildCalendarTicks,
  buildEffortSegments,
  buildPerformanceMetricScale,
  buildWorkoutHistoryHref,
  describeWorkingLoadTrend,
  exerciseAnalyticsKey,
  formatPerformanceMetric,
  moveSessionIndex,
  nearestSessionIndex,
  PERFORMANCE_STUDIO_RANGES,
  performanceMetricPosition,
  performanceStudioEmptyMessage,
  phaseBandCanShowLabel,
  resolveExerciseSelectionKey,
  splitMetricRuns,
  sustainedPhaseBand,
  timelineDatePosition,
} from "./workoutExerciseHistoryApi.ts";
import type {
  ExerciseHistoryAnalyticsSummary,
  ExercisePerformancePhaseSegment,
} from "../types/workoutExerciseHistory.ts";

test("builds user-scoped workout history links", () => {
  assert.equal(
    buildWorkoutHistoryHref(102),
    "/workout/history?user_id=102",
  );
});

test("uses catalog identity before normalized name fallback", () => {
  assert.equal(
    exerciseAnalyticsKey({
      catalog_exercise_id: 55,
      exercise_name: "Dumbbell Row",
    }),
    "catalog:55",
  );
  assert.equal(
    exerciseAnalyticsKey({
      catalog_exercise_id: null,
      exercise_name: "  Dumbbell   Row ",
    }),
    "name:dumbbell row",
  );
});

test("describes only meaningful factual load trends with product wording", () => {
  assert.equal(
    describeWorkingLoadTrend({
      status: "higher_recently",
      latest_comparable_working_weight: 50,
      comparison_working_weight: 40,
      absolute_change_lb: 10,
      qualifying_session_count: 2,
    }),
    "Recent load: 10 lb higher",
  );
  assert.equal(
    describeWorkingLoadTrend({
      status: "steady",
      latest_comparable_working_weight: 40,
      comparison_working_weight: 40,
      absolute_change_lb: 0,
      qualifying_session_count: 2,
    }),
    "Recent load: steady",
  );
  assert.equal(
    describeWorkingLoadTrend({
      status: "insufficient_data",
      latest_comparable_working_weight: null,
      comparison_working_weight: null,
      absolute_change_lb: null,
      qualifying_session_count: 0,
    }),
    null,
  );
});

test("exposes the four bounded Performance Studio ranges", () => {
  assert.deepEqual(
    PERFORMANCE_STUDIO_RANGES.map((range) => [range.days, range.label]),
    [
      [28, "4 weeks"],
      [84, "12 weeks"],
      [183, "6 months"],
      [365, "1 year"],
    ],
  );
});

test("formats each backend-owned performance metric without unit conversion", () => {
  assert.equal(
    formatPerformanceMetric({
      metric_type: "load",
      label: "Load",
      value: 47.5,
      unit: "lb",
    }),
    "47.5 lb",
  );
  assert.equal(
    formatPerformanceMetric({
      metric_type: "duration",
      label: "Longest set",
      value: 90,
      unit: "seconds",
    }),
    "1:30",
  );
  assert.equal(
    formatPerformanceMetric({
      metric_type: "distance",
      label: "Longest set",
      value: 1500,
      unit: "meters",
    }),
    "1.5 km",
  );
});

test("retains a valid exercise selection and falls back when a range removes it", () => {
  const exercises = [
    { catalog_exercise_id: 11, exercise_name: "Bench Press" },
    { catalog_exercise_id: 22, exercise_name: "Plank" },
  ] as ExerciseHistoryAnalyticsSummary[];

  assert.equal(resolveExerciseSelectionKey(exercises, "catalog:22"), "catalog:22");
  assert.equal(resolveExerciseSelectionKey(exercises, "catalog:99"), "catalog:11");
  assert.equal(resolveExerciseSelectionKey([], "catalog:22"), "");
});

test("uses useful range and no-history empty states", () => {
  assert.equal(
    performanceStudioEmptyMessage(false, 28),
    "No completed exercise sessions were found in the last 4 weeks. Try a longer range.",
  );
  assert.equal(
    performanceStudioEmptyMessage(false, 365),
    "Complete and log a workout to build your performance history.",
  );
});

test("positions sessions by their actual calendar gaps", () => {
  assert.equal(
    timelineDatePosition("2026-01-02", "2026-01-01", "2026-01-11"),
    0.1,
  );
  assert.equal(
    timelineDatePosition("2026-01-10", "2026-01-01", "2026-01-11"),
    0.9,
  );
  assert.equal(
    timelineDatePosition("2025-12-01", "2026-01-01", "2026-01-11"),
    0,
  );
  assert.equal(
    timelineDatePosition("2026-02-01", "2026-01-01", "2026-01-11"),
    1,
  );
});

test("snaps to the nearest of 160 chronological sessions across the plot", () => {
  const positions = Array.from({ length: 160 }, (_, index) => index / 159);
  const expectedNearest = (target: number) =>
    positions.reduce(
      (best, position, index) =>
        Math.abs(position - target) <= Math.abs(positions[best] - target)
          ? index
          : best,
      0,
    );

  for (const target of [0, 0.013, 0.25, 0.503, 0.731, 0.999, 1]) {
    assert.equal(
      nearestSessionIndex(positions, target),
      expectedNearest(target),
    );
  }
  assert.equal(nearestSessionIndex([], 0.5), -1);
  assert.equal(nearestSessionIndex(positions, -4), 0);
  assert.equal(nearestSessionIndex(positions, 4), 159);
  assert.equal(nearestSessionIndex([0, 0.5, 1], 0.25), 1);
});

test("keeps keyboard session movement within chronological bounds", () => {
  assert.equal(moveSessionIndex(0, 160, -1), 0);
  assert.equal(moveSessionIndex(159, 160, 1), 159);
  assert.equal(moveSessionIndex(80, 160, -1), 79);
  assert.equal(moveSessionIndex(80, 160, 1), 81);
  assert.equal(moveSessionIndex(999, 160, 1), 159);
  assert.equal(moveSessionIndex(-1, 160, 1), 159);
  assert.equal(moveSessionIndex(0, 0, 1), -1);
});

test("builds bounded, ordered calendar ticks with stable endpoints", () => {
  const ticks = buildCalendarTicks("2025-07-24", "2026-07-23", 5);
  assert.equal(ticks.length, 5);
  assert.equal(ticks[0], "2025-07-24");
  assert.equal(ticks.at(-1), "2026-07-23");
  assert.deepEqual(ticks, [...ticks].sort());
  assert.equal(new Set(ticks).size, ticks.length);

  const cappedTicks = buildCalendarTicks(
    "2025-07-24",
    "2026-07-23",
    100,
  );
  assert.equal(cappedTicks.length, 7);
  assert.deepEqual(
    buildCalendarTicks("2026-07-23", "2026-07-23", 5),
    ["2026-07-23"],
  );
});

test("builds a zero-origin rounded metric scale and positions values safely", () => {
  const scale = buildPerformanceMetricScale([40, 50, 60]);
  assert.ok(scale);
  assert.deepEqual(scale, {
    minimum: 0,
    maximum: 60,
    ticks: [0, 20, 40, 60],
  });
  assert.equal(performanceMetricPosition(40, scale), 2 / 3);
  assert.equal(performanceMetricPosition(50, scale), 5 / 6);
  assert.equal(performanceMetricPosition(60, scale), 1);
  assert.equal(performanceMetricPosition(20, scale), 1 / 3);
  assert.equal(performanceMetricPosition(80, scale), 1);
  assert.equal(performanceMetricPosition(Number.NaN, scale), 0.5);

  const onePoundChange = buildPerformanceMetricScale([56, 57]);
  assert.deepEqual(onePoundChange, {
    minimum: 0,
    maximum: 60,
    ticks: [0, 20, 40, 60],
  });
  assert.ok(
    Math.abs(
      performanceMetricPosition(57, onePoundChange) -
        performanceMetricPosition(56, onePoundChange) -
        1 / 60,
    ) < 1e-12,
  );

  const constantScale = buildPerformanceMetricScale([50, 50, 50]);
  assert.ok(constantScale);
  assert.equal(constantScale.minimum, 0);
  assert.ok(constantScale.maximum >= 50);
  assert.deepEqual(buildPerformanceMetricScale([0, 0]), {
    minimum: 0,
    maximum: 1,
    ticks: [0, 0.5, 1],
  });
  assert.equal(buildPerformanceMetricScale([Number.NaN]), null);
});

test("splits metric runs on missing, non-finite, and incompatible values", () => {
  const sessions = [
    {
      session_key: "load-1",
      performance_metric: {
        metric_type: "load",
        label: "Load",
        value: 40,
        unit: "lb",
      },
    },
    {
      session_key: "load-2",
      performance_metric: {
        metric_type: "load",
        label: "Load",
        value: 42.5,
        unit: "lb",
      },
    },
    { session_key: "missing", performance_metric: null },
    {
      session_key: "reps",
      performance_metric: {
        metric_type: "reps",
        label: "Best set",
        value: 12,
        unit: "reps",
      },
    },
    {
      session_key: "invalid",
      performance_metric: {
        metric_type: "load",
        label: "Load",
        value: Number.NaN,
        unit: "lb",
      },
    },
    {
      session_key: "load-3",
      performance_metric: {
        metric_type: "load",
        label: "Load",
        value: 45,
        unit: "lb",
      },
    },
    {
      session_key: "load-4",
      performance_metric: {
        metric_type: "load",
        label: "Load",
        value: 47.5,
        unit: "lb",
      },
    },
  ] as const;

  assert.deepEqual(splitMetricRuns(sessions, "load"), [
    ["load-1", "load-2"],
    ["load-3", "load-4"],
  ]);
  assert.deepEqual(splitMetricRuns(sessions, "distance"), []);
});

test("preserves honest gaps in the aligned effort strip", () => {
  assert.deepEqual(
    buildEffortSegments([
      { session_key: "a", average_actual_rir: 3 },
      { session_key: "b", average_actual_rir: null },
      { session_key: "c", average_actual_rir: 2 },
      { session_key: "d", average_actual_rir: 1 },
      { session_key: "e", average_actual_rir: Number.NaN },
      { session_key: "f", average_actual_rir: 2 },
    ]),
    [["a"], ["c", "d"], ["f"]],
  );
  assert.deepEqual(
    buildEffortSegments([
      { session_key: "a", average_actual_rir: null },
      { session_key: "b", average_actual_rir: null },
    ]),
    [],
  );
});

test("renders only sustained phase bands and labels bands with enough room", () => {
  const phase = phaseFixture();
  assert.equal(sustainedPhaseBand(phase), true);
  assert.equal(
    sustainedPhaseBand(
      phaseFixture({
        evidence_session_count: 1,
        end_session_key: "session-1",
      }),
    ),
    false,
  );
  assert.equal(
    sustainedPhaseBand(
      phaseFixture({
        end_date: "2026-01-01",
        end_session_key: "session-2",
      }),
    ),
    false,
  );
  assert.equal(
    sustainedPhaseBand(
      phaseFixture({
        end_session_key: "session-1",
      }),
    ),
    false,
  );

  assert.equal(
    phaseBandCanShowLabel(
      phase,
      "2026-01-01",
      "2026-04-01",
      900,
    ),
    true,
  );
  assert.equal(
    phaseBandCanShowLabel(
      phase,
      "2026-01-01",
      "2026-04-01",
      100,
    ),
    false,
  );
  assert.equal(
    phaseBandCanShowLabel(
      phaseFixture({
        label: "Stable load with considerably higher recorded effort",
      }),
      "2026-01-01",
      "2026-04-01",
      500,
    ),
    false,
  );
});

function phaseFixture(
  overrides: Partial<ExercisePerformancePhaseSegment> = {},
): ExercisePerformancePhaseSegment {
  return {
    code: "progression",
    label: "Progression",
    evidence: "Load increased across comparable sessions.",
    evidence_session_count: 3,
    start_date: "2026-01-01",
    end_date: "2026-03-01",
    start_session_key: "session-1",
    end_session_key: "session-3",
    ...overrides,
  };
}
