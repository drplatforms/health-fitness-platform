"use client";

import { useEffect, useState } from "react";

import { DataQualityNote } from "@/components/DataQualityNote";
import { StatusPill } from "@/components/StatusPill";
import { TodayCard } from "@/components/TodayCard";
import {
  fetchWorkoutCurrent,
  fetchWorkoutPreview,
  selectWorkoutPreview,
  startWorkoutPlan,
} from "@/lib/todayWorkoutApi";
import {
  ApprovedWorkoutPlanPreview,
  WorkoutCurrentResponse,
  WorkoutExecutionSessionSummary,
  WorkoutPlanInstanceSummary,
  WorkoutPreviewExercise,
  WorkoutPreviewResponse,
  WorkoutSizePreference,
} from "@/types/todayWorkout";

const workoutToneMap: Record<
  string,
  "positive" | "caution" | "warning" | "neutral"
> = {
  preview: "caution",
  selected: "caution",
  started: "positive",
  in_progress: "positive",
  completed: "positive",
  not_available: "neutral",
};

const sizeOptions: Array<{
  label: string;
  value: WorkoutSizePreference;
}> = [
  { label: "Quick", value: "quick" },
  { label: "Standard", value: "standard" },
  { label: "Extended", value: "full" },
];

interface WorkoutPreviewExperienceProps {
  userId: number;
  requestedDate: string | undefined;
}

type WorkoutViewMode = "preview" | "persisted";

function detailLabel(label: string, value: string | number | null): string | null {
  if (value === null || value === "") {
    return null;
  }

  return `${label}: ${value}`;
}

function formatRange(min: number, max: number): string {
  return min === max ? String(min) : `${min}-${max}`;
}

function exerciseMeta(exercise: WorkoutPreviewExercise): string[] {
  return [
    detailLabel("Sets", exercise.sets),
    detailLabel("Reps", formatRange(exercise.reps_min, exercise.reps_max)),
    detailLabel("RIR", formatRange(exercise.rir_min, exercise.rir_max)),
  ].filter((value): value is string => Boolean(value));
}

function buildPreviewSummary(preview: WorkoutPreviewResponse): string {
  const plan = preview.approved_workout_plan;
  return `${plan.exercises.length} exercises focused on ${plan.session_focus.toLowerCase()}.`;
}

function isPreviewPayload(
  payload: WorkoutPreviewResponse | null,
): payload is WorkoutPreviewResponse {
  if (payload === null) {
    return false;
  }

  return (
    typeof payload === "object" &&
    payload.approved_workout_plan !== null &&
    typeof payload.approved_workout_plan === "object" &&
    typeof payload.approved_workout_plan.title === "string" &&
    Array.isArray(payload.approved_workout_plan.exercises)
  );
}

function hasPersistedWorkoutState(
  payload: WorkoutCurrentResponse | null,
): payload is WorkoutCurrentResponse & {
  current_execution_state: NonNullable<WorkoutCurrentResponse["current_execution_state"]>;
} {
  if (payload?.current_execution_state === null) {
    return false;
  }

  return (
    payload?.workout_daily_state.state === "selected_today" ||
    payload?.workout_daily_state.state === "active_today"
  );
}

