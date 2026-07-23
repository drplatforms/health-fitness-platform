import Link from "next/link";
import type { ReactNode } from "react";

import { PrimaryNavigation } from "@/components/PrimaryNavigation";
import { formatLongReadableDate } from "@/lib/dateFormatting";
import { buildTodayWorkoutHref } from "@/lib/todayWorkoutApi";
import { getSwitchableUserLabel } from "@/lib/userSwitcher";
import { buildWeeklyWorkoutHref } from "@/lib/weeklyTrainingPlanApi";
import { buildWorkoutHistoryHref } from "@/lib/workoutExerciseHistoryApi";

type WorkoutPage = "today" | "week" | "history";

const WORKOUT_PAGES: ReadonlyArray<{
  key: WorkoutPage;
  label: string;
}> = [
  { key: "today", label: "Today" },
  { key: "week", label: "Weekly Planner" },
  { key: "history", label: "Performance History" },
];

const PAGE_TITLES: Record<WorkoutPage, string> = {
  today: "Today",
  week: "Weekly Planner",
  history: "Performance History",
};

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
  const userLabel = getSwitchableUserLabel(userId);
  const displayDate = formatLongReadableDate(date);
  const hrefByPage: Record<WorkoutPage, string> = {
    today: buildTodayWorkoutHref({ userId, date: todayDate }),
    week: buildWeeklyWorkoutHref(userId, weekStartDate),
    history: buildWorkoutHistoryHref(userId),
  };

  return (
    <main className="min-h-screen [background:var(--theme-workout-canvas-background)] px-3 py-3 text-text-strong sm:px-4 sm:py-6">
      <div className="mx-auto flex min-w-0 w-full max-w-7xl flex-col gap-3 pb-[calc(5.5rem+env(safe-area-inset-bottom))] sm:gap-4 md:pb-8 lg:gap-6 lg:px-2">
        <header className="min-h-[10.5rem] rounded-2xl [background:var(--theme-workout-header-surface)] px-4 py-4 shadow-[0_20px_45px_-32px_rgba(15,23,42,0.45)] sm:min-h-44 sm:rounded-[28px] md:px-5 md:py-5 lg:px-6">
          <div className="flex min-h-16 items-start justify-between gap-3">
            <div className="min-w-0">
              <h1 className="truncate text-2xl font-semibold tracking-tight text-text-strong sm:text-3xl lg:text-[2.5rem]">
                {PAGE_TITLES[activePage]}
              </h1>
              <p className="mt-1 truncate text-sm font-medium text-text-body">
                {displayDate}
                <span className="sm:hidden">
                  {" "}
                  <span aria-hidden="true">•</span> {userLabel}
                </span>
              </p>
            </div>
            <p className="hidden max-w-[45%] shrink-0 truncate rounded-full bg-surface/85 px-3 py-2 text-sm font-semibold text-text-primary shadow-[0_14px_28px_-24px_rgba(15,23,42,0.45)] sm:block">
              {userLabel}
            </p>
          </div>

          <nav
            aria-label="Workout"
            className="mt-4 flex min-w-0 items-stretch gap-2 sm:mt-2 sm:items-end sm:gap-0 sm:px-4"
          >
            {WORKOUT_PAGES.map((page, index) => {
              const isActive = page.key === activePage;
              return (
                <Link
                  key={page.key}
                  href={hrefByPage[page.key]}
                  aria-current={isActive ? "page" : undefined}
                  className={`relative flex min-h-14 min-w-0 flex-1 items-center justify-center rounded-xl border px-2 py-2 text-center text-xs font-bold leading-tight transition focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus sm:w-[calc(33.333%+1rem)] sm:flex-none sm:justify-start sm:rounded-[1.5rem_1.5rem_1rem_1rem] sm:px-5 sm:pb-5 sm:pt-3 sm:text-left sm:text-base ${
                    index === 0 ? "" : "sm:-ml-6"
                  } ${
                    isActive
                      ? "z-20 border-border-accent bg-surface text-positive-foreground-strong shadow-[0_18px_35px_-24px_rgba(15,23,42,0.55)]"
                      : "z-10 border-border-subtle bg-surface-muted text-text-secondary shadow-[0_12px_26px_-24px_rgba(15,23,42,0.5)] sm:translate-y-2"
                  }`}
                >
                  {page.label}
                </Link>
              );
            })}
          </nav>
        </header>

        <PrimaryNavigation userId={userId} date={primaryNavigationDate} />

        {children}
      </div>
    </main>
  );
}
