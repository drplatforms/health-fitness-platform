import { DataQualityNote } from "@/components/DataQualityNote";
import { NextActionCard } from "@/components/NextActionCard";
import { StatusPill } from "@/components/StatusPill";
import { TodayCard } from "@/components/TodayCard";
import {
  fetchDailyDriverToday,
  resolveTodayQuery,
} from "@/lib/dailyDriverApi";
import {
  DailyDriverNutritionStatus,
  DailyDriverReadinessStatus,
  DailyDriverWorkoutStatus,
} from "@/types/dailyDriver";

type SearchParams = Promise<Record<string, string | string[] | undefined>>;

const readinessToneMap: Record<
  DailyDriverReadinessStatus,
  "positive" | "caution" | "warning" | "neutral"
> = {
  ready: "positive",
  light: "caution",
  recover: "warning",
  unknown: "neutral",
};

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

const nutritionToneMap: Record<
  DailyDriverNutritionStatus,
  "positive" | "caution" | "warning" | "neutral"
> = {
  on_track: "positive",
  behind: "warning",
  complete: "positive",
  not_logged: "caution",
  unknown: "neutral",
};

function formatNumber(value: number | null, suffix = ""): string {
  if (value === null) {
    return "Not available";
  }

  return `${value.toLocaleString()}${suffix}`;
}

export default async function Home({
  searchParams,
}: {
  searchParams: SearchParams;
}) {
  const resolvedSearchParams = await searchParams;
  const todayQuery = resolveTodayQuery(resolvedSearchParams);
  const { data, error } = await fetchDailyDriverToday(todayQuery);

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(251,191,36,0.16),_transparent_35%),linear-gradient(180deg,#fffdf7_0%,#f8fafc_100%)] px-4 py-6 text-slate-950">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-4 pb-8 lg:gap-6 lg:px-2">
        <section className="rounded-[32px] bg-[linear-gradient(160deg,rgba(255,255,255,0.96),rgba(255,247,237,0.96))] p-6 shadow-[0_20px_45px_-32px_rgba(15,23,42,0.45)] lg:px-8 lg:py-7">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-2xl">
              <p className="text-[0.72rem] font-semibold uppercase tracking-[0.2em] text-amber-700">
                Today
              </p>
              <h1 className="mt-3 text-4xl font-semibold tracking-tight text-slate-950 lg:text-[3.5rem]">
                What should I do now?
              </h1>
              <p className="mt-3 max-w-xl text-sm leading-6 text-slate-600 lg:text-base">
                Open one screen, see today&apos;s training direction, nutrition
                mission, and the next action that matters.
              </p>
            </div>

            {data ? (
              <div className="grid grid-cols-2 gap-3 sm:max-w-sm lg:min-w-[320px]">
                <div className="rounded-2xl bg-white/80 px-4 py-3 shadow-[0_14px_28px_-24px_rgba(15,23,42,0.45)]">
                  <p className="text-[0.68rem] font-semibold uppercase tracking-[0.16em] text-slate-500">
                    User
                  </p>
                  <p className="mt-2 text-base font-semibold text-slate-900">
                    {data.user_id}
                  </p>
                </div>
                <div className="rounded-2xl bg-white/80 px-4 py-3 shadow-[0_14px_28px_-24px_rgba(15,23,42,0.45)]">
                  <p className="text-[0.68rem] font-semibold uppercase tracking-[0.16em] text-slate-500">
                    Date
                  </p>
                  <p className="mt-2 text-base font-semibold text-slate-900">
                    {data.target_date}
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
          <TodayCard title="Today is empty" accent="warm">
            <p className="text-sm leading-6 text-slate-700">
              The backend did not return a usable Today response yet.
            </p>
          </TodayCard>
        ) : null}

        {data ? (
          <div className="grid gap-4 lg:grid-cols-[minmax(0,1.4fr)_minmax(320px,0.95fr)] lg:gap-6 xl:grid-cols-[minmax(0,1.5fr)_minmax(360px,1fr)]">
            <NextActionCard
              action={data.next_action}
              className="lg:col-start-1 lg:row-start-1 lg:p-7"
            />

            <TodayCard
              title="Readiness"
              eyebrow="Daily Driver"
              className="lg:col-start-2 lg:row-start-1"
            >
              <div className="space-y-3">
                <StatusPill
                  label={data.readiness.status.replace("_", " ")}
                  tone={readinessToneMap[data.readiness.status]}
                />
                <p className="text-2xl font-semibold tracking-tight text-slate-950">
                  {data.readiness.headline}
                </p>
                <p className="text-sm leading-6 text-slate-700">
                  {data.readiness.reason}
                </p>
                <p className="text-xs uppercase tracking-[0.16em] text-slate-500">
                  Confidence {data.readiness.confidence}
                </p>
              </div>
            </TodayCard>

            <TodayCard title="Workout" className="lg:col-start-1 lg:row-start-2">
              <div className="space-y-3">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-lg font-semibold text-slate-950">
                      {data.workout.title}
                    </p>
                    <p className="text-sm leading-6 text-slate-700">
                      {data.workout.summary}
                    </p>
                  </div>
                  <StatusPill
                    label={data.workout.status.replace("_", " ")}
                    tone={workoutToneMap[data.workout.status]}
                  />
                </div>
                <div className="rounded-2xl bg-slate-50 px-4 py-3 text-sm font-medium text-slate-800">
                  {data.workout.first_action_label}
                </div>
              </div>
            </TodayCard>

            <TodayCard
              title="Nutrition"
              className="lg:col-start-2 lg:row-start-2"
            >
              <div className="space-y-3">
                <div className="flex items-start justify-between gap-3">
                  <p className="text-sm leading-6 text-slate-700">
                    {data.nutrition.today_mission}
                  </p>
                  <StatusPill
                    label={data.nutrition.status.replace("_", " ")}
                    tone={nutritionToneMap[data.nutrition.status]}
                  />
                </div>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div className="rounded-2xl bg-slate-50 px-4 py-3">
                    <p className="text-xs uppercase tracking-[0.16em] text-slate-500">
                      Calories
                    </p>
                    <p className="mt-2 font-semibold text-slate-900">
                      {formatNumber(data.nutrition.calories_logged)} /{" "}
                      {formatNumber(data.nutrition.calorie_target)}
                    </p>
                  </div>
                  <div className="rounded-2xl bg-slate-50 px-4 py-3">
                    <p className="text-xs uppercase tracking-[0.16em] text-slate-500">
                      Protein
                    </p>
                    <p className="mt-2 font-semibold text-slate-900">
                      {formatNumber(data.nutrition.protein_logged_g, "g")} /{" "}
                      {formatNumber(data.nutrition.protein_target_g, "g")}
                    </p>
                  </div>
                </div>
              </div>
            </TodayCard>

            {data.coach_note.enabled && data.coach_note.text ? (
              <TodayCard
                title="Coach Note"
                accent="warm"
                className="lg:col-start-1 lg:row-start-3"
              >
                <p className="text-sm leading-7 text-slate-800">
                  {data.coach_note.text}
                </p>
              </TodayCard>
            ) : null}

            <DataQualityNote
              title="Data Gaps"
              items={data.data_gaps}
              className="lg:col-start-2 lg:row-start-3"
            />
            <DataQualityNote
              title="Limitations"
              items={data.limitations}
              className="lg:col-start-2 lg:row-start-4"
            />
          </div>
        ) : null}
      </div>
    </main>
  );
}
