import Link from "next/link";

import { MobilePrimaryNav } from "@/components/MobilePrimaryNav";
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
    <main className="min-h-screen [background:var(--theme-workout-canvas-background)] px-3 py-3 text-text-strong sm:px-4 sm:py-6">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-3 pb-[calc(5.5rem+env(safe-area-inset-bottom))] sm:gap-4 md:pb-8 lg:gap-6 lg:px-2">
        <section className="rounded-2xl [background:var(--theme-workout-header-surface)] px-4 py-3 shadow-[0_20px_45px_-32px_rgba(15,23,42,0.45)] sm:rounded-[28px] sm:px-5 sm:py-4 lg:px-6 lg:py-5">
          <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between lg:gap-4">
            <div className="max-w-3xl space-y-2">
              <Link
                href={todayHref}
                className="hidden text-[0.72rem] font-semibold uppercase tracking-[0.2em] text-accent-text md:inline"
              >
                Back to Today
              </Link>
              <h1 className="text-2xl font-semibold tracking-tight text-text-strong sm:text-3xl lg:text-[2.5rem]">
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
      <MobilePrimaryNav userId={userId} date={todayQuery.date} />
    </main>
  );
}
