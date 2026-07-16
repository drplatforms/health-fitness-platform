import Link from "next/link";

import { ThemePreferenceControl } from "@/components/ThemePreferenceControl";
import { WorkoutPreviewExperience } from "@/components/WorkoutPreviewExperience";
import { formatLongReadableDate } from "@/lib/dateFormatting";
import { getDefaultUserId, resolveTodayQuery } from "@/lib/dailyDriverApi";
import { getSwitchableUserLabel } from "@/lib/userSwitcher";

type SearchParams = Promise<Record<string, string | string[] | undefined>>;

function buildTodayHref(userId?: number, date?: string): string {
  const params = new URLSearchParams();

  if (userId) {
    params.set("user_id", String(userId));
  }
  if (date) {
    params.set("date", date);
  }

  const query = params.toString();
  return query ? `/?${query}` : "/";
}

export default async function WorkoutPage({
  searchParams,
}: {
  searchParams: SearchParams;
}) {
  const resolvedSearchParams = await searchParams;
  const todayQuery = resolveTodayQuery(resolvedSearchParams);
  const userId = todayQuery.userId ?? getDefaultUserId();
  const todayHref = buildTodayHref(todayQuery.userId, todayQuery.date);
  const userLabel = getSwitchableUserLabel(userId);
  const displayDate = formatLongReadableDate(todayQuery.date);

  return (
    <main className="min-h-screen [background:var(--theme-workout-canvas-background)] px-4 py-6 text-text-strong">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-4 pb-8 lg:gap-6 lg:px-2">
        <section className="rounded-[28px] [background:var(--theme-workout-header-surface)] px-5 py-4 shadow-[0_20px_45px_-32px_rgba(15,23,42,0.45)] lg:px-6 lg:py-5">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-3xl space-y-2">
              <Link
                href={todayHref}
                className="text-[0.72rem] font-semibold uppercase tracking-[0.2em] text-accent-text"
              >
                Back to Today
              </Link>
              <h1 className="text-3xl font-semibold tracking-tight text-text-strong lg:text-[2.5rem]">
                Today&apos;s Workout
              </h1>
            </div>

            <div className="flex flex-wrap gap-2 lg:justify-end">
              <ThemePreferenceControl />
              <div className="rounded-full bg-surface/85 px-3 py-2 text-sm font-semibold text-text-primary shadow-[0_14px_28px_-24px_rgba(15,23,42,0.45)]">
                {userLabel}
              </div>
              <div className="rounded-full bg-surface/85 px-3 py-2 text-sm text-text-body shadow-[0_14px_28px_-24px_rgba(15,23,42,0.45)]">
                {displayDate}
              </div>
            </div>
          </div>
        </section>

        <WorkoutPreviewExperience
          userId={userId}
          requestedDate={todayQuery.date}
        />
      </div>
    </main>
  );
}
