import { AppPageShell } from "@/components/AppPageShell";
import { CoachWorkspace } from "@/components/CoachWorkspace";
import { FoodWorkspaceDeck } from "@/components/FoodWorkspaceDeck";
import { LiveDayRolloverBoundary } from "@/components/LiveDayRolloverBoundary";
import { LongitudinalInsightsPanel } from "@/components/LongitudinalInsightsPanel";
import { MealsWorkspaceDeck } from "@/components/MealsWorkspaceDeck";
import { RecoveryCheckInCard } from "@/components/RecoveryCheckInCard";
import { TodayCard } from "@/components/TodayCard";
import { fetchCanonicalFoodLogsFromBackend } from "@/lib/canonicalFoodLogsApi";
import {
  fetchDailyDriverToday,
  getDefaultUserId,
  resolveTodayQuery,
} from "@/lib/dailyDriverApi";
import { formatLongReadableDate } from "@/lib/dateFormatting";
import { fetchLongitudinalInsightsFromBackend } from "@/lib/longitudinalInsightApi";
import { fetchPersonalFoodLogsFromBackend } from "@/lib/personalFoodLogsApi";

type SearchParams = Promise<Record<string, string | string[] | undefined>>;

export async function DailyWorkspacePage({
  workspace,
  searchParams,
}: {
  workspace: "coach" | "food" | "meals" | "recovery";
  searchParams: SearchParams;
}) {
  const resolvedSearchParams = await searchParams;
  const requestedFoodView = firstQueryValue(resolvedSearchParams.view);
  const todayQuery = resolveTodayQuery(resolvedSearchParams);
  const { data, error } = await fetchDailyDriverToday(todayQuery);
  const userId = todayQuery.userId ?? data?.user_id ?? getDefaultUserId();
  const displayDate = formatLongReadableDate(data?.target_date ?? todayQuery.date);
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
  const longitudinalInsightsResult =
    workspace === "recovery" && data
      ? await fetchLongitudinalInsightsFromBackend(userId, data.target_date)
      : { data: null, error: null };
  const title =
    workspace === "coach"
      ? "Coach"
      : workspace === "food"
        ? "Food"
        : workspace === "meals"
          ? "Meals"
          : "Recovery";

  return (
    <>
      <LiveDayRolloverBoundary requestedDate={todayQuery.date} />
      <AppPageShell
        title={title}
        dateLabel={displayDate}
        userId={userId}
        navigationDate={todayQuery.date}
      >
        {workspace !== "coach" && error ? (
          <TodayCard title={error.heading} accent="warm">
            <p className="text-sm leading-6 text-text-body">{error.message}</p>
          </TodayCard>
        ) : null}

        {workspace !== "coach" && !error && !data ? (
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

        {workspace === "coach" ? (
          <CoachWorkspace
            key={`${userId}:${data?.target_date ?? todayQuery.date ?? "live"}`}
            userId={userId}
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
            <LongitudinalInsightsPanel
              data={longitudinalInsightsResult.data}
              error={longitudinalInsightsResult.error}
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
      </AppPageShell>
    </>
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
