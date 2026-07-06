import Link from "next/link";

import { FoodLoggingCard } from "@/components/FoodLoggingCard";
import { NutritionMacroCard } from "@/components/NutritionMacroCard";
import { RecoveryCheckInCard } from "@/components/RecoveryCheckInCard";
import { StatusPill } from "@/components/StatusPill";
import { TodayCard } from "@/components/TodayCard";
import { UserSwitcher } from "@/components/UserSwitcher";
import { formatLongReadableDate } from "@/lib/dateFormatting";
import {
  fetchDailyDriverToday,
  getDefaultUserId,
  resolveTodayQuery,
} from "@/lib/dailyDriverApi";
import { buildTodayWorkoutHref, fetchTodayWorkout } from "@/lib/todayWorkoutApi";
import { getSwitchableUserLabel } from "@/lib/userSwitcher";
import { DailyDriverWorkoutStatus } from "@/types/dailyDriver";
import { TodayWorkoutExerciseItem, TodayWorkoutResponse } from "@/types/todayWorkout";

type SearchParams = Promise<Record<string, string | string[] | undefined>>;

const workoutToneMap: Record<
  DailyDriverWorkoutStatus,
  "positive" | "caution" | "warning" | "neutral"
> = {
  not_started: "caution",
  in_progress: "positive",
  completed: "positive",
  not_planned: "neutral",
  unknown: "neutral",
};

function formatWorkoutStatusLabel(status: DailyDriverWorkoutStatus): string {
  switch (status) {
    case "not_started":
      return "Not started";
    case "in_progress":
      return "In progress";
    case "completed":
      return "Complete";
    case "not_planned":
      return "Not planned";
    default:
      return "Unknown";
  }
}

function getWorkoutActionLabel(status: DailyDriverWorkoutStatus): string {
  switch (status) {
    case "in_progress":
      return "Continue workout";
    case "completed":
      return "View completed workout";
    default:
      return "Open workout details";
  }
}

function getWorkoutSupportLine(status: DailyDriverWorkoutStatus): string {
  switch (status) {
    case "in_progress":
      return "Pick up where you left off.";
    case "completed":
      return "Completed workout summary.";
    case "not_planned":
      return "No workout is planned right now.";
    default:
      return "Ready when you are.";
  }
}

function buildWorkoutMeta(
  workout: TodayWorkoutResponse | null,
  status: DailyDriverWorkoutStatus,
): string[] {
  const items: string[] = [];

  if (workout?.exercises.length) {
    items.push(
      `${workout.exercises.length} exercise${workout.exercises.length === 1 ? "" : "s"}`,
    );
  }

  if (workout?.estimated_duration_minutes) {
    items.push(`${workout.estimated_duration_minutes} min`);
  }

  items.push(formatWorkoutStatusLabel(status));
  return items;
}

function formatExerciseSetSummary(exercise: TodayWorkoutExerciseItem): string {
  if (exercise.sets === null) {
    return "Sets not logged";
  }

  return `${exercise.sets} set${exercise.sets === 1 ? "" : "s"}`;
}

function completedWorkoutExercises(
  workout: TodayWorkoutResponse | null,
): TodayWorkoutExerciseItem[] {
  return workout?.exercises.slice(0, 6) ?? [];
}

