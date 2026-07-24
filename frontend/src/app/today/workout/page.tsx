import { LiveDayRolloverBoundary } from "@/components/LiveDayRolloverBoundary";
import { WorkoutPageShell } from "@/components/WorkoutPageShell";
import { WorkoutPreviewExperience } from "@/components/WorkoutPreviewExperience";
import { getDefaultUserId, resolveTodayQuery } from "@/lib/dailyDriverApi";

type SearchParams = Promise<Record<string, string | string[] | undefined>>;

export default async function WorkoutPage({
  searchParams,
}: {
  searchParams: SearchParams;
}) {
  const resolvedSearchParams = await searchParams;
  const todayQuery = resolveTodayQuery(resolvedSearchParams);
  const userId = todayQuery.userId ?? getDefaultUserId();

  return (
    <WorkoutPageShell
      activePage="today"
      userId={userId}
      date={todayQuery.date}
      todayDate={todayQuery.date}
      weekStartDate={todayQuery.date}
      primaryNavigationDate={todayQuery.date}
    >
      <LiveDayRolloverBoundary requestedDate={todayQuery.date} />
      <WorkoutPreviewExperience
        key={`${userId}:${todayQuery.date ?? "live"}`}
        userId={userId}
        requestedDate={todayQuery.date}
      />
    </WorkoutPageShell>
  );
}
