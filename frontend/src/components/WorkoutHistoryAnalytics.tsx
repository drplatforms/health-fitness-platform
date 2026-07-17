"use client";

import { useEffect, useState } from "react";

import {
  describeWorkingLoadTrend,
  exerciseAnalyticsKey,
  fetchWorkoutExerciseHistoryAnalytics,
  WorkoutExerciseHistoryAnalyticsApiResult,
} from "@/lib/workoutExerciseHistoryApi";
import { ExerciseHistoryAnalyticsSummary } from "@/types/workoutExerciseHistory";

export function WorkoutHistoryAnalytics({ userId }: { userId: number }) {
  return <WorkoutHistoryAnalyticsForUser key={userId} userId={userId} />;
}

function WorkoutHistoryAnalyticsForUser({ userId }: { userId: number }) {
  const [result, setResult] =
    useState<WorkoutExerciseHistoryAnalyticsApiResult | null>(null);
  const [selectedExerciseKey, setSelectedExerciseKey] = useState("");
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    let isCurrent = true;
    void fetchWorkoutExerciseHistoryAnalytics(userId).then((nextResult) => {
      if (!isCurrent) {
        return;
      }
      setResult(nextResult);
      setSelectedExerciseKey(
        nextResult.data?.exercises[0]
          ? exerciseAnalyticsKey(nextResult.data.exercises[0])
          : "",
      );
    });
    return () => {
      isCurrent = false;
    };
  }, [userId]);

  const exercises = result?.data?.exercises ?? [];
  const selectedExercise =
    exercises.find(
      (exercise) => exerciseAnalyticsKey(exercise) === selectedExerciseKey,
    ) ?? exercises[0];
  const visibleExercises = filterExercises(
    exercises,
    searchQuery,
    selectedExercise,
  );

  if (result === null) {
    return (
      <section className="rounded-2xl bg-surface px-4 py-5 text-sm text-text-body ring-1 ring-border">
        Loading training history…
      </section>
    );
  }

  if (result.error || !result.data) {
    return (
      <section className="rounded-2xl bg-danger-surface px-4 py-5">
        <h2 className="font-semibold text-danger-foreground">
          {result.error?.heading ?? "Unable to load training history"}
        </h2>
        <p className="mt-1 text-sm text-text-body">
          {result.error?.message ?? "Refresh the page to try again."}
        </p>
      </section>
    );
  }

  if (!result.data.overview.has_history) {
    return (
      <section className="rounded-2xl bg-surface px-4 py-6 text-sm text-text-body ring-1 ring-border">
        Complete and log a workout to build your exercise history.
      </section>
    );
  }

  const overview = result.data.overview;
  return (
    <div className="space-y-3 sm:space-y-4">
      <section className="rounded-2xl bg-surface px-4 py-4 ring-1 ring-border sm:px-5">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <div>
            <p className="text-[0.7rem] font-semibold uppercase tracking-[0.16em] text-text-muted">
              Training history
            </p>
            <h2 className="mt-1 text-lg font-semibold text-text-strong">
              Last {result.data.lookback_days} days
            </h2>
          </div>
          <p className="text-xs text-text-secondary">
            Completed planned workouts only
          </p>
        </div>
        <dl className="mt-3 grid grid-cols-2 gap-x-4 gap-y-3 border-t border-border-subtle pt-3 sm:grid-cols-4">
          <OverviewMetric
            label="Completed workouts"
            value={String(overview.completed_workout_count)}
          />
          <OverviewMetric
            label="Completed sets"
            value={String(overview.completed_set_count)}
          />
          <OverviewMetric
            label="Exercises trained"
            value={String(overview.distinct_effective_exercise_count)}
          />
          <OverviewMetric
            label="Most recent"
            value={formatHistoryDate(
              overview.most_recent_completed_workout_date,
              true,
            )}
          />
        </dl>
      </section>

      {selectedExercise ? (
        <section className="rounded-2xl bg-surface px-4 py-4 ring-1 ring-border sm:px-5 sm:py-5">
          <div className="grid gap-3 border-b border-border-subtle pb-4 md:grid-cols-[minmax(0,1fr)_minmax(15rem,20rem)] md:items-end">
            <div>
              <p className="text-[0.7rem] font-semibold uppercase tracking-[0.16em] text-text-muted">
                Exercise history
              </p>
              <h2 className="mt-1 text-xl font-semibold text-text-strong">
                {selectedExercise.exercise_name}
              </h2>
              <p className="mt-1 text-sm text-text-body">
                {selectedExercise.completed_session_count} completed{" "}
                {selectedExercise.completed_session_count === 1
                  ? "session"
                  : "sessions"}
                {selectedExercise.last_performed_at
                  ? ` • Last performed ${formatHistoryDate(selectedExercise.last_performed_at)}`
                  : ""}
              </p>
            </div>

            <div className="grid grid-cols-[minmax(0,1fr)_minmax(0,1fr)] gap-2">
              <label className="col-span-2 space-y-1 text-xs font-semibold text-text-secondary">
                <span>Find an exercise</span>
                <input
                  type="search"
                  value={searchQuery}
                  onChange={(event) => setSearchQuery(event.target.value)}
                  placeholder="Search history"
                  className="min-h-11 w-full rounded-xl border border-border bg-surface-subtle px-3 text-base text-text-strong outline-none focus:border-focus-subtle sm:text-sm"
                />
              </label>
              <label className="col-span-2 space-y-1 text-xs font-semibold text-text-secondary">
                <span>Exercise</span>
                <select
                  value={exerciseAnalyticsKey(selectedExercise)}
                  onChange={(event) => setSelectedExerciseKey(event.target.value)}
                  className="min-h-11 w-full rounded-xl border border-border bg-surface-subtle px-3 text-base text-text-strong outline-none focus:border-focus-subtle sm:text-sm"
                >
                  {visibleExercises.map((exercise) => (
                    <option
                      key={exerciseAnalyticsKey(exercise)}
                      value={exerciseAnalyticsKey(exercise)}
                    >
                      {exercise.exercise_name}
                    </option>
                  ))}
                </select>
              </label>
            </div>
          </div>

          <SelectedExerciseSummary exercise={selectedExercise} />
        </section>
      ) : null}
    </div>
  );
}

