"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState, useSyncExternalStore } from "react";

import { getBrowserLocalDateString } from "@/lib/dateFormatting";
import { buildTodayWorkoutHref } from "@/lib/todayWorkoutApi";
import {
  buildWeeklyWorkoutHref,
  createWeeklyTrainingPlan,
  fetchWeeklyTrainingPlan,
  previewWeeklySessionTitles,
  resolveVisibleWeekStart,
  shiftWeekStart,
  updateWeeklyTrainingPlan,
  weekDateStrings,
} from "@/lib/weeklyTrainingPlanApi";
import {
  WeeklyTrainingPlan,
  WeeklyTrainingPlanDay,
  WeeklyWorkoutSizePreference,
} from "@/types/weeklyTrainingPlan";

const weekdayLabels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const statusLabels: Record<string, string> = {
  rest: "Rest",
  planned: "Planned",
  today: "Today",
  selected: "Selected",
  in_progress: "In progress",
  completed: "Completed",
  missed: "Missed",
  extra_workout: "Extra workout",
};
const statusClasses: Record<string, string> = {
  completed: "bg-positive-surface text-positive-foreground-strong",
  in_progress: "bg-caution-surface text-caution-foreground-strong",
  selected: "bg-caution-surface text-caution-foreground-strong",
  today: "bg-surface-highlighted text-accent-text",
  missed: "bg-danger-surface text-danger-foreground",
  extra_workout: "bg-positive-surface text-positive-foreground-strong",
  planned: "bg-neutral-surface text-neutral-foreground",
  rest: "bg-surface-muted text-text-secondary",
};

interface WeeklyTrainingPlannerProps {
  userId: number;
  initialWeekStartDate?: string;
}

function subscribeToHydration() {
  return () => undefined;
}

function localDate(value: string): Date {
  const [year, month, day] = value.split("-").map(Number);
  return new Date(year, month - 1, day);
}

function shortDate(value: string): string {
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
  }).format(localDate(value));
}

function weekRangeLabel(start: string, end: string): string {
  const startDate = localDate(start);
  const endDate = localDate(end);
  const startLabel = new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
  }).format(startDate);
  const endLabel = new Intl.DateTimeFormat(undefined, {
    month: startDate.getMonth() === endDate.getMonth() ? undefined : "short",
    day: "numeric",
  }).format(endDate);
  return `${startLabel} – ${endLabel}`;
}

function dayTrainingWeekdays(plan: WeeklyTrainingPlan): number[] {
  return plan.days
    .filter((day) => day.day_type === "training")
    .map((day) => day.day_index);
}

function splitPreview(trainingWeekdays: number[]) {
  const titleByWeekday = new Map(
    previewWeeklySessionTitles(trainingWeekdays).map((item) => [
      item.weekday,
      item.title,
    ]),
  );
  return weekdayLabels.map((label, index) => ({
    label,
    title: titleByWeekday.get(index) ?? "Rest",
  }));
}

function DayRow({
  day,
  userId,
  currentDate,
}: {
  day: WeeklyTrainingPlanDay;
  userId: number;
  currentDate: string;
}) {
  const isCurrentDate = day.training_date === currentDate;
  return (
    <div className="grid grid-cols-[3.25rem_minmax(0,1fr)_auto] items-center gap-2 rounded-xl bg-surface px-3 py-2.5 ring-1 ring-border">
      <div>
        <p className="text-sm font-semibold text-text-strong">
          {weekdayLabels[day.day_index]}
        </p>
        <p className="type-compact-metadata text-text-muted">{shortDate(day.training_date)}</p>
      </div>
      <div className="min-w-0">
        <p className="truncate text-sm font-semibold text-text-primary">
          {day.session_title ?? "Rest"}
        </p>
        {isCurrentDate && day.day_type === "training" ? (
          <Link
            href={buildTodayWorkoutHref({ userId })}
            className="text-xs font-semibold text-accent-text underline-offset-2 hover:underline"
          >
            Open today&apos;s workout
          </Link>
        ) : null}
      </div>
      <span
        className={`type-compact-metadata whitespace-nowrap rounded-full px-2 py-1 font-semibold uppercase tracking-[0.08em] ${
          statusClasses[day.derived_status] ?? statusClasses.rest
        }`}
      >
        {statusLabels[day.derived_status] ?? day.derived_status}
      </span>
    </div>
  );
}

