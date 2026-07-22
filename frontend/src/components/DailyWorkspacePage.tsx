import Link from "next/link";

import { FoodWorkspaceDeck } from "@/components/FoodWorkspaceDeck";
import { LiveDayRolloverBoundary } from "@/components/LiveDayRolloverBoundary";
import { MealsWorkspaceDeck } from "@/components/MealsWorkspaceDeck";
import { PrimaryNavigation } from "@/components/PrimaryNavigation";
import { RecoveryCheckInCard } from "@/components/RecoveryCheckInCard";
import { ThemePreferenceControl } from "@/components/ThemePreferenceControl";
import { TodayCard } from "@/components/TodayCard";
import { UserSwitcher } from "@/components/UserSwitcher";
import { fetchCanonicalFoodLogsFromBackend } from "@/lib/canonicalFoodLogsApi";
import {
  fetchDailyDriverToday,
  getDefaultUserId,
  resolveTodayQuery,
} from "@/lib/dailyDriverApi";
import { buildDailyWorkspaceHref } from "@/lib/dailyNavigation";
import { formatLongReadableDate } from "@/lib/dateFormatting";
import { fetchPersonalFoodLogsFromBackend } from "@/lib/personalFoodLogsApi";

type SearchParams = Promise<Record<string, string | string[] | undefined>>;

export async function DailyWorkspacePage({
  workspace,
  searchParams,
}: {
  workspace: "food" | "meals" | "recovery";
  searchParams: SearchParams;
}) {
  const resolvedSearchParams = await searchParams;
  const requestedFoodView = firstQueryValue(resolvedSearchParams.view);
  const todayQuery = resolveTodayQuery(resolvedSearchParams);
  const { data, error } = await fetchDailyDriverToday(todayQuery);
  const userId = todayQuery.userId ?? data?.user_id ?? getDefaultUserId();
  const displayDate = formatLongReadableDate(data?.target_date ?? todayQuery.date);
  const todayHref = buildDailyWorkspaceHref("today", userId, todayQuery.date);

  const [canonicalLoggedFoodsResult, personalLoggedFoodsResult] =
    workspace === "food" && data
      ? await Promise.all([
          fetchCanonicalFoodLogsFromBackend({
            userId,
            date: data.target_date,
          }),
          fetchPersonalFoodLogsFromBackend({
            userId,
            date: data.target_date,
          }),
        ])
      : [
          { data: null, error: null },
          { data: null, error: null },
        ];
  const loggedFoodEntries = [
    ...(canonicalLoggedFoodsResult.data?.entries ?? []).map((entry) => ({
      ...entry,
      food_type: "canonical" as const,
    })),
    ...(personalLoggedFoodsResult.data?.entries ?? []),
  ];
  const loggedFoodsError =
    canonicalLoggedFoodsResult.error && personalLoggedFoodsResult.error
      ? "Logged foods are unavailable right now."
      : canonicalLoggedFoodsResult.error || personalLoggedFoodsResult.error
        ? "Some logged foods are unavailable right now."
        : null;
  const title =
    workspace === "food"
      ? "Food"
      : workspace === "meals"
        ? "Meals"
        : "Recovery";

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,var(--theme-canvas-glow),transparent_35%),linear-gradient(180deg,var(--theme-canvas-start)_0%,var(--theme-canvas)_100%)] px-3 py-3 text-text-strong sm:px-4 sm:py-6">
      <LiveDayRolloverBoundary requestedDate={todayQuery.date} />
      <div className="mx-auto flex w-full max-w-5xl flex-col gap-3 pb-[calc(5.5rem+env(safe-area-inset-bottom))] sm:gap-4 md:pb-8 lg:gap-5 lg:px-2">
        <section className="rounded-2xl bg-[linear-gradient(160deg,var(--theme-header-surface-start),var(--theme-header-surface-end))] px-4 py-3 shadow-[0_20px_45px_-32px_rgba(15,23,42,0.45)] sm:rounded-[28px] sm:px-5 sm:py-4 lg:px-6 lg:py-5">
          <div className="flex items-end justify-between gap-3">
            <div className="min-w-0">
              <Link
                href={todayHref}
                className="hidden text-[0.72rem] font-semibold uppercase tracking-[0.18em] text-accent-text md:inline"
              >
                Back to Today
              </Link>
              <h1 className="text-xl font-semibold tracking-tight text-text-strong sm:text-2xl">
                {title}
              </h1>
              <p className="mt-0.5 truncate text-sm text-text-body">
                {displayDate}
              </p>
            </div>
            <div className="flex shrink-0 items-center gap-2">
              <UserSwitcher
                currentUserId={userId}
                showLabel={false}
                selectClassName="bg-surface/90 py-2.5"
              />
              <ThemePreferenceControl />
            </div>
          </div>
        </section>

        <PrimaryNavigation userId={userId} date={todayQuery.date} />

        {error ? (
          <TodayCard title={error.heading} accent="warm">
            <p className="text-sm leading-6 text-text-body">{error.message}</p>
          </TodayCard>
        ) : null}

        {!error && !data ? (
          <TodayCard title={`${title} is unavailable`} accent="warm">
            <p className="text-sm leading-6 text-text-body">
              The backend did not return a usable daily response yet.
            </p>
          </TodayCard>
        ) : null}

        {data && workspace === "food" ? (
          <FoodWorkspaceDeck
            key={`${userId}:${data.target_date}`}
            userId={userId}
            targetDate={data.target_date}
            requestedDate={todayQuery.date}
            initialLoggedEntries={loggedFoodEntries}
            initialLoggedError={loggedFoodsError}
            initialView={foodView(requestedFoodView)}
          />
        ) : null}

        {data && workspace === "meals" ? (
          <MealsWorkspaceDeck
            key={`${userId}:${data.target_date}`}
            userId={userId}
            targetDate={data.target_date}
          />
        ) : null}

        {data && workspace === "recovery" ? (
          <div className="space-y-3 sm:space-y-4">
            <RecoveryCheckInCard
              userId={userId}
              targetDate={data.target_date}
              readiness={data.readiness}
            />
            {data.coach_note.enabled && data.coach_note.text ? (
              <TodayCard title="Coach Note" accent="warm">
                <p className="text-sm leading-7 text-text-body">
                  {data.coach_note.text}
                </p>
              </TodayCard>
            ) : null}
          </div>
        ) : null}
      </div>
    </main>
  );
}

function firstQueryValue(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] : value;
}

function foodView(value: string | undefined) {
  return value === "logged" || value === "pantry" || value === "library"
    ? value
    : "log";
}
