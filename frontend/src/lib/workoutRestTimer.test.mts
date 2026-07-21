import assert from "node:assert/strict";
import test from "node:test";

import {
  extendWorkoutRestTimer,
  formatWorkoutRestCountdown,
  remainingWorkoutRestSeconds,
  resolveWorkoutRestSeconds,
  startWorkoutRestTimer,
  WORKOUT_REST_FALLBACK_SECONDS,
} from "./workoutRestTimer.ts";

test("uses a prescribed rest duration when present and the v1 fallback otherwise", () => {
  assert.equal(resolveWorkoutRestSeconds(120), 120);
  assert.equal(resolveWorkoutRestSeconds(null), WORKOUT_REST_FALLBACK_SECONDS);
  assert.equal(resolveWorkoutRestSeconds(0), WORKOUT_REST_FALLBACK_SECONDS);
});

test("starts a fresh rest period from each successful save timestamp", () => {
  const firstEndAtMs = startWorkoutRestTimer(10_000, 60);
  const restartedEndAtMs = startWorkoutRestTimer(25_000, 60);

  assert.equal(firstEndAtMs, 70_000);
  assert.equal(restartedEndAtMs, 85_000);
});

test("derives remaining time from the end timestamp after delayed ticks", () => {
  const endAtMs = startWorkoutRestTimer(1_000, 90);

  assert.equal(remainingWorkoutRestSeconds(endAtMs, 1_000), 90);
  assert.equal(remainingWorkoutRestSeconds(endAtMs, 31_250), 60);
  assert.equal(remainingWorkoutRestSeconds(endAtMs, 100_000), 0);
});

test("adds 30 seconds from now when the prior rest period is already complete", () => {
  assert.equal(extendWorkoutRestTimer(40_000, 45_000), 75_000);
  assert.equal(extendWorkoutRestTimer(60_000, 45_000), 90_000);
});

test("formats a compact minute and second countdown", () => {
  assert.equal(formatWorkoutRestCountdown(90), "1:30");
  assert.equal(formatWorkoutRestCountdown(5), "0:05");
  assert.equal(formatWorkoutRestCountdown(0), "0:00");
});
