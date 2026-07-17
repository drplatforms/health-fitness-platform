import assert from "node:assert/strict";
import test from "node:test";

import {
  activeDailyWorkspace,
  buildDailyWorkspaceHref,
} from "./dailyNavigation.ts";

test("builds the four primary daily workspace routes", () => {
  assert.equal(buildDailyWorkspaceHref("today", 101), "/?user_id=101");
  assert.equal(buildDailyWorkspaceHref("food", 101), "/food?user_id=101");
  assert.equal(
    buildDailyWorkspaceHref("workout", 101),
    "/today/workout?user_id=101",
  );
  assert.equal(
    buildDailyWorkspaceHref("recovery", 101),
    "/recovery?user_id=101",
  );
});

test("keeps live navigation unpinned and preserves explicit dates", () => {
  assert.equal(
    buildDailyWorkspaceHref("workout", 101),
    "/today/workout?user_id=101",
  );
  assert.equal(
    buildDailyWorkspaceHref("workout", 101, "2026-07-15"),
    "/today/workout?user_id=101&date=2026-07-15",
  );
  assert.equal(
    buildDailyWorkspaceHref("food", 101, "2026-07-15"),
    "/food?user_id=101&date=2026-07-15",
  );
});

test("maps nested personal-food routes to the Food destination", () => {
  assert.equal(activeDailyWorkspace("/"), "today");
  assert.equal(activeDailyWorkspace("/food"), "food");
  assert.equal(activeDailyWorkspace("/personal-foods"), "food");
  assert.equal(activeDailyWorkspace("/personal-foods/new"), "food");
  assert.equal(activeDailyWorkspace("/personal-foods/42"), "food");
  assert.equal(activeDailyWorkspace("/today/workout"), "workout");
  assert.equal(activeDailyWorkspace("/workout/week"), "workout");
  assert.equal(activeDailyWorkspace("/workout/history"), "workout");
  assert.equal(activeDailyWorkspace("/recovery"), "recovery");
});
