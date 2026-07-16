import Link from "next/link";

import { FoodWorkspaceDeck } from "@/components/FoodWorkspaceDeck";
import { LoggedFoodsList } from "@/components/LoggedFoodsList";
import { LiveDayRolloverBoundary } from "@/components/LiveDayRolloverBoundary";
import { MobilePrimaryNav } from "@/components/MobilePrimaryNav";
import { NutritionMacroCard } from "@/components/NutritionMacroCard";
import { RecoveryCheckInCard } from "@/components/RecoveryCheckInCard";
import { StatusPill } from "@/components/StatusPill";
import { ThemePreferenceControl } from "@/components/ThemePreferenceControl";
import { TodayCard } from "@/components/TodayCard";
import { UserSwitcher } from "@/components/UserSwitcher";
import { formatLongReadableDate } from "@/lib/dateFormatting";
import {
  fetchDailyDriverToday,
  getDefaultUserId,
  resolveTodayQuery,
} from "@/lib/dailyDriverApi";
import { buildDailyWorkspaceHref } from "@/lib/dailyNavigation";
import { fetchCanonicalFoodLogsFromBackend } from "@/lib/canonicalFoodLogsApi";
import { fetchPersonalFoodLogsFromBackend } from "@/lib/personalFoodLogsApi";
import {
  buildTodayWorkoutHref,
  fetchTodayWorkout,
  fetchWorkoutCurrentFromBackend,
} from "@/lib/todayWorkoutApi";
import { DailyDriverWorkoutStatus } from "@/types/dailyDriver";
import {
  TodayWorkoutResponse,
  WorkoutActualSetSummary,
  WorkoutCurrentResponse,
} from "@/types/todayWorkout";

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
  currentWorkout: WorkoutCurrentResponse | null,
): string[] {
  const items: string[] = [];
  items.push(formatWorkoutStatusLabel(status));

  const plannedExercises =
    currentWorkout?.current_execution_state?.planned_exercises ?? [];
  const actualSets = currentWorkout?.current_execution_state?.actual_sets ?? [];
  const plannedSetCount = plannedExercises.reduce(
    (total, exercise) => total + exercise.sets,
    0,
  );
  const completedSetCount = actualSets.filter(
    (actualSet) => actualSet.completed && !actualSet.skipped,
  ).length;

  if (plannedSetCount > 0) {
    items.push(`${completedSetCount}/${plannedSetCount} sets`);
  }

  if (workout?.exercises.length) {
    items.push(
      `${workout.exercises.length} exercise${workout.exercises.length === 1 ? "" : "s"}`,
    );
  }

  if (workout?.estimated_duration_minutes) {
    items.push(`${workout.estimated_duration_minutes} min`);
  }

  return items;
}

function formatRange(min: number | null, max: number | null): string | null {
  if (min === null && max === null) {
    return null;
  }

  if (min === max) {
    return String(min);
  }

  if (min === null) {
    return String(max);
  }

  if (max === null) {
    return String(min);
  }

  return `${min}-${max}`;
}

function actualSetsForExercise(
  actualSets: WorkoutActualSetSummary[],
  plannedExerciseId: number,
): WorkoutActualSetSummary[] {
  return actualSets.filter(
    (actualSet) =>
      actualSet.planned_workout_exercise_id === plannedExerciseId ||
      actualSet.substitution_for_planned_exercise_id === plannedExerciseId,
  );
}

function formatActualSetDetail(actualSet: WorkoutActualSetSummary): string[] {
  const details: string[] = [];

  if (actualSet.actual_reps !== null) {
    details.push(`${actualSet.actual_reps} reps`);
  }
  if (actualSet.actual_weight !== null) {
    details.push(`${actualSet.actual_weight} lb`);
  }
  if (actualSet.actual_rir !== null) {
    details.push(`RIR ${actualSet.actual_rir}`);
  }

  return details;
}

function currentWorkoutRows(
  currentWorkout: WorkoutCurrentResponse | null,
): Array<{ key: string; name: string; detail: string }> {
  const currentExecution = currentWorkout?.current_execution_state;
  if (!currentExecution?.planned_exercises.length) {
    return [];
  }

  return currentExecution.planned_exercises.slice(0, 6).map((exercise) => {
    const loggedSets = actualSetsForExercise(
      currentExecution.actual_sets,
      exercise.id,
    ).filter((actualSet) => actualSet.completed && !actualSet.skipped);
    const latestLoggedSet = loggedSets[loggedSets.length - 1];
    const plannedReps = formatRange(exercise.reps_min, exercise.reps_max);
    const plannedRir = formatRange(exercise.rir_min, exercise.rir_max);
    const detailParts = latestLoggedSet
      ? [
          `${loggedSets.length}/${exercise.sets} sets`,
          ...formatActualSetDetail(latestLoggedSet),
        ]
      : [
          `0/${exercise.sets} sets`,
          plannedReps ? `planned ${plannedReps}` : null,
          plannedRir ? `RIR ${plannedRir}` : null,
        ].filter((value): value is string => Boolean(value));

    return {
      key: String(exercise.id),
      name: exercise.name,
      detail: detailParts.join(" · "),
    };
  });
}