export function WorkoutPreviewExperience({
  userId,
  requestedDate,
}: WorkoutPreviewExperienceProps) {
  const [workoutSizePreference, setWorkoutSizePreference] =
    useState<WorkoutSizePreference>("standard");
  const [previewVariationIndex, setPreviewVariationIndex] = useState(0);
  const [preview, setPreview] = useState<WorkoutPreviewResponse | null>(null);
  const [persistedPlan, setPersistedPlan] =
    useState<ApprovedWorkoutPlanPreview | null>(null);
  const [viewMode, setViewMode] = useState<WorkoutViewMode>("preview");
  const [selectedPlan, setSelectedPlan] =
    useState<WorkoutPlanInstanceSummary | null>(null);
  const [executionSession, setExecutionSession] =
    useState<WorkoutExecutionSessionSummary | null>(null);
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isLoadingPreview, setIsLoadingPreview] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function loadPreview() {
      setIsLoadingPreview(true);
      setErrorMessage(null);
      setActionMessage(null);
      try {
        const currentResult = await fetchWorkoutCurrent({
          userId,
          date: requestedDate,
        });

        if (cancelled) {
          return;
        }

        if (hasPersistedWorkoutState(currentResult.data)) {
          setPreview(null);
          setViewMode("persisted");
          setPersistedPlan(
            currentResult.data.current_execution_state.approved_workout_plan,
          );
          setSelectedPlan(
            currentResult.data.current_execution_state.workout_plan_instance,
          );
          setExecutionSession(
            currentResult.data.current_execution_state.execution_session,
          );
          return;
        }

        const result = await fetchWorkoutPreview({
          userId,
          workoutSizePreference,
          previewVariationIndex,
        });

        if (cancelled) {
          return;
        }

        if (result.error) {
          setPreview(null);
          setViewMode("preview");
          setPersistedPlan(null);
          setSelectedPlan(null);
          setExecutionSession(null);
          setErrorMessage(
            result.error.message ??
              currentResult.error?.message ??
              "Workout preview is not available right now.",
          );
          return;
        }

        if (!isPreviewPayload(result.data)) {
          setPreview(null);
          setViewMode("preview");
          setPersistedPlan(null);
          setSelectedPlan(null);
          setExecutionSession(null);
          setErrorMessage(
            "The backend returned a workout preview, but it was missing the fields needed to render.",
          );
          return;
        }

        setViewMode("preview");
        setPersistedPlan(null);
        setSelectedPlan(null);
        setExecutionSession(null);
        setPreview(result.data);
      } finally {
        if (!cancelled) {
          setIsLoadingPreview(false);
        }
      }
    }

    void loadPreview();

    return () => {
      cancelled = true;
    };
  }, [previewVariationIndex, requestedDate, userId, workoutSizePreference]);

  const approvedPlan = persistedPlan ?? preview?.approved_workout_plan ?? null;
  const isPersistedState = viewMode === "persisted";
  const statusLabel =
    executionSession?.status ??
    selectedPlan?.status ??
    (approvedPlan ? "preview" : "not_available");
  const statusTone = workoutToneMap[statusLabel] ?? "neutral";
  const previewStateItems =
    approvedPlan === null && errorMessage
      ? [errorMessage]
      : approvedPlan
        ? []
        : ["Workout preview is not available right now."];

  function handleSizeChange(nextValue: WorkoutSizePreference) {
    setWorkoutSizePreference(nextValue);
    setPreviewVariationIndex(0);
    setViewMode("preview");
    setPersistedPlan(null);
    setSelectedPlan(null);
    setExecutionSession(null);
    setActionMessage(null);
    setErrorMessage(null);
  }

  function handleTryDifferentVersion() {
    setPreviewVariationIndex((current) => current + 1);
    setViewMode("preview");
    setPersistedPlan(null);
    setSelectedPlan(null);
    setExecutionSession(null);
    setActionMessage(null);
    setErrorMessage(null);
  }

  async function handleSelectWorkout() {
    if (approvedPlan === null) {
      return;
    }

    setIsSubmitting(true);
    try {
      setErrorMessage(null);
      const result = await selectWorkoutPreview(userId, approvedPlan);

      if (result.error) {
        setActionMessage(null);
        setErrorMessage(result.error.message);
        return;
      }

      setViewMode("persisted");
      setPersistedPlan(result.data?.approved_workout_plan ?? approvedPlan);
      setSelectedPlan(result.data?.workout_plan_instance ?? null);
      setExecutionSession(result.data?.execution_session ?? null);
      setActionMessage(
        `Selected workout plan ${result.data?.workout_plan_instance.id}.`,
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleStartWorkout() {
    if (selectedPlan === null) {
      return;
    }

    setIsSubmitting(true);
    try {
      setErrorMessage(null);
      const result = await startWorkoutPlan(selectedPlan.id);

      if (result.error) {
        setActionMessage(null);
        setErrorMessage(result.error.message);
        return;
      }

      setViewMode("persisted");
      setPersistedPlan(result.data?.approved_workout_plan ?? persistedPlan);
      setSelectedPlan(result.data?.workout_plan_instance ?? null);
      setExecutionSession(result.data?.execution_session ?? null);
      setActionMessage(`Started workout plan ${selectedPlan.id}.`);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="grid gap-4 lg:grid-cols-[minmax(0,1.45fr)_minmax(320px,0.95fr)] lg:gap-6 xl:grid-cols-[minmax(0,1.55fr)_minmax(360px,1fr)]">
      <TodayCard
        title={approvedPlan?.title ?? "Workout Preview"}
        eyebrow="Workout Plan"
        accent="highlight"
        className="lg:col-start-1 lg:row-start-1"
      >
        <div className="space-y-5">
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div className="space-y-2">
              <p className="text-lg font-semibold text-slate-950">
                {preview
                  ? buildPreviewSummary(preview)
                  : approvedPlan
                    ? `${approvedPlan.exercises.length} exercises ready for today.`
                    : "Load a workout preview."}
              </p>
              <p className="text-sm leading-6 text-slate-700">
                {approvedPlan?.session_focus ??
                  "Preview a backend-generated workout and commit to the one you want to do."}
              </p>
            </div>
            <StatusPill
              label={statusLabel.replaceAll("_", " ")}
              tone={statusTone}
            />
          </div>

          {!isPersistedState ? (
            <div className="flex flex-wrap gap-2">
              {sizeOptions.map((option) => {
                const isActive = option.value === workoutSizePreference;
                return (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => handleSizeChange(option.value)}
                    className={`rounded-full px-4 py-2 text-sm font-semibold transition ${
                      isActive
                        ? "bg-emerald-900 text-emerald-50"
                        : "bg-white text-slate-700 ring-1 ring-slate-200 hover:bg-emerald-50"
                    }`}
                  >
                    {option.label}
                  </button>
                );
              })}
            </div>
          ) : null}

          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
            <div className="rounded-2xl bg-slate-50 px-4 py-3">
              <p className="text-xs uppercase tracking-[0.16em] text-slate-500">
                Requested Date
              </p>
              <p className="mt-2 font-semibold text-slate-900">
                {requestedDate ?? "Today"}
              </p>
            </div>
            <div className="rounded-2xl bg-slate-50 px-4 py-3">
              <p className="text-xs uppercase tracking-[0.16em] text-slate-500">
                Duration
              </p>
              <p className="mt-2 font-semibold text-slate-900">
                {approvedPlan ? `${approvedPlan.duration_minutes} min` : "Not available"}
              </p>
            </div>
            <div className="rounded-2xl bg-slate-50 px-4 py-3">
              <p className="text-xs uppercase tracking-[0.16em] text-slate-500">
                Variation
              </p>
              <p className="mt-2 font-semibold text-slate-900">
                {isPersistedState ? "Selected" : previewVariationIndex + 1}
              </p>
            </div>
          </div>

          <div className="flex flex-wrap gap-3">
            {!isPersistedState ? (
              <button
                type="button"
                onClick={handleTryDifferentVersion}
                disabled={isLoadingPreview || isSubmitting}
                className="rounded-2xl bg-white px-4 py-3 text-sm font-semibold text-slate-900 ring-1 ring-slate-200 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
              >
                Try different version
              </button>
            ) : null}
            {!isPersistedState ? (
              <button
                type="button"
                onClick={() => void handleSelectWorkout()}
                disabled={approvedPlan === null || isLoadingPreview || isSubmitting}
                className="rounded-2xl bg-emerald-900 px-4 py-3 text-sm font-semibold text-emerald-50 transition hover:bg-emerald-800 disabled:cursor-not-allowed disabled:opacity-60"
              >
                Select this workout
              </button>
            ) : null}
            {selectedPlan ? (
              <button
                type="button"
                onClick={() => void handleStartWorkout()}
                disabled={
                  isLoadingPreview ||
                  isSubmitting ||
                  executionSession?.status === "started" ||
                  executionSession?.status === "in_progress"
                }
                className="rounded-2xl bg-slate-950 px-4 py-3 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
              >
                Start workout
              </button>
            ) : null}
          </div>

          {isLoadingPreview ? (
            <div className="rounded-2xl bg-slate-100 px-4 py-3 text-sm font-medium text-slate-700">
              Loading workout preview...
            </div>
          ) : null}
          {actionMessage ? (
            <div className="rounded-2xl bg-emerald-50 px-4 py-3 text-sm font-medium text-emerald-900">
              {actionMessage}
            </div>
          ) : null}
          {errorMessage ? (
            <div className="rounded-2xl bg-rose-50 px-4 py-3 text-sm font-medium text-rose-900">
              {errorMessage}
            </div>
          ) : null}
        </div>
      </TodayCard>

      <TodayCard
        title="Preview Details"
        className="lg:col-start-2 lg:row-start-1"
      >
        <div className="space-y-4">
          <div className="rounded-2xl bg-slate-50 px-4 py-3">
            <p className="text-xs uppercase tracking-[0.16em] text-slate-500">
              Scenario
            </p>
            <p className="mt-2 text-sm font-semibold text-slate-900">
              {(preview?.scenario ?? approvedPlan?.scenario)
                ?.replaceAll("_", " ") ?? "Not available"}
            </p>
          </div>
          <div className="rounded-2xl bg-slate-50 px-4 py-3">
            <p className="text-xs uppercase tracking-[0.16em] text-slate-500">
              Confidence
            </p>
            <p className="mt-2 text-sm font-semibold text-slate-900">
              {preview?.confidence ?? approvedPlan?.confidence ?? "Not available"}
            </p>
          </div>
          <div className="rounded-2xl bg-slate-50 px-4 py-3">
            <p className="text-xs uppercase tracking-[0.16em] text-slate-500">
              Size Reason
            </p>
            <p className="mt-2 text-sm leading-6 text-slate-700">
              {preview?.workout_exercise_count.user_safe_reason ??
                preview?.workout_exercise_count.reason ??
                "Preview a workout size to see the backend rationale."}
            </p>
          </div>
          <div className="rounded-2xl bg-slate-50 px-4 py-3">
            <p className="text-xs uppercase tracking-[0.16em] text-slate-500">
              Selected Plan
            </p>
            <p className="mt-2 text-sm font-semibold text-slate-900">
              {selectedPlan ? `Plan ${selectedPlan.id}` : "No workout selected yet"}
            </p>
          </div>
        </div>
      </TodayCard>

      <TodayCard
        title="Exercises"
        className="lg:col-start-1 lg:row-start-2"
      >
        {approvedPlan?.exercises.length ? (
          <div className="space-y-3">
            {approvedPlan.exercises.map((exercise, index) => (
              <article
                key={`${exercise.name}-${index + 1}`}
                className="rounded-[24px] border border-slate-200 bg-slate-50/80 p-4"
              >
                <div className="space-y-2">
                  <p className="text-[0.72rem] font-semibold uppercase tracking-[0.16em] text-slate-500">
                    Exercise {index + 1}
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
                    {exercise.equipment_required.map((item) => (
                      <span
                        key={`${exercise.name}-${item}`}
                        className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-900"
                      >
                        {item}
                      </span>
                    ))}
                  </div>
                </div>
                <p className="mt-4 text-sm leading-6 text-slate-700">
                  {exercise.notes}
                </p>
              </article>
            ))}
          </div>
        ) : (
          <p className="text-sm leading-6 text-slate-700">
            No exercise details are available for this preview yet.
          </p>
        )}
      </TodayCard>

      <TodayCard
        title="Session Notes"
        className="lg:col-start-2 lg:row-start-2"
      >
        <div className="space-y-4">
          <div className="rounded-2xl bg-slate-50 px-4 py-3">
            <p className="text-xs uppercase tracking-[0.16em] text-slate-500">
              Warmup
            </p>
            <p className="mt-2 text-sm leading-6 text-slate-700">
              {approvedPlan?.warmup ?? "Not available"}
            </p>
          </div>
          <div className="rounded-2xl bg-slate-50 px-4 py-3">
            <p className="text-xs uppercase tracking-[0.16em] text-slate-500">
              Cooldown
            </p>
            <p className="mt-2 text-sm leading-6 text-slate-700">
              {approvedPlan?.cooldown ?? "Not available"}
            </p>
          </div>
          <div className="rounded-2xl bg-slate-50 px-4 py-3">
            <p className="text-xs uppercase tracking-[0.16em] text-slate-500">
              Progression Guidance
            </p>
            <p className="mt-2 text-sm leading-6 text-slate-700">
              {approvedPlan?.progression_guidance ?? "Not available"}
            </p>
          </div>
          <div className="rounded-2xl bg-slate-50 px-4 py-3">
            <p className="text-xs uppercase tracking-[0.16em] text-slate-500">
              Rationale
            </p>
            <p className="mt-2 text-sm leading-6 text-slate-700">
              {approvedPlan?.rationale ?? "Not available"}
            </p>
          </div>
        </div>
      </TodayCard>

      <DataQualityNote
        title="Preview State"
        items={previewStateItems}
        className="lg:col-start-2 lg:row-start-3"
      />
    </div>
  );
}
