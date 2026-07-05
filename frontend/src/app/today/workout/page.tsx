import Link from "next/link";

import { DataQualityNote } from "@/components/DataQualityNote";
import { StatusPill } from "@/components/StatusPill";
import { TodayCard } from "@/components/TodayCard";
import { resolveTodayQuery } from "@/lib/dailyDriverApi";
import { fetchTodayWorkout } from "@/lib/todayWorkoutApi";
import { TodayWorkoutResponse, TodayWorkoutStatus } from "@/types/todayWorkout";

type SearchParams = Promise<Record<string, string | string[] | undefined>>;

const workoutToneMap: Record<
  TodayWorkoutStatus,
  "positive" | "caution" | "warning" | "neutral"
> = {
  preview: "caution",
  selected: "caution",
  in_progress: "positive",
  completed: "positive",
  not_available: "neutral",
};

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

function detailLabel(label: string, value: string | number | null): string | null {
  if (value === null || value === "") {
    return null;
  }

  return `${label}: ${value}`;
}

function exerciseMeta(exercise: TodayWorkoutResponse["exercises"][number]): string[] {
  return [
    detailLabel("Sets", exercise.sets),
    detailLabel("Reps", exercise.reps),
    exercise.weight !== null
      ? `Weight: ${exercise.weight}${exercise.weight_unit ? ` ${exercise.weight_unit}` : ""}`
      : null,
    detailLabel("Rest", exercise.rest_seconds ? `${exercise.rest_seconds}s` : null),
    detailLabel("Tempo", exercise.tempo),
  ].filter((value): value is string => Boolean(value));
}