export default async function Home({
  searchParams,
}: {
  searchParams: SearchParams;
}) {
  const resolvedSearchParams = await searchParams;
  const todayQuery = resolveTodayQuery(resolvedSearchParams);
  const [{ data, error }, todayWorkoutResult] = await Promise.all([
    fetchDailyDriverToday(todayQuery),
    fetchTodayWorkout(todayQuery),
  ]);
  const workoutHref = buildTodayWorkoutHref(todayQuery);
  const currentUserId = todayQuery.userId ?? data?.user_id ?? getDefaultUserId();
  const currentUserLabel = getSwitchableUserLabel(currentUserId);
  const displayDate = formatLongReadableDate(data?.target_date ?? todayQuery.date);
  const workoutMeta = data
    ? buildWorkoutMeta(todayWorkoutResult.data, data.workout.status)
    : [];

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(251,191,36,0.16),_transparent_35%),linear-gradient(180deg,#fffdf7_0%,#f8fafc_100%)] px-4 py-6 text-slate-950">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-4 pb-8 lg:gap-6 lg:px-2">
        <section className="rounded-[28px] bg-[linear-gradient(160deg,rgba(255,255,255,0.96),rgba(255,247,237,0.96))] px-5 py-4 shadow-[0_20px_45px_-32px_rgba(15,23,42,0.45)] lg:px-6 lg:py-5">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-2xl space-y-1">
              <p className="text-[0.72rem] font-semibold uppercase tracking-[0.2em] text-amber-700">
                Today
              </p>
              <h1 className="text-2xl font-semibold tracking-tight text-slate-950 lg:text-[2rem]">
                {displayDate}
              </h1>
            </div>

            <div className="flex flex-col gap-2 lg:items-end">
              <p className="text-[0.68rem] font-semibold uppercase tracking-[0.16em] text-slate-500">
                User
              </p>
              <div className="flex flex-col gap-2 sm:flex-row sm:items-center lg:justify-end">
                <p className="text-sm font-semibold text-slate-900">
                  {currentUserLabel}
                </p>
                <UserSwitcher
                  currentUserId={currentUserId}
                  showLabel={false}
                  selectClassName="bg-white/90 py-2.5"
                />
              </div>
            </div>
          </div>
        </section>

        {error ? (
          <TodayCard title={error.heading} accent="warm">
            <div className="space-y-3">
              <p className="text-sm leading-6 text-slate-700">{error.message}</p>
              {error.statusCode ? (
                <p className="text-xs uppercase tracking-[0.16em] text-slate-500">
                  Status {error.statusCode}
                </p>
              ) : null}
            </div>
          </TodayCard>
        ) : null}

        {!error && !data ? (
          <TodayCard title="Today is empty" accent="warm">
            <p className="text-sm leading-6 text-slate-700">
              The backend did not return a usable Today response yet.
            </p>
          </TodayCard>
        ) : null}

        {data ? (
          <div className="grid gap-4 lg:grid-cols-[minmax(0,1.35fr)_minmax(340px,0.9fr)] lg:gap-5 xl:grid-cols-[minmax(0,1.45fr)_minmax(360px,0.95fr)]">
            <div className="space-y-3 lg:col-start-1 lg:row-start-1 lg:space-y-4">
              <NutritionMacroCard nutrition={data.nutrition} />
              <FoodLoggingCard
                key={`${todayQuery.userId ?? data.user_id}:${data.target_date}`}
                userId={todayQuery.userId ?? data.user_id}
                targetDate={data.target_date}
              />
            </div>
            <TodayCard
              title="Today's Workout"
              className="lg:col-start-1 lg:row-start-2"
            >
              <div className="space-y-3">
                <div className="flex items-start justify-between gap-3">
                  <p className="text-sm leading-6 text-slate-700">
                    {getWorkoutSupportLine(data.workout.status)}
                  </p>
                  <StatusPill
                    label={formatWorkoutStatusLabel(data.workout.status)}
                    tone={workoutToneMap[data.workout.status]}
                  />
                </div>
                <div className="flex flex-wrap gap-2 text-xs">
                  {workoutMeta.map((item) => (
                    <span
                      key={item}
                      className="rounded-full bg-slate-100 px-3 py-1.5 font-semibold text-slate-700"
                    >
                      {item}
                    </span>
                  ))}
                </div>
                {data.workout.status === "completed" ? (
                  <div className="divide-y divide-slate-100 rounded-2xl bg-slate-50 px-4 py-2">
                    {completedWorkoutExercises(todayWorkoutResult.data).map(
                      (exercise) => (
                        <div
                          key={`${exercise.order}-${exercise.name}`}
                          className="flex items-center justify-between gap-3 py-2 text-sm"
                        >
                          <span className="font-semibold text-slate-900">
                            {exercise.name}
                          </span>
                          <span className="shrink-0 text-slate-600">
                            {formatExerciseSetSummary(exercise)}
                          </span>
                        </div>
                      ),
                    )}
                    {completedWorkoutExercises(todayWorkoutResult.data).length ===
                    0 ? (
                      <p className="py-2 text-sm text-slate-700">
                        Workout details are available in the completed view.
                      </p>
                    ) : null}
                  </div>
                ) : (
                  <p className="rounded-2xl bg-slate-50 px-4 py-3 text-sm text-slate-700">
                    {data.workout.first_action_label}
                  </p>
                )}
                {data.workout.planned ? (
                  <Link
                    href={workoutHref}
                    className="inline-flex items-center justify-center rounded-2xl bg-emerald-900 px-4 py-2.5 text-sm font-semibold text-emerald-50 transition hover:bg-emerald-800"
                  >
                    {getWorkoutActionLabel(data.workout.status)}
                  </Link>
                ) : null}
              </div>
            </TodayCard>

            <RecoveryCheckInCard
              userId={todayQuery.userId ?? data.user_id}
              targetDate={data.target_date}
              readiness={data.readiness}
            />

            {data.coach_note.enabled && data.coach_note.text ? (
              <TodayCard
                title="Coach Note"
                accent="warm"
                className="lg:col-start-2 lg:row-start-2"
              >
                <p className="text-sm leading-7 text-slate-800">
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
