import assert from "node:assert/strict";
import { readdirSync, readFileSync } from "node:fs";
import test from "node:test";

import {
  FOOD_WORKSPACE_LABELS,
  MEALS_WORKSPACE_LABELS,
  PRIMARY_NAV_ITEMS,
  readinessStatusLabel,
  SEMANTIC_TYPOGRAPHY_ROLES,
  WORKOUT_NAV_ITEMS,
  WORKOUT_PAGE_TITLES,
} from "./appUiStandards.ts";

function source(relativePath: string): string {
  return readFileSync(new URL(relativePath, import.meta.url), "utf8");
}

function sourceFiles(relativeDirectory: string): string[] {
  const directory = new URL(relativeDirectory, import.meta.url);
  const entries = readdirSync(directory, {
    encoding: "utf8",
    recursive: true,
  }) as string[];
  return entries
    .filter((entry) => /\.(?:ts|tsx)$/.test(entry))
    .map((entry) => readFileSync(new URL(entry, directory), "utf8"));
}

test("shared navigation and workspace labels stay concise", () => {
  assert.deepEqual(
    PRIMARY_NAV_ITEMS.map((item) => item.label),
    ["Today", "Food", "Meals", "Coach", "Workout", "Recovery"],
  );
  assert.deepEqual(
    WORKOUT_NAV_ITEMS.map((item) => item.label),
    ["Today", "Weekly Planner", "Performance History"],
  );
  assert.deepEqual(Object.values(FOOD_WORKSPACE_LABELS), [
    "Log",
    "Logged Today",
    "Pantry",
    "Library",
  ]);
  assert.deepEqual(Object.values(MEALS_WORKSPACE_LABELS), [
    "Ideas",
    "Saved Recipes",
    "Create Manually",
  ]);
});

test("page titles and readiness labels follow the shared UI contract", () => {
  assert.deepEqual(WORKOUT_PAGE_TITLES, {
    today: "Workout",
    week: "Weekly Planner",
    history: "Performance History",
  });
  assert.equal(readinessStatusLabel("ready"), "Ready to train");
  assert.equal(readinessStatusLabel("needs_recovery"), "needs recovery");
  assert.deepEqual(SEMANTIC_TYPOGRAPHY_ROLES, [
    "page-title",
    "section-title",
    "card-title",
    "body",
    "field-label",
    "status-label",
    "button",
    "compact-metadata",
    "chart-metadata",
    "feedback",
  ]);
});

test("top-level workspaces share one shell and Today alone owns theme control", () => {
  const shell = source("../components/AppPageShell.tsx");
  const today = source("../app/page.tsx");
  const daily = source("../components/DailyWorkspacePage.tsx");
  const workout = source("../components/WorkoutPageShell.tsx");

  assert.match(shell, /max-w-7xl/);
  assert.match(shell, /min-h-32/);
  assert.match(shell, /<PrimaryNavigation/);
  assert.match(shell, /<UserSwitcher/);
  assert.match(today, /<AppPageShell/);
  assert.match(today, /<ThemePreferenceControl/);
  assert.match(daily, /<AppPageShell/);
  assert.doesNotMatch(daily, /ThemePreferenceControl|Back to Today/);
  assert.match(workout, /<AppPageShell/);
  assert.doesNotMatch(workout, /ThemePreferenceControl/);
});

test("workspace decks, Coach, and workout composition omit retired UI prose", () => {
  const workspaceDeck = source("../components/WorkspaceDeck.tsx");
  const foodDeck = source("../components/FoodWorkspaceDeck.tsx");
  const mealsDeck = source("../components/MealsWorkspaceDeck.tsx");
  const coach = source("../components/CoachWorkspace.tsx");
  const workout = source("../components/WorkoutPreviewExperience.tsx");
  const limitation = source(
    "../components/TemporaryWorkoutLimitationCard.tsx",
  );

  for (const text of [
    workspaceDeck,
    foodDeck,
    mealsDeck,
    coach,
    workout,
  ]) {
    assert.doesNotMatch(
      text,
      /Search and log|Review and edit|Foods on hand|Manage your foods|Generate grounded meals|Reuse and manage|Build from your foods|Grounded Coach|Try asking|Session Status|Try different version|Select this workout/i,
    );
  }
  assert.doesNotMatch(workspaceDeck, /\bhint\b/);
  assert.match(workout, />\s*Different Version\s*</);
  assert.match(workout, />\s*Select\s*</);
  assert.match(limitation, /<dialog/);
  assert.match(limitation, /showModal\(\)/);
});

test("user-visible source uses semantic or finite typography utilities", () => {
  const applicationSource = [
    ...sourceFiles("../app/"),
    ...sourceFiles("../components/"),
  ].join("\n");

  assert.doesNotMatch(applicationSource, /text-\[/);
});
