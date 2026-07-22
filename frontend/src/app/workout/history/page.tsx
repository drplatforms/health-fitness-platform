import Link from "next/link";

import { PrimaryNavigation } from "@/components/PrimaryNavigation";
import { ThemePreferenceControl } from "@/components/ThemePreferenceControl";
import { WorkoutHistoryAnalytics } from "@/components/WorkoutHistoryAnalytics";
import { getDefaultUserId } from "@/lib/dailyDriverApi";
import { buildTodayWorkoutHref } from "@/lib/todayWorkoutApi";
import { getSwitchableUserLabel } from "@/lib/userSwitcher";
import { buildWeeklyWorkoutHref } from "@/lib/weeklyTrainingPlanApi";
import { buildWorkoutHistoryHref } from "@/lib/workoutExerciseHistoryApi";

type SearchParams = Promise<Record<string, string | string[] | undefined>>;

function firstValue(value: string | string[] | undefined): string | undefined {
  return Array.isArray(value) ? value[0] : value;
}

export default async function WorkoutHistoryPage({
  searchParams,
}: {
  searchParams: SearchParams;
}) {
  const params = await searchParams;
  const parsedUserId = Number(firstValue(params.user_id));
  const userId =
    Number.isInteger(parsedUserId) && parsedUserId > 0
      ? parsedUserId
      : getDefaultUserId();
  const userLabel = getSwitchableUserLabel(userId);

  return (
    <main className="min-h-screen [background:var(--theme-workout-canvas-background)] px-3 py-3 text-text-strong sm:px-4 sm:py-6">
      <div className="mx-auto flex w-full max-w-5xl flex-col gap-3 pb-[calc(5.5rem+env(safe-area-inset-bottom))] sm:gap-4 md:pb-8">
        <section className="rounded-2xl [background:var(--theme-workout-header-surface)] px-4 py-3 shadow-[0_20px_45px_-32px_rgba(15,23,42,0.45)] sm:rounded-[28px] md:px-5 md:py-4">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <h1 className="text-xl font-semibold tracking-tight text-text-strong md:text-3xl">
                Workout History
              </h1>
              <p className="mt-1 truncate text-sm text-text-body">
                {userLabel}
              </p>
              <nav
                aria-label="Workout view"
                className="mt-2 flex w-fit rounded-xl bg-surface/75 p-1 text-sm font-semibold"
              >
                <Link
                  href={buildTodayWorkoutHref({ userId })}
                  className="rounded-lg px-3 py-1.5 text-text-body hover:bg-surface-muted sm:px-4"
                >
                  Today
                </Link>
                <Link
                  href={buildWeeklyWorkoutHref(userId)}
                  className="rounded-lg px-3 py-1.5 text-text-body hover:bg-surface-muted sm:px-4"
                >
                  Week
                </Link>
                <Link
                  href={buildWorkoutHistoryHref(userId)}
                  aria-current="page"
                  className="rounded-lg bg-action-primary px-3 py-1.5 text-action-primary-foreground sm:px-4"
                >
                  History
                </Link>
              </nav>
            </div>
            <ThemePreferenceControl />
          </div>
        </section>

        <PrimaryNavigation userId={userId} />

        <WorkoutHistoryAnalytics userId={userId} />
      </div>
    </main>
  );
}