function todayWorkoutRows(
  workout: TodayWorkoutResponse | null,
): Array<{ key: string; name: string; detail: string }> {
  if (!workout?.exercises.length) {
    return [];
  }

  return workout.exercises.slice(0, 6).map((exercise) => {
    const detailParts = [
      exercise.sets === null ? null : `0/${exercise.sets} sets`,
      exercise.reps ? `planned ${exercise.reps}` : null,
    ].filter((value): value is string => Boolean(value));

    return {
      key: `${exercise.order}-${exercise.name}`,
      name: exercise.name,
      detail: detailParts.join(" · ") || "Workout details available",
    };
  });
}

function compactWorkoutRows(
  workout: TodayWorkoutResponse | null,
  currentWorkout: WorkoutCurrentResponse | null,
): Array<{ key: string; name: string; detail: string }> {
  const currentRows = currentWorkoutRows(currentWorkout);
  return currentRows.length > 0 ? currentRows : todayWorkoutRows(workout);
}

export default async function Home({
  searchParams,
}: {
  searchParams: SearchParams;
}) {
  const resolvedSearchParams = await searchParams;
  const todayQuery = resolveTodayQuery(resolvedSearchParams);
  const [{ data, error }, todayWorkoutResult, currentWorkoutResult] = await Promise.all([
    fetchDailyDriverToday(todayQuery),
    fetchTodayWorkout(todayQuery),
    fetchWorkoutCurrentFromBackend(todayQuery),
  ]);
  const workoutHref = buildTodayWorkoutHref(todayQuery);
  const currentUserId = todayQuery.userId ?? data?.user_id ?? getDefaultUserId();
  const foodHref = buildDailyWorkspaceHref(
    "food",
    currentUserId,
    todayQuery.date,
  );
  const recoveryHref = buildDailyWorkspaceHref(
    "recovery",
    currentUserId,
    todayQuery.date,
  );
  const displayDate = formatLongReadableDate(data?.target_date ?? todayQuery.date);
  const workoutMeta = data
    ? buildWorkoutMeta(
        todayWorkoutResult.data,
        data.workout.status,
        currentWorkoutResult.data,
      )
    : [];
  const workoutRows = compactWorkoutRows(
    todayWorkoutResult.data,
    currentWorkoutResult.data,
  );
  const [canonicalLoggedFoodsResult, personalLoggedFoodsResult] = data
    ? await Promise.all([
        fetchCanonicalFoodLogsFromBackend({
          userId: currentUserId,
          date: data.target_date,
        }),
        fetchPersonalFoodLogsFromBackend({
          userId: currentUserId,
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

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,var(--theme-canvas-glow),transparent_35%),linear-gradient(180deg,var(--theme-canvas-start)_0%,var(--theme-canvas)_100%)] px-3 py-3 text-text-strong sm:px-4 sm:py-6">
      <LiveDayRolloverBoundary requestedDate={todayQuery.date} />
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-3 pb-[calc(5.5rem+env(safe-area-inset-bottom))] sm:gap-4 md:pb-8 lg:gap-6 lg:px-2">
        <section className="rounded-2xl bg-[linear-gradient(160deg,var(--theme-header-surface-start),var(--theme-header-surface-end))] px-4 py-3 shadow-[0_20px_45px_-32px_rgba(15,23,42,0.45)] sm:rounded-[28px] sm:px-5 sm:py-4 lg:px-6 lg:py-5">
          <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between lg:gap-4">
            <div className="max-w-2xl space-y-1">
              <p className="hidden text-[0.72rem] font-semibold uppercase tracking-[0.2em] text-text-warm md:block">
                Today
              </p>
              <h1 className="text-xl font-semibold tracking-tight text-text-strong sm:text-2xl lg:text-[2rem]">
                {displayDate}
              </h1>
            </div>

            <div className="flex flex-col gap-2 lg:items-end">
              <p className="hidden text-[0.68rem] font-semibold uppercase tracking-[0.16em] text-text-muted md:block">
                User
              </p>
              <div className="flex items-center gap-2 lg:justify-end">
                <UserSwitcher
                  currentUserId={currentUserId}
                  showLabel={false}
                  selectClassName="bg-surface/90 py-2.5"
                />
                <ThemePreferenceControl />
              </div>
            </div>
          </div>
        </section>

        {error ? (
          <TodayCard title={error.heading} accent="warm">
            <div className="space-y-3">
              <p className="text-sm leading-6 text-text-body">{error.message}</p>
              {error.statusCode ? (
                <p className="text-xs uppercase tracking-[0.16em] text-text-muted">
                  Status {error.statusCode}
                </p>
              ) : null}
            </div>
          </TodayCard>
        ) : null}

        {!error && !data ? (
          <TodayCard title="Today is empty" accent="warm">
            <p className="text-sm leading-6 text-text-body">
              The backend did not return a usable Today response yet.
            </p>
          </TodayCard>
        ) : null}

        {data ? (
          <div className="grid gap-4 lg:grid-cols-[minmax(0,1.35fr)_minmax(340px,0.9fr)] lg:items-start lg:gap-5 xl:grid-cols-[minmax(0,1.45fr)_minmax(360px,0.95fr)]">
            <div className="min-w-0 space-y-3 lg:space-y-4">
              <NutritionMacroCard nutrition={data.nutrition} />
              <Link
                href={foodHref}
                className="flex min-h-11 items-center justify-between rounded-2xl bg-surface px-4 py-2.5 text-sm font-semibold !text-accent-text shadow-[0_18px_38px_-32px_rgba(15,23,42,0.5)] md:hidden"
              >
                Open Food workspace
                <span aria-hidden="true">→</span>
              </Link>
              <div
                id="food-workspace"
                className="hidden scroll-mt-3 sm:scroll-mt-6 md:block"
              >
                <FoodWorkspaceDeck
                  key={`${todayQuery.userId ?? data.user_id}:${data.target_date}`}
                  userId={todayQuery.userId ?? data.user_id}
                  targetDate={data.target_date}
                  requestedDate={todayQuery.date}
                />
              </div>
              <div className="grid gap-3 xl:grid-cols-2">
                <LoggedFoodsList
                  key={`logged-foods:${todayQuery.userId ?? data.user_id}:${data.target_date}`}
                  initialEntries={loggedFoodEntries}
                  initialError={loggedFoodsError}
                  userId={todayQuery.userId ?? data.user_id}
                  targetDate={data.target_date}
                  className="hidden md:block"
                />
                <TodayCard title="Today's Workout">
                  <div className="space-y-3">
                    <div className="flex items-start justify-between gap-3">
                      <span className="text-sm font-semibold text-text-body">
                        {getWorkoutSupportLine(data.workout.status)}
                      </span>
                      <StatusPill
                        label={formatWorkoutStatusLabel(data.workout.status)}
                        tone={workoutToneMap[data.workout.status]}
                      />
                    </div>
                    <div className="flex flex-wrap gap-2 text-xs">
                      {workoutMeta.map((item) => (
                        <span
                          key={item}
                          className="rounded-full bg-surface-muted px-3 py-1.5 font-semibold text-text-body"
                        >
                          {item}
                        </span>
                      ))}
                    </div>
                    {workoutRows.length > 0 ? (
                      <div className="divide-y divide-border-subtle rounded-2xl bg-surface-subtle px-4 py-2">
                        {workoutRows.map((exercise) => (
                          <div
                            key={exercise.key}
                            className="grid gap-1 py-2 text-sm sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center"
                          >
                            <span className="font-semibold text-text-primary">
                              {exercise.name}
                            </span>
                            <span className="text-text-secondary sm:text-right">
                              {exercise.detail}
                            </span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="rounded-2xl bg-surface-subtle px-4 py-3 text-sm text-text-body">
                        {data.workout.first_action_label}
                      </p>
                    )}
                    {data.workout.planned ? (
                      <Link
                        href={workoutHref}
                        className="inline-flex items-center justify-center rounded-2xl bg-action-primary px-4 py-2.5 text-sm font-semibold !text-action-primary-foreground transition hover:bg-action-primary-hover"
                      >
                        {getWorkoutActionLabel(data.workout.status)}
                      </Link>
                    ) : null}
                  </div>
                </TodayCard>
              </div>
            </div>

            <div className="min-w-0 space-y-4">
              <div
                id="recovery"
                className="hidden scroll-mt-3 sm:scroll-mt-6 md:block"
              >
                <RecoveryCheckInCard
                  userId={todayQuery.userId ?? data.user_id}
                  targetDate={data.target_date}
                  readiness={data.readiness}
                />
              </div>

              <TodayCard title="Recovery" className="md:hidden">
                <div className="space-y-2">
                  <div className="flex items-center justify-between gap-3">
                    <p className="font-semibold text-text-primary">
                      Readiness {data.readiness.score ?? "--"}
                    </p>
                    <span className="text-sm font-semibold capitalize text-text-secondary">
                      {data.readiness.status.replace("_", " ")}
                    </span>
                  </div>
                  <p className="text-sm text-text-body">
                    {data.readiness.headline}
                  </p>
                  <Link
                    href={recoveryHref}
                    className="inline-flex min-h-11 items-center font-semibold !text-accent-text"
                  >
                    Open Recovery workspace
                  </Link>
                </div>
              </TodayCard>

              {data.coach_note.enabled && data.coach_note.text ? (
                <TodayCard title="Coach Note" accent="warm">
                  <p className="text-sm leading-7 text-text-body">
                    {data.coach_note.text}
                  </p>
                </TodayCard>
              ) : null}
            </div>
          </div>
        ) : null}
      </div>
      <MobilePrimaryNav
        userId={currentUserId}
        date={todayQuery.date}
      />
    </main>
  );
}