export function WeeklyTrainingPlanner({
  userId,
  initialWeekStartDate,
}: WeeklyTrainingPlannerProps) {
  const router = useRouter();
  const isHydrated = useSyncExternalStore(
    subscribeToHydration,
    () => true,
    () => false,
  );
  const [weekOverride, setWeekOverride] = useState(initialWeekStartDate ?? "");
  const [plan, setPlan] = useState<WeeklyTrainingPlan | null>(null);
  const [trainingWeekdays, setTrainingWeekdays] = useState<number[]>([0, 2, 4]);
  const [workoutSize, setWorkoutSize] =
    useState<WeeklyWorkoutSizePreference>("standard");
  const [isEditing, setIsEditing] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const visibleWeekStart = isHydrated
    ? resolveVisibleWeekStart(weekOverride || initialWeekStartDate)
    : "";
  const visibleDates = visibleWeekStart ? weekDateStrings(visibleWeekStart) : [];
  const currentDate = isHydrated ? getBrowserLocalDateString() : "";

  useEffect(() => {
    if (!visibleWeekStart || !currentDate) {
      return;
    }
    let cancelled = false;
    async function loadPlan() {
      setIsLoading(true);
      setError(null);
      setMessage(null);
      const result = await fetchWeeklyTrainingPlan(
        userId,
        visibleWeekStart,
        currentDate,
      );
      if (cancelled) {
        return;
      }
      if (result.error) {
        setPlan(null);
        setError(result.error.message);
      } else {
        const nextPlan = result.data?.plan ?? null;
        setPlan(nextPlan);
        setTrainingWeekdays(
          nextPlan ? dayTrainingWeekdays(nextPlan) : [0, 2, 4],
        );
        setWorkoutSize(
          nextPlan?.default_workout_size_preference ?? "standard",
        );
        setIsEditing(false);
      }
      setIsLoading(false);
    }
    void loadPlan();
    return () => {
      cancelled = true;
    };
  }, [currentDate, userId, visibleWeekStart]);

  function navigateWeek(offset: number) {
    const nextWeek = shiftWeekStart(visibleWeekStart, offset);
    setWeekOverride(nextWeek);
    router.replace(buildWeeklyWorkoutHref(userId, nextWeek));
  }

  function returnToCurrentWeek() {
    setWeekOverride("");
    router.replace(buildWeeklyWorkoutHref(userId));
  }

  function toggleWeekday(dayIndex: number) {
    setTrainingWeekdays((current) =>
      current.includes(dayIndex)
        ? current.filter((value) => value !== dayIndex)
        : [...current, dayIndex].sort((a, b) => a - b),
    );
  }

  async function savePlan() {
    if (trainingWeekdays.length < 1 || trainingWeekdays.length > 6) {
      setError("Choose between 1 and 6 training days.");
      return;
    }
    setIsSaving(true);
    setError(null);
    setMessage(null);
    const mutation = {
      weekStartDate: visibleWeekStart,
      trainingWeekdays,
      defaultWorkoutSizePreference: workoutSize,
      currentDate,
    };
    const result = plan
      ? await updateWeeklyTrainingPlan(userId, plan, mutation)
      : await createWeeklyTrainingPlan(userId, mutation);
    if (result.error) {
      setError(result.error.message);
    } else if (result.data?.plan) {
      setPlan(result.data.plan);
      setTrainingWeekdays(dayTrainingWeekdays(result.data.plan));
      setWorkoutSize(result.data.plan.default_workout_size_preference);
      setIsEditing(false);
      setMessage(plan ? "Week updated." : "Week planned.");
    }
    setIsSaving(false);
  }

  const editorVisible = !plan || isEditing;
  const previewRows = splitPreview(trainingWeekdays);
  const isCurrentWeek = visibleWeekStart
    ? visibleWeekStart === resolveVisibleWeekStart()
    : true;

  return (
    <section className="space-y-3">
      <div className="rounded-2xl bg-surface px-3 py-3 ring-1 ring-border sm:px-4">
        <div className="flex items-center justify-between gap-2">
          <button
            type="button"
            onClick={() => navigateWeek(-1)}
            className="min-h-10 rounded-xl bg-surface-muted px-3 text-sm font-semibold text-text-body hover:bg-surface-interactive-hover"
            aria-label="Previous week"
          >
            Previous
          </button>
          <div className="min-w-0 text-center">
            <h2 className="text-lg font-semibold text-text-strong">
              {isCurrentWeek ? "This Week" : "Training Week"}
            </h2>
            <p className="text-sm text-text-secondary">
              {visibleDates.length
                ? weekRangeLabel(visibleDates[0], visibleDates[6])
                : "Loading dates…"}
            </p>
          </div>
          <button
            type="button"
            onClick={() => navigateWeek(1)}
            className="min-h-10 rounded-xl bg-surface-muted px-3 text-sm font-semibold text-text-body hover:bg-surface-interactive-hover"
            aria-label="Next week"
          >
            Next
          </button>
        </div>
        {!isCurrentWeek ? (
          <button
            type="button"
            onClick={returnToCurrentWeek}
            className="mx-auto mt-2 block text-xs font-semibold text-accent-text underline-offset-2 hover:underline"
          >
            Return to this week
          </button>
        ) : null}
      </div>

      {isLoading ? (
        <div className="rounded-2xl bg-neutral-surface px-4 py-4 text-sm font-medium text-neutral-foreground">
          Loading weekly plan…
        </div>
      ) : null}
      {error ? (
        <div role="alert" className="rounded-2xl bg-danger-surface px-4 py-3 text-sm font-medium text-danger-foreground">
          {error}
        </div>
      ) : null}
      {message ? (
        <div className="rounded-2xl bg-positive-surface px-4 py-3 text-sm font-medium text-positive-foreground-strong">
          {message}
        </div>
      ) : null}

      {!isLoading && plan && !editorVisible ? (
        <div className="space-y-2">
          {plan.days.map((day) => (
            <DayRow key={day.id} day={day} userId={userId} currentDate={currentDate} />
          ))}
          <div className="flex items-center justify-between gap-3 rounded-2xl bg-surface-subtle px-3 py-3">
            <p className="text-sm text-text-body">
              Default size: <span className="font-semibold capitalize text-text-strong">{plan.default_workout_size_preference}</span>
            </p>
            {plan.status === "active" ? (
              <button
                type="button"
                onClick={() => setIsEditing(true)}
                className="rounded-xl bg-action-primary px-4 py-2 text-sm font-semibold text-action-primary-foreground hover:bg-action-primary-hover"
              >
                Edit Week
              </button>
            ) : (
              <span className="text-xs font-semibold uppercase tracking-[0.08em] text-text-muted">Read only</span>
            )}
          </div>
        </div>
      ) : null}

      {!isLoading && editorVisible ? (
        <div className="space-y-3 rounded-2xl bg-surface px-3 py-4 ring-1 ring-border sm:px-4">
          <div>
            <h3 className="text-lg font-semibold text-text-strong">
              {plan ? "Edit Week" : "Plan My Week"}
            </h3>
            <p className="mt-1 text-sm text-text-secondary">
              Choose 1–6 training days. Exact exercises are generated day-of.
            </p>
          </div>

          <fieldset>
            <legend className="text-xs font-semibold uppercase tracking-[0.12em] text-text-muted">Training days</legend>
            <div className="mt-2 grid grid-cols-7 gap-1.5">
              {weekdayLabels.map((label, index) => {
                const selected = trainingWeekdays.includes(index);
                const protectedDay = plan?.days[index]?.is_protected ?? false;
                return (
                  <button
                    key={label}
                    type="button"
                    onClick={() => toggleWeekday(index)}
                    disabled={protectedDay}
                    aria-pressed={selected}
                    title={plan?.days[index]?.protection_reason ?? undefined}
                    className={`min-h-11 rounded-xl px-1 text-xs font-semibold transition disabled:cursor-not-allowed disabled:opacity-60 ${
                      selected
                        ? "bg-action-primary text-action-primary-foreground"
                        : "bg-surface-muted text-text-body hover:bg-surface-interactive-hover"
                    }`}
                  >
                    {label}
                  </button>
                );
              })}
            </div>
          </fieldset>

          <fieldset>
            <legend className="text-xs font-semibold uppercase tracking-[0.12em] text-text-muted">Default session size</legend>
            <div className="mt-2 grid grid-cols-3 gap-2">
              {(["quick", "standard", "extended"] as const).map((size) => (
                <button
                  key={size}
                  type="button"
                  onClick={() => setWorkoutSize(size)}
                  aria-pressed={workoutSize === size}
                  className={`rounded-xl px-2 py-2 text-sm font-semibold capitalize ${
                    workoutSize === size
                      ? "bg-action-primary text-action-primary-foreground"
                      : "bg-surface-muted text-text-body hover:bg-surface-interactive-hover"
                  }`}
                >
                  {size}
                </button>
              ))}
            </div>
          </fieldset>

          <div className="grid grid-cols-2 gap-1.5 sm:grid-cols-4 lg:grid-cols-7">
            {previewRows.map((row) => (
              <div key={row.label} className="rounded-xl bg-surface-subtle px-2 py-2">
                <p className="type-compact-metadata font-semibold uppercase tracking-[0.08em] text-text-muted">{row.label}</p>
                <p className="mt-1 text-xs font-semibold text-text-primary">{row.title}</p>
              </div>
            ))}
          </div>

          <div className="flex gap-2">
            {plan ? (
              <button
                type="button"
                onClick={() => {
                  setIsEditing(false);
                  setTrainingWeekdays(dayTrainingWeekdays(plan));
                  setWorkoutSize(plan.default_workout_size_preference);
                  setError(null);
                }}
                className="flex-1 rounded-xl bg-surface-muted px-4 py-2.5 text-sm font-semibold text-text-body hover:bg-surface-interactive-hover"
              >
                Cancel
              </button>
            ) : null}
            <button
              type="button"
              onClick={() => void savePlan()}
              disabled={isSaving || trainingWeekdays.length < 1 || trainingWeekdays.length > 6}
              className="flex-1 rounded-xl bg-action-primary px-4 py-2.5 text-sm font-semibold text-action-primary-foreground hover:bg-action-primary-hover disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isSaving ? "Saving…" : plan ? "Save Changes" : "Save Week"}
            </button>
          </div>
        </div>
      ) : null}
    </section>
  );
}
