import type { DailyWorkspaceDestination } from "@/lib/dailyNavigation";

export const PRIMARY_NAV_ITEMS: ReadonlyArray<{
  key: DailyWorkspaceDestination;
  label: string;
}> = [
  { key: "today", label: "Today" },
  { key: "food", label: "Food" },
  { key: "meals", label: "Meals" },
  { key: "coach", label: "Coach" },
  { key: "workout", label: "Workout" },
  { key: "recovery", label: "Recovery" },
];

export type WorkoutPage = "today" | "week" | "history";

export const WORKOUT_NAV_ITEMS: ReadonlyArray<{
  key: WorkoutPage;
  label: string;
}> = [
  { key: "today", label: "Today" },
  { key: "week", label: "Weekly Planner" },
  { key: "history", label: "Performance History" },
];

export const WORKOUT_PAGE_TITLES: Record<WorkoutPage, string> = {
  today: "Workout",
  week: "Weekly Planner",
  history: "Performance History",
};

export const FOOD_WORKSPACE_LABELS = {
  log: "Log",
  logged: "Logged Today",
  pantry: "Pantry",
  library: "Library",
} as const;

export const MEALS_WORKSPACE_LABELS = {
  ideas: "Ideas",
  saved: "Saved Recipes",
  create: "Create Manually",
} as const;

export const SEMANTIC_TYPOGRAPHY_ROLES = [
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
] as const;

export function readinessStatusLabel(status: string): string {
  return status === "ready"
    ? "Ready to train"
    : status.replaceAll("_", " ");
}
