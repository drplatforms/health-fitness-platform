import type { ReactNode } from "react";

import { AppPageShell } from "@/components/AppPageShell";
import { LinkCardDeck } from "@/components/LinkCardDeck";
import {
  WORKOUT_NAV_ITEMS,
  WORKOUT_PAGE_TITLES,
  type WorkoutPage,
} from "@/lib/appUiStandards";
import { formatLongReadableDate } from "@/lib/dateFormatting";
import { buildTodayWorkoutHref } from "@/lib/todayWorkoutApi";
import { buildWeeklyWorkoutHref } from "@/lib/weeklyTrainingPlanApi";
import { buildWorkoutHistoryHref } from "@/lib/workoutExerciseHistoryApi";

interface WorkoutPageShellProps {
  activePage: WorkoutPage;
  userId: number;
  date?: string;
  todayDate?: string;
  weekStartDate?: string;
  primaryNavigationDate?: string;
  children: ReactNode;
}

export function WorkoutPageShell({
  activePage,
  userId,
  date,
  todayDate,
  weekStartDate,
  primaryNavigationDate,
  children,
}: WorkoutPageShellProps) {
  const displayDate = formatLongReadableDate(date);
  const hrefByPage: Record<WorkoutPage, string> = {
    today: buildTodayWorkoutHref({ userId, date: todayDate }),
    week: buildWeeklyWorkoutHref(userId, weekStartDate),
    history: buildWorkoutHistoryHref(userId),
  };
  const workoutNavigationItems = WORKOUT_NAV_ITEMS.map((page) => ({
    ...page,
    href: hrefByPage[page.key],
  }));

  return (
    <AppPageShell
      title={WORKOUT_PAGE_TITLES[activePage]}
      dateLabel={displayDate}
      userId={userId}
      navigationDate={primaryNavigationDate}
    >
      <LinkCardDeck
        activeKey={activePage}
        ariaLabel="Workout"
        items={workoutNavigationItems}
      />
      {children}
    </AppPageShell>
  );
}
