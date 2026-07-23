import { LiveDayRolloverBoundary } from "@/components/LiveDayRolloverBoundary";
import { WeeklyTrainingPlanner } from "@/components/WeeklyTrainingPlanner";
import { WorkoutPageShell } from "@/components/WorkoutPageShell";
import { getDefaultUserId } from "@/lib/dailyDriverApi";

type SearchParams = Promise<Record<string, string | string[] | undefined>>;

function firstValue(value: string | string[] | undefined): string | undefined {
  return Array.isArray(value) ? value[0] : value;
}

export default async function WeeklyWorkoutPage({
  searchParams,
}: {
  searchParams: SearchParams;
}) {
  const params = await searchParams;
  const parsedUserId = Number(firstValue(params.user_id));
  const userId = Number.isInteger(parsedUserId) && parsedUserId > 0
    ? parsedUserId
    : getDefaultUserId();
  const rawWeekStart = firstValue(params.week_start_date);
  const initialWeekStartDate = rawWeekStart && /^\d{4}-\d{2}-\d{2}$/.test(rawWeekStart)
    ? rawWeekStart
    : undefined;

  return (
    <WorkoutPageShell
      activePage="week"
      userId={userId}
      weekStartDate={initialWeekStartDate}
    >
      <LiveDayRolloverBoundary requestedDate={initialWeekStartDate} />
      <WeeklyTrainingPlanner
        userId={userId}
        initialWeekStartDate={initialWeekStartDate}
      />
    </WorkoutPageShell>
  );
}
