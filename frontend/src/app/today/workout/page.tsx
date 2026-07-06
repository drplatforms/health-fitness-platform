import Link from "next/link";

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
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(16,185,129,0.18),_transparent_32%),linear-gradient(180deg,#f8fafc_0%,#f1f5f9_100%)] px-4 py-6 text-slate-950">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-4 pb-8 lg:gap-6 lg:px-2">
        <section className="rounded-[28px] bg-[linear-gradient(160deg,rgba(255,255,255,0.98),rgba(236,253,245,0.94))] px-5 py-4 shadow-[0_20px_45px_-32px_rgba(15,23,42,0.45)] lg:px-6 lg:py-5">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-3xl space-y-2">
              <Link
                href={todayHref}
                className="text-[0.72rem] font-semibold uppercase tracking-[0.2em] text-emerald-700"
              >
                Back to Today
              </Link>
              <h1 className="text-3xl font-semibold tracking-tight text-slate-950 lg:text-[2.5rem]">
                Today&apos;s Workout
              </h1>
              <p className="max-w-2xl text-sm leading-6 text-slate-600">
                Review today&apos;s workout and keep moving through the session.
              </p>
            </div>

            <div className="flex flex-wrap gap-2 lg:justify-end">
              <div className="rounded-full bg-white/85 px-3 py-2 text-sm font-semibold text-slate-900 shadow-[0_14px_28px_-24px_rgba(15,23,42,0.45)]">
                {userLabel}
              </div>
              <div className="rounded-full bg-white/85 px-3 py-2 text-sm text-slate-700 shadow-[0_14px_28px_-24px_rgba(15,23,42,0.45)]">
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
