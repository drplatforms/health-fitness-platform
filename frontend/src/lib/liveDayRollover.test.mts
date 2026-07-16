import assert from "node:assert/strict";
import test from "node:test";

import { startLiveDayRolloverWatcher } from "./dateFormatting.ts";
import type { LiveDayRolloverEnvironment } from "./dateFormatting.ts";

interface FakeEnvironmentState {
  scheduledCallback: (() => void) | null;
  scheduledDelay: number | null;
  cancelledIds: number[];
  reloadCount: number;
  visibilityCallback: (() => void) | null;
  focusCallback: (() => void) | null;
  removedVisibilityListener: boolean;
  removedFocusListener: boolean;
}

function createFakeEnvironment(
  requestedDate?: string,
): {
  environment: LiveDayRolloverEnvironment;
  state: FakeEnvironmentState;
  setNow: (value: Date) => void;
} {
  let currentDate = new Date(2026, 6, 16, 23, 59, 59, 500);
  const state: FakeEnvironmentState = {
    scheduledCallback: null,
    scheduledDelay: null,
    cancelledIds: [],
    reloadCount: 0,
    visibilityCallback: null,
    focusCallback: null,
    removedVisibilityListener: false,
    removedFocusListener: false,
  };

  return {
    environment: {
      requestedDate,
      now: () => currentDate,
      schedule: (callback, delayMilliseconds) => {
        state.scheduledCallback = callback;
        state.scheduledDelay = delayMilliseconds;
        return 7;
      },
      cancel: (timeoutId) => state.cancelledIds.push(timeoutId),
      reload: () => {
        state.reloadCount += 1;
      },
      isVisible: () => true,
      onVisibilityChange: (callback) => {
        state.visibilityCallback = callback;
        return () => {
          state.removedVisibilityListener = true;
        };
      },
      onFocus: (callback) => {
        state.focusCallback = callback;
        return () => {
          state.removedFocusListener = true;
        };
      },
    },
    state,
    setNow: (value) => {
      currentDate = value;
    },
  };
}

test("live mode schedules one local-midnight check and cleans up listeners", () => {
  const { environment, state } = createFakeEnvironment();
  const stop = startLiveDayRolloverWatcher(environment);

  assert.equal(state.scheduledDelay, 550);
  assert.ok(state.scheduledCallback);
  assert.ok(state.visibilityCallback);
  assert.ok(state.focusCallback);

  stop();

  assert.deepEqual(state.cancelledIds, [7]);
  assert.equal(state.removedVisibilityListener, true);
  assert.equal(state.removedFocusListener, true);
});

test("explicit dated mode does not schedule or subscribe", () => {
  const { environment, state } = createFakeEnvironment("2026-07-15");
  startLiveDayRolloverWatcher(environment);

  assert.equal(state.scheduledCallback, null);
  assert.equal(state.visibilityCallback, null);
  assert.equal(state.focusCallback, null);
});

test("focus and visibility rechecks reload when the local day changes", () => {
  const { environment, state, setNow } = createFakeEnvironment();
  startLiveDayRolloverWatcher(environment);
  setNow(new Date(2026, 6, 17, 8, 0, 0));

  state.focusCallback?.();
  state.visibilityCallback?.();

  assert.equal(state.reloadCount, 1);
});

test("same-day rechecks reschedule without reloading", () => {
  const { environment, state } = createFakeEnvironment();
  startLiveDayRolloverWatcher(environment);

  state.focusCallback?.();

  assert.equal(state.reloadCount, 0);
  assert.deepEqual(state.cancelledIds, [7]);
  assert.equal(state.scheduledDelay, 550);
});
