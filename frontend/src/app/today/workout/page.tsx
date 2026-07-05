import Link from "next/link";

import { WorkoutPreviewExperience } from "@/components/WorkoutPreviewExperience";
import { getDefaultUserId, resolveTodayQuery } from "@/lib/dailyDriverApi";

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

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(16,185,129,0.18),_transparent_32%),linear-gradient(180deg,#f8fafc_0%,#f1f5f9_100%)] px-4 py-6 text-slate-950">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-4 pb-8 lg:gap-6 lg:px-2">
        <section className="rounded-[32px] bg-[linear-gradient(160deg,rgba(255,255,255,0.98),rgba(236,253,245,0.94))] p-6 shadow-[0_20px_45px_-32px_rgba(15,23,42,0.45)] lg:px-8 lg:py-7">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-3xl">
              <Link
                href={todayHref}
                className="text-[0.72rem] font-semibold uppercase tracking-[0.2em] text-emerald-700"
              >
                Back to Today
              </Link>
              <h1 className="mt-3 text-4xl font-semibold tracking-tight text-slate-950 lg:text-[3.35rem]">
                Today&apos;s Workout
              </h1>
              <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-600 lg:text-base">
                Preview the backend-generated workout, try another version, and
                commit to the exact one you want to do.
              </p>
            </div>

            <div className="grid grid-cols-2 gap-3 sm:max-w-md lg:min-w-[340px]">
              <div className="rounded-2xl bg-white/80 px-4 py-3 shadow-[0_14px_28px_-24px_rgba(15,23,42,0.45)]">
                <p className="text-[0.68rem] font-semibold uppercase tracking-[0.16em] text-slate-500">
                  User
                </p>
                <p className="mt-2 text-base font-semibold text-slate-900">
                  {userId}
                </p>
              </div>
              <div className="rounded-2xl bg-white/80 px-4 py-3 shadow-[0_14px_28px_-24px_rgba(15,23,42,0.45)]">
                <p className="text-[0.68rem] font-semibold uppercase tracking-[0.16em] text-slate-500">
                  Date
                </p>
                <p className="mt-2 text-base font-semibold text-slate-900">
                  {todayQuery.date ?? "Today"}
                </p>
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
