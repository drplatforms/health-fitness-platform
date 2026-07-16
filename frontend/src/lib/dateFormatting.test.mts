import assert from "node:assert/strict";
import test from "node:test";

import {
  compareIsoCalendarDates,
  getBrowserLocalDateString,
  isHistoricalRequestedDate,
  millisecondsUntilNextLocalMidnight,
} from "./dateFormatting.ts";

test("formats a date from local calendar fields", () => {
  const localDate = new Date(2026, 0, 2, 23, 30, 0);

  assert.equal(getBrowserLocalDateString(localDate), "2026-01-02");
});

test("compares valid ISO calendar dates and rejects malformed dates", () => {
  assert.equal(compareIsoCalendarDates("2026-07-15", "2026-07-16"), -1);
  assert.equal(compareIsoCalendarDates("2026-07-16", "2026-07-16"), 0);
  assert.equal(compareIsoCalendarDates("2026-07-17", "2026-07-16"), 1);
  assert.equal(compareIsoCalendarDates("2026-02-30", "2026-07-16"), null);
  assert.equal(compareIsoCalendarDates("July 15", "2026-07-16"), null);
});

test("classifies only requested dates before the browser-local day as historical", () => {
  assert.equal(isHistoricalRequestedDate("2026-07-15", "2026-07-16"), true);
  assert.equal(isHistoricalRequestedDate("2026-07-16", "2026-07-16"), false);
  assert.equal(isHistoricalRequestedDate("2026-07-17", "2026-07-16"), false);
  assert.equal(isHistoricalRequestedDate("not-a-date", "2026-07-16"), false);
  assert.equal(isHistoricalRequestedDate(undefined, "2026-07-16"), false);
});

test("schedules the next check for the next local midnight", () => {
  const justBeforeMidnight = new Date(2026, 6, 16, 23, 59, 59, 500);

  assert.equal(millisecondsUntilNextLocalMidnight(justBeforeMidnight), 500);
});
