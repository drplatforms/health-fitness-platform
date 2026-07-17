import assert from "node:assert/strict";
import test from "node:test";

import {
  buildWorkoutHistoryHref,
  describeWorkingLoadTrend,
  exerciseAnalyticsKey,
} from "./workoutExerciseHistoryApi.ts";

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

test("describes only meaningful factual working-load trends", () => {
  assert.equal(
    describeWorkingLoadTrend({
      status: "higher_recently",
      latest_comparable_working_weight: 50,
      comparison_working_weight: 40,
      absolute_change_lb: 10,
      qualifying_session_count: 2,
    }),
    "Recent working load: 10 lb higher",
  );
  assert.equal(
    describeWorkingLoadTrend({
      status: "steady",
      latest_comparable_working_weight: 40,
      comparison_working_weight: 40,
      absolute_change_lb: 0,
      qualifying_session_count: 2,
    }),
    "Recent working load: steady",
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
