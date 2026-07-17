import assert from "node:assert/strict";
import test from "node:test";

import {
  buildWeeklyWorkoutHref,
  getMondayWeekStart,
  previewWeeklySessionTitles,
  shiftWeekStart,
  weekDateStrings,
} from "./weeklyTrainingPlanDates.ts";

test("normalizes visible dates to a Monday-through-Sunday week", () => {
  assert.equal(getMondayWeekStart("2026-07-13"), "2026-07-13");
  assert.equal(getMondayWeekStart("2026-07-16"), "2026-07-13");
  assert.equal(getMondayWeekStart("2026-07-19"), "2026-07-13");
  assert.deepEqual(weekDateStrings("2026-07-16"), [
    "2026-07-13",
    "2026-07-14",
    "2026-07-15",
    "2026-07-16",
    "2026-07-17",
    "2026-07-18",
    "2026-07-19",
  ]);
});

test("shifts explicit week navigation without pinning the live week href", () => {
  assert.equal(shiftWeekStart("2026-07-13", -1), "2026-07-06");
  assert.equal(shiftWeekStart("2026-07-13", 1), "2026-07-20");
  assert.equal(buildWeeklyWorkoutHref(102), "/workout/week?user_id=102");
  assert.equal(
    buildWeeklyWorkoutHref(102, "2026-07-16"),
    "/workout/week?user_id=102&week_start_date=2026-07-13",
  );
});

test("previews the deterministic split in chronological weekday order", () => {
  assert.deepEqual(previewWeeklySessionTitles([5, 0, 1, 3]), [
    { weekday: 0, title: "Upper A" },
    { weekday: 1, title: "Lower A" },
    { weekday: 3, title: "Upper B" },
    { weekday: 5, title: "Lower B" },
  ]);
  assert.deepEqual(previewWeeklySessionTitles([4, 0, 2]), [
    { weekday: 0, title: "Full Body A" },
    { weekday: 2, title: "Full Body B" },
    { weekday: 4, title: "Full Body C" },
  ]);
});