export default async function WorkoutPage({
  searchParams,
}: {
  searchParams: SearchParams;
}) {
  const resolvedSearchParams = await searchParams;
  const todayQuery = resolveTodayQuery(resolvedSearchParams);
  const todayHref = buildTodayHref(todayQuery.userId, todayQuery.date);
  const { data, error } = await fetchTodayWorkout(todayQuery);

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
                Review the backend-owned workout plan for today without bouncing
                back to Streamlit.
              </p>
            </div>

            {data ? (
              <div className="grid grid-cols-2 gap-3 sm:max-w-md lg:min-w-[340px]">
                <div className="rounded-2xl bg-white/80 px-4 py-3 shadow-[0_14px_28px_-24px_rgba(15,23,42,0.45)]">
                  <p className="text-[0.68rem] font-semibold uppercase tracking-[0.16em] text-slate-500">
                    Date
                  </p>
                  <p className="mt-2 text-base font-semibold text-slate-900">
                    {data.target_date}
                  </p>
                </div>
                <div className="rounded-2xl bg-white/80 px-4 py-3 shadow-[0_14px_28px_-24px_rgba(15,23,42,0.45)]">
                  <p className="text-[0.68rem] font-semibold uppercase tracking-[0.16em] text-slate-500">
                    Source
                  </p>
                  <p className="mt-2 text-base font-semibold text-slate-900">
                    {data.source.replaceAll("_", " ")}
                  </p>
                </div>
              </div>
            ) : null}
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
          <TodayCard title="Workout is empty" accent="warm">
            <p className="text-sm leading-6 text-slate-700">
              The backend did not return a usable workout response yet.
            </p>
          </TodayCard>
        ) : null}

        {data ? (
          <div className="grid gap-4 lg:grid-cols-[minmax(0,1.45fr)_minmax(320px,0.95fr)] lg:gap-6 xl:grid-cols-[minmax(0,1.55fr)_minmax(360px,1fr)]">
            <TodayCard
              title={data.title}
              eyebrow="Workout Plan"
              accent="highlight"
              className="lg:col-start-1 lg:row-start-1"
            >
              <div className="space-y-4">
                <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                  <div className="space-y-2">
                    <p className="text-lg font-semibold text-slate-950">
                      {data.summary}
                    </p>
                    <p className="text-sm leading-6 text-slate-700">
                      {data.focus ?? "Workout focus is limited for this date."}
                    </p>
                  </div>
                  <StatusPill
                    label={data.status.replaceAll("_", " ")}
                    tone={workoutToneMap[data.status]}
                  />
                </div>
                <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                  <div className="rounded-2xl bg-slate-50 px-4 py-3">
                    <p className="text-xs uppercase tracking-[0.16em] text-slate-500">
                      Duration
                    </p>
                    <p className="mt-2 font-semibold text-slate-900">
                      {data.estimated_duration_minutes
                        ? `${data.estimated_duration_minutes} min`
                        : "Not available"}
                    </p>
                  </div>
                  <div className="rounded-2xl bg-slate-50 px-4 py-3">
                    <p className="text-xs uppercase tracking-[0.16em] text-slate-500">
                      Exercises
                    </p>
                    <p className="mt-2 font-semibold text-slate-900">
                      {data.exercises.length}
                    </p>
                  </div>
                  <div className="rounded-2xl bg-slate-50 px-4 py-3">
                    <p className="text-xs uppercase tracking-[0.16em] text-slate-500">
                      Generated
                    </p>
                    <p className="mt-2 font-semibold text-slate-900">
                      {data.generated_at ?? "Current preview"}
                    </p>
                  </div>
                </div>
              </div>
            </TodayCard>

            <TodayCard
              title="Workout Details"
              className="lg:col-start-2 lg:row-start-1"
            >
              <div className="space-y-4">
                <div className="rounded-2xl bg-slate-50 px-4 py-3">
                  <p className="text-xs uppercase tracking-[0.16em] text-slate-500">
                    Workout ID
                  </p>
                  <p className="mt-2 text-sm font-semibold text-slate-900">
                    {data.workout_id ?? "Not assigned"}
                  </p>
                </div>
                <div className="rounded-2xl bg-slate-50 px-4 py-3">
                  <p className="text-xs uppercase tracking-[0.16em] text-slate-500">
                    Equipment
                  </p>
                  <p className="mt-2 text-sm font-semibold text-slate-900">
                    {data.equipment.length > 0
                      ? data.equipment.join(", ")
                      : "No equipment details available"}
                  </p>
                </div>
                <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3">
                  <p className="text-xs uppercase tracking-[0.16em] text-slate-500">
                    Return Path
                  </p>
                  <Link
                    href={todayHref}
                    className="mt-2 inline-flex text-sm font-semibold text-emerald-700 transition hover:text-emerald-900"
                  >
                    Back to the Today dashboard
                  </Link>
                </div>
              </div>
            </TodayCard>

            <TodayCard
              title="Exercises"
              className="lg:col-start-1 lg:row-start-2"
            >
              {data.exercises.length > 0 ? (
                <div className="space-y-3">
                  {data.exercises.map((exercise) => (
                    <article
                      key={`${exercise.exercise_id ?? exercise.name}-${exercise.order}`}
                      className="rounded-[24px] border border-slate-200 bg-slate-50/80 p-4"
                    >
                      <div className="flex flex-col gap-3">
                        <div className="space-y-2">
                          <p className="text-[0.72rem] font-semibold uppercase tracking-[0.16em] text-slate-500">
                            {exercise.section ?? "Exercise"} {exercise.order}
                          </p>
                          <h2 className="text-xl font-semibold text-slate-950">
                            {exercise.name}
                          </h2>
                          <div className="flex flex-wrap gap-2">
                            {exerciseMeta(exercise).map((item) => (
                              <span
                                key={item}
                                className="rounded-full bg-white px-3 py-1 text-xs font-medium text-slate-700"
                              >
                                {item}
                              </span>
                            ))}
                          </div>
                        </div>
                      </div>
                      {exercise.notes ? (
                        <p className="mt-4 text-sm leading-6 text-slate-700">
                          {exercise.notes}
                        </p>
                      ) : null}
                      {exercise.substitution_notes ? (
                        <p className="mt-3 rounded-2xl bg-amber-50 px-4 py-3 text-sm leading-6 text-amber-900">
                          {exercise.substitution_notes}
                        </p>
                      ) : null}
                    </article>
                  ))}
                </div>
              ) : (
                <p className="text-sm leading-6 text-slate-700">
                  No exercise details are available for this date.
                </p>
              )}
            </TodayCard>

            <DataQualityNote
              title="Data Gaps"
              items={data.data_gaps}
              className="lg:col-start-2 lg:row-start-2"
            />
            <DataQualityNote
              title="Limitations"
              items={data.limitations}
              className="lg:col-start-2 lg:row-start-3"
            />
          </div>
        ) : null}
      </div>
    </main>
  );
}