function OverviewMetric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs text-text-secondary">{label}</dt>
      <dd className="mt-0.5 text-lg font-semibold text-text-strong">{value}</dd>
    </div>
  );
}

function SelectedExerciseSummary({
  exercise,
}: {
  exercise: ExerciseHistoryAnalyticsSummary;
}) {
  const trendText = describeWorkingLoadTrend(
    exercise.recent_working_load_trend,
  );
  return (
    <div className="pt-4">
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        <SummaryItem
          label="Latest session"
          value={exercise.latest_completed_session_summary}
        />
        {exercise.recent_best_set ? (
          <SummaryItem
            label="Recent best logged set"
            value={exercise.recent_best_set.summary}
          />
        ) : null}
        {trendText ? <SummaryItem label="Working-load trend" value={trendText} /> : null}
      </div>

      {exercise.limitation ? (
        <p className="mt-3 rounded-xl bg-caution-surface px-3 py-2 text-xs leading-5 text-caution-foreground">
          {exercise.limitation}
        </p>
      ) : null}

      <div className="mt-4">
        <h3 className="text-sm font-semibold text-text-strong">
          Recent sessions
        </h3>
        <ul className="mt-2 divide-y divide-border-subtle border-y border-border-subtle">
          {exercise.recent_sessions.map((session, index) => (
            <li
              key={`${session.performed_at ?? "unknown"}-${index}`}
              className="grid gap-0.5 py-3 sm:grid-cols-[8rem_minmax(0,1fr)] sm:gap-4"
            >
              <p className="text-sm font-semibold text-text-primary">
                {formatHistoryDate(session.performed_at, true)}
              </p>
              <div className="min-w-0">
                <p className="text-sm text-text-body">{session.summary}</p>
                <p className="mt-0.5 text-xs text-text-secondary">
                  {session.completed_set_count} of {session.planned_set_count}{" "}
                  planned sets logged
                </p>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

function SummaryItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl bg-surface-subtle px-3 py-3 ring-1 ring-border-subtle">
      <p className="text-[0.68rem] font-semibold uppercase tracking-[0.12em] text-text-muted">
        {label}
      </p>
      <p className="mt-1 text-sm font-medium leading-5 text-text-primary">
        {value}
      </p>
    </div>
  );
}

function filterExercises(
  exercises: ExerciseHistoryAnalyticsSummary[],
  searchQuery: string,
  selectedExercise: ExerciseHistoryAnalyticsSummary | undefined,
): ExerciseHistoryAnalyticsSummary[] {
  const query = searchQuery.trim().toLowerCase();
  const matches = query
    ? exercises.filter((exercise) =>
        exercise.exercise_name.toLowerCase().includes(query),
      )
    : exercises;
  if (
    selectedExercise &&
    !matches.some(
      (exercise) =>
        exerciseAnalyticsKey(exercise) === exerciseAnalyticsKey(selectedExercise),
    )
  ) {
    return [selectedExercise, ...matches];
  }
  return matches;
}

function formatHistoryDate(value: string | null, includeYear = false): string {
  if (!value) {
    return "Not available";
  }
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    ...(includeYear ? { year: "numeric" as const } : {}),
  }).format(new Date(`${value}T00:00:00`));
}
