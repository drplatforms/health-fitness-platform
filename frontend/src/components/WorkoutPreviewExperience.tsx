"use client";

import { useCallback, useEffect, useState } from "react";

import { StatusPill } from "@/components/StatusPill";
import { TodayCard } from "@/components/TodayCard";
import {
  completeWorkout,
  fetchWorkoutCurrent,
  fetchWorkoutPlannedVsActual,
  fetchWorkoutPreview,
  fetchWorkoutProgressionHistory,
  logWorkoutActualSet,
  selectWorkoutPreview,
  startWorkoutPlan,
} from "@/lib/todayWorkoutApi";
import {
  ApprovedWorkoutPlanPreview,
  PlannedWorkoutExerciseSummary,
  WorkoutActiveSubstitutionSummary,
  WorkoutActualSetSummary,
  WorkoutDailyStateSummary,
  WorkoutExecutionSessionSummary,
  WorkoutExerciseHistorySummary,
  WorkoutPlanInstanceSummary,
  WorkoutPlannedVsActualSummary,
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

interface ActualSetFormState {
  actualReps: string;
  actualWeight: string;
  actualRir: string;
  notes: string;
}

type WorkoutViewMode = "preview" | "persisted" | "completed";

const HISTORY_LOOKBACK_DAYS = 90;

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

function formatExerciseCountLabel(count: number): string {
  return `${count} exercise${count === 1 ? "" : "s"}`;
}

function formatPercentage(value: number): string {
  return Number.isInteger(value) ? `${value}%` : `${value.toFixed(1)}%`;
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

function isSummaryEligibleStatus(status: string | null | undefined): boolean {
  return status === "in_progress" || status === "completed";
}

function loggedSetsForExercise(
  actualSets: WorkoutActualSetSummary[],
  plannedExerciseId: number,
): WorkoutActualSetSummary[] {
  return actualSets.filter(
    (actualSet) =>
      actualSet.planned_workout_exercise_id === plannedExerciseId ||
      actualSet.substitution_for_planned_exercise_id === plannedExerciseId,
  );
}

function nextSetNumberForExercise(
  actualSets: WorkoutActualSetSummary[],
  plannedExerciseId: number,
): number {
  const relatedSets = loggedSetsForExercise(actualSets, plannedExerciseId);

  if (!relatedSets.length) {
    return 1;
  }

  return (
    Math.max(...relatedSets.map((actualSet) => actualSet.set_number || 0)) + 1
  );
}

function compactMetric(
  value: number | string | null | undefined,
  suffix = "",
): string {
  if (value === null || value === undefined || value === "") {
    return "Not available";
  }

  return `${value}${suffix}`;
}

function normalizeExerciseHistoryKey(name: string): string {
  return name.trim().toLowerCase().replace(/\s+/g, " ");
}

function uniqueExerciseNames(names: string[]): string[] {
  const seen = new Set<string>();
  const unique: string[] = [];

  names.forEach((name) => {
    const trimmed = name.trim();
    const key = normalizeExerciseHistoryKey(trimmed);
    if (!trimmed || seen.has(key)) {
      return;
    }
    seen.add(key);
    unique.push(trimmed);
  });

  return unique;
}

function mapProgressionHistories(
  histories: WorkoutExerciseHistorySummary[],
): Record<string, WorkoutExerciseHistorySummary> {
  return histories.reduce<Record<string, WorkoutExerciseHistorySummary>>(
    (mapped, history) => {
      mapped[normalizeExerciseHistoryKey(history.exercise_name)] = history;
      return mapped;
    },
    {},
  );
}

function PreviousPerformanceLine({
  history,
}: {
  history: WorkoutExerciseHistorySummary | undefined;
}) {
  if (!history) {
    return null;
  }

  if (!history.has_history) {
    return (
      <div className="rounded-lg bg-white px-3 py-2 text-xs font-medium text-slate-600 ring-1 ring-slate-200">
        {history.message}
      </div>
    );
  }

  return (
    <div className="space-y-1 rounded-lg bg-white px-3 py-2 text-xs text-slate-700 ring-1 ring-slate-200">
      {history.last_session_summary ? (
        <p>
          <span className="font-semibold text-slate-900">Last time:</span>{" "}
          {history.last_session_summary}
        </p>
      ) : null}
      {history.recent_best_set ? (
        <p>
          <span className="font-semibold text-slate-900">Recent best:</span>{" "}
          {history.recent_best_set.summary}
        </p>
      ) : null}
      <p>
        <span className="font-semibold text-slate-900">History:</span>{" "}
        {history.completed_session_count} completed{" "}
        {history.completed_session_count === 1 ? "session" : "sessions"} in last{" "}
        {HISTORY_LOOKBACK_DAYS} days
      </p>
      {history.logging_quality !== "complete" ? (
        <p className="font-medium text-amber-800">{history.message}</p>
      ) : null}
    </div>
  );
}

function statusSummaryLine(
  approvedPlan: ApprovedWorkoutPlanPreview | null,
  preview: WorkoutPreviewResponse | null,
  viewMode: WorkoutViewMode,
  selectedPlanStatus: string | null | undefined,
  plannedVsActualSummary: WorkoutPlannedVsActualSummary | null,
): string {
  if (viewMode === "completed") {
    if (plannedVsActualSummary) {
      return `${plannedVsActualSummary.completed_set_count} / ${plannedVsActualSummary.planned_set_count} sets complete`;
    }

    return "Completed";
  }

  if (selectedPlanStatus === "in_progress") {
    if (plannedVsActualSummary) {
      return `${formatPercentage(plannedVsActualSummary.completion_percentage)} sets complete.`;
    }

    return "In progress";
  }

  if (selectedPlanStatus === "selected") {
    return "Selected and ready";
  }

  if (preview && approvedPlan) {
    return `${formatExerciseCountLabel(approvedPlan.exercises.length)} ready`;
  }

  if (approvedPlan) {
    return `${formatExerciseCountLabel(approvedPlan.exercises.length)} ready`;
  }

  return "Workout unavailable";
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
  const [, setDailyState] = useState<WorkoutDailyStateSummary | null>(null);
  const [selectedPlan, setSelectedPlan] =
    useState<WorkoutPlanInstanceSummary | null>(null);
  const [executionSession, setExecutionSession] =
    useState<WorkoutExecutionSessionSummary | null>(null);
  const [plannedExercises, setPlannedExercises] = useState<
    PlannedWorkoutExerciseSummary[]
  >([]);
  const [actualSets, setActualSets] = useState<WorkoutActualSetSummary[]>([]);
  const [activeSubstitutions, setActiveSubstitutions] = useState<
    WorkoutActiveSubstitutionSummary[]
  >([]);
  const [plannedVsActualSummary, setPlannedVsActualSummary] =
    useState<WorkoutPlannedVsActualSummary | null>(null);
  const [progressionHistoryByExerciseName, setProgressionHistoryByExerciseName] =
    useState<Record<string, WorkoutExerciseHistorySummary>>({});
  const [formStateByExerciseId, setFormStateByExerciseId] = useState<
    Record<number, ActualSetFormState>
  >({});
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isLoadingPreview, setIsLoadingPreview] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const approvedPlan = persistedPlan ?? preview?.approved_workout_plan ?? null;
  const isPersistedState = viewMode === "persisted";
  const isCompletedState = viewMode === "completed";
  const summaryStatus = executionSession?.status ?? selectedPlan?.status ?? null;
  const statusLabel =
    isCompletedState
      ? "completed"
      : summaryStatus ?? (approvedPlan ? "preview" : "not_available");
  const statusTone = workoutToneMap[statusLabel] ?? "neutral";
  const topMetrics = [
    approvedPlan ? formatExerciseCountLabel(approvedPlan.exercises.length) : null,
    approvedPlan ? `${approvedPlan.duration_minutes} min` : null,
    !isPersistedState && !isCompletedState ? `Version ${previewVariationIndex + 1}` : null,
  ].filter((value): value is string => Boolean(value));

  const activeSubstitutionByExerciseId = new Map(
    activeSubstitutions.map((substitution) => [
      substitution.planned_workout_exercise_id,
      substitution,
    ]),
  );

  async function loadPlannedVsActualSummary(
    planInstanceId: number,
    expectedStatus: string | null | undefined,
  ) {
    if (!isSummaryEligibleStatus(expectedStatus)) {
      setPlannedVsActualSummary(null);
      return;
    }

    const result = await fetchWorkoutPlannedVsActual(planInstanceId);

    if (result.error) {
      setPlannedVsActualSummary(null);
      return;
    }

    setPlannedVsActualSummary(result.data?.planned_vs_actual_summary ?? null);
    if (result.data?.planned_exercises.length) {
      setPlannedExercises(result.data.planned_exercises);
    }
    if (result.data?.actual_sets.length) {
      setActualSets(result.data.actual_sets);
    }
  }

  const loadProgressionHistoryForNames = useCallback(async function (
    names: string[],
  ): Promise<Record<string, WorkoutExerciseHistorySummary>> {
    const exerciseNames = uniqueExerciseNames(names);
    if (!exerciseNames.length) {
      return {};
    }

    const result = await fetchWorkoutProgressionHistory(userId, exerciseNames);
    if (result.error || !result.data) {
      return {};
    }

    return mapProgressionHistories(result.data.exercise_histories);
  }, [userId]);

  useEffect(() => {
    let cancelled = false;

    async function loadWorkoutState() {
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

        const currentData = currentResult.data;
        setDailyState(currentData?.workout_daily_state ?? null);

        if (currentData?.workout_daily_state.state === "completed_today") {
          const currentExecution = currentData.current_execution_state;
          setPreview(null);
          setViewMode("completed");
          setPersistedPlan(currentExecution?.approved_workout_plan ?? null);
          setSelectedPlan(currentExecution?.workout_plan_instance ?? null);
          setExecutionSession(currentExecution?.execution_session ?? null);
          setPlannedExercises(currentExecution?.planned_exercises ?? []);
          setActualSets(currentExecution?.actual_sets ?? []);
          setActiveSubstitutions(currentExecution?.active_substitutions ?? []);
          setFormStateByExerciseId({});
          setProgressionHistoryByExerciseName(
            await loadProgressionHistoryForNames(
              currentExecution?.planned_exercises.map((exercise) => exercise.name) ??
                [],
            ),
          );
          if (currentExecution) {
            await loadPlannedVsActualSummary(
              currentExecution.workout_plan_instance.id,
              currentExecution.execution_session.status,
            );
          } else {
            setPlannedVsActualSummary(null);
          }
          return;
        }

        const currentExecution = currentResult.data?.current_execution_state;

        if (
          currentExecution &&
          (currentData?.workout_daily_state.state === "selected_today" ||
            currentData?.workout_daily_state.state === "active_today")
        ) {
          setPreview(null);
          setViewMode("persisted");
          setPersistedPlan(currentExecution.approved_workout_plan);
          setSelectedPlan(currentExecution.workout_plan_instance);
          setExecutionSession(currentExecution.execution_session);
          setPlannedExercises(currentExecution.planned_exercises);
          setActualSets(currentExecution.actual_sets);
          setActiveSubstitutions(currentExecution.active_substitutions);
          setFormStateByExerciseId({});
          setProgressionHistoryByExerciseName(
            await loadProgressionHistoryForNames(
              currentExecution.planned_exercises.map((exercise) => exercise.name),
            ),
          );
          await loadPlannedVsActualSummary(
            currentExecution.workout_plan_instance.id,
            currentExecution.execution_session.status,
          );
          return;
        }

        const previewResult = await fetchWorkoutPreview({
          userId,
          workoutSizePreference,
          previewVariationIndex,
        });

        if (cancelled) {
          return;
        }

        if (previewResult.error) {
          setPreview(null);
          setViewMode("preview");
          setDailyState(currentData?.workout_daily_state ?? null);
          setPersistedPlan(null);
          setSelectedPlan(null);
          setExecutionSession(null);
          setPlannedExercises([]);
          setActualSets([]);
          setActiveSubstitutions([]);
          setPlannedVsActualSummary(null);
          setProgressionHistoryByExerciseName({});
          setErrorMessage(
            previewResult.error.message ??
              currentResult.error?.message ??
              "Workout preview is not available right now.",
          );
          return;
        }

        if (!isPreviewPayload(previewResult.data)) {
          setPreview(null);
          setViewMode("preview");
          setDailyState(currentData?.workout_daily_state ?? null);
          setPersistedPlan(null);
          setSelectedPlan(null);
          setExecutionSession(null);
          setPlannedExercises([]);
          setActualSets([]);
          setActiveSubstitutions([]);
          setPlannedVsActualSummary(null);
          setProgressionHistoryByExerciseName({});
          setErrorMessage(
            "The backend returned a workout preview, but it was missing the fields needed to render.",
          );
          return;
        }

        setViewMode("preview");
        setDailyState(currentData?.workout_daily_state ?? null);
        setPersistedPlan(null);
        setSelectedPlan(null);
        setExecutionSession(null);
        setPlannedExercises([]);
        setActualSets([]);
        setActiveSubstitutions([]);
        setPlannedVsActualSummary(null);
        setPreview(previewResult.data);
        setProgressionHistoryByExerciseName(
          await loadProgressionHistoryForNames(
            previewResult.data.approved_workout_plan.exercises.map(
              (exercise) => exercise.name,
            ),
          ),
        );
        setFormStateByExerciseId({});
      } finally {
        if (!cancelled) {
          setIsLoadingPreview(false);
        }
      }
    }

    void loadWorkoutState();

    return () => {
      cancelled = true;
    };
  }, [
    loadProgressionHistoryForNames,
    previewVariationIndex,
    requestedDate,
    userId,
    workoutSizePreference,
  ]);

  function handleSizeChange(nextValue: WorkoutSizePreference) {
    setWorkoutSizePreference(nextValue);
    setPreviewVariationIndex(0);
    setViewMode("preview");
    setDailyState(null);
    setPersistedPlan(null);
    setSelectedPlan(null);
    setExecutionSession(null);
    setPlannedExercises([]);
    setActualSets([]);
    setActiveSubstitutions([]);
    setPlannedVsActualSummary(null);
    setProgressionHistoryByExerciseName({});
    setActionMessage(null);
    setErrorMessage(null);
  }

  function handleTryDifferentVersion() {
    setPreviewVariationIndex((current) => current + 1);
    setViewMode("preview");
    setDailyState(null);
    setPersistedPlan(null);
    setSelectedPlan(null);
    setExecutionSession(null);
    setPlannedExercises([]);
    setActualSets([]);
    setActiveSubstitutions([]);
    setPlannedVsActualSummary(null);
    setProgressionHistoryByExerciseName({});
    setActionMessage(null);
    setErrorMessage(null);
  }

  function updateExerciseFormState(
    plannedExerciseId: number,
    field: keyof ActualSetFormState,
    value: string,
  ) {
    setFormStateByExerciseId((current) => ({
      ...current,
      [plannedExerciseId]: {
        actualReps: current[plannedExerciseId]?.actualReps ?? "",
        actualWeight: current[plannedExerciseId]?.actualWeight ?? "",
        actualRir: current[plannedExerciseId]?.actualRir ?? "",
        notes: current[plannedExerciseId]?.notes ?? "",
        [field]: value,
      },
    }));
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

      setPreview(null);
      setViewMode("persisted");
      setDailyState((current) =>
        current
          ? { ...current, state: "selected_today", user_safe_message: null }
          : current,
      );
      setPersistedPlan(result.data?.approved_workout_plan ?? approvedPlan);
      setSelectedPlan(result.data?.workout_plan_instance ?? null);
      setExecutionSession(result.data?.execution_session ?? null);
      setPlannedExercises(result.data?.planned_exercises ?? []);
      setActualSets([]);
      setActiveSubstitutions([]);
      setPlannedVsActualSummary(null);
      setProgressionHistoryByExerciseName(
        await loadProgressionHistoryForNames(
          result.data?.planned_exercises.map((exercise) => exercise.name) ?? [],
        ),
      );
      setFormStateByExerciseId({});
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
      setDailyState((current) =>
        current
          ? { ...current, state: "active_today", user_safe_message: null }
          : current,
      );
      setPersistedPlan(result.data?.approved_workout_plan ?? persistedPlan);
      setSelectedPlan(result.data?.workout_plan_instance ?? null);
      setExecutionSession(result.data?.execution_session ?? null);
      setPlannedExercises(result.data?.planned_exercises ?? plannedExercises);
      setActualSets([]);
      setActiveSubstitutions([]);
      setPlannedVsActualSummary(null);
      setProgressionHistoryByExerciseName(
        await loadProgressionHistoryForNames(
          (result.data?.planned_exercises ?? plannedExercises).map(
            (exercise) => exercise.name,
          ),
        ),
      );
      setActionMessage(`Started workout plan ${selectedPlan.id}.`);
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleLogSet(exercise: PlannedWorkoutExerciseSummary) {
    if (selectedPlan === null) {
      return;
    }

    const activeSubstitution = activeSubstitutionByExerciseId.get(exercise.id);
    const formState = formStateByExerciseId[exercise.id];
    const actualReps = formState?.actualReps || String(exercise.reps_min);
    const actualWeight = formState?.actualWeight || "0";
    const actualRir = formState?.actualRir || String(exercise.rir_max);
    const notes = formState?.notes.trim() || undefined;

    setIsSubmitting(true);
    try {
      setErrorMessage(null);
      const result = await logWorkoutActualSet(selectedPlan.id, {
        planned_workout_exercise_id: activeSubstitution ? undefined : exercise.id,
        substitution_for_planned_exercise_id: activeSubstitution
          ? exercise.id
          : undefined,
        exercise_name: activeSubstitution?.replacement_exercise_name,
        set_number: nextSetNumberForExercise(actualSets, exercise.id),
        actual_reps: Number(actualReps),
        actual_weight: Number(actualWeight),
        actual_rir: Number(actualRir),
        completed: true,
        skipped: false,
        notes,
      });

      if (result.error) {
        setActionMessage(null);
        setErrorMessage(result.error.message);
        return;
      }

      const latestPlan = result.data?.workout_plan_instance ?? selectedPlan;
      const latestExecution = result.data?.execution_session ?? executionSession;
      setSelectedPlan(latestPlan);
      setExecutionSession(latestExecution);
      setActualSets(result.data?.actual_sets ?? actualSets);
      setViewMode("persisted");
      setActionMessage(
        `Logged ${result.data?.actual_set.exercise_name ?? exercise.name} set ${result.data?.actual_set.set_number ?? nextSetNumberForExercise(actualSets, exercise.id)}.`,
      );
      setFormStateByExerciseId((current) => ({
        ...current,
        [exercise.id]: {
          actualReps: String(exercise.reps_min),
          actualWeight: current[exercise.id]?.actualWeight ?? "0",
          actualRir: String(exercise.rir_max),
          notes: "",
        },
      }));

      if (latestPlan && latestExecution) {
        await loadPlannedVsActualSummary(latestPlan.id, latestExecution.status);
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleCompleteWorkout() {
    if (selectedPlan === null) {
      return;
    }

    setIsSubmitting(true);
    try {
      setErrorMessage(null);
      const result = await completeWorkout(selectedPlan.id);

      if (result.error) {
        setActionMessage(null);
        setErrorMessage(result.error.message);
        return;
      }

      setSelectedPlan(result.data?.workout_plan_instance ?? selectedPlan);
      setExecutionSession(result.data?.execution_session ?? executionSession);
      setPlannedVsActualSummary(result.data?.planned_vs_actual_summary ?? null);
      setViewMode("completed");
      setDailyState((current) =>
        current
          ? { ...current, state: "completed_today", user_safe_message: null }
          : current,
      );
      setActionMessage("Workout completed successfully.");
      await loadPlannedVsActualSummary(selectedPlan.id, "completed");
    } finally {
      setIsSubmitting(false);
    }
  }

  const canStartWorkout =
    selectedPlan !== null &&
    executionSession !== null &&
    selectedPlan.status === "selected" &&
    executionSession.status === "selected";
  const canLogWorkout =
    selectedPlan !== null &&
    executionSession !== null &&
    (selectedPlan.status === "started" ||
      selectedPlan.status === "in_progress" ||
      executionSession.status === "started" ||
      executionSession.status === "in_progress");
  const canCompleteWorkout =
    selectedPlan !== null &&
    executionSession !== null &&
    (selectedPlan.status === "in_progress" ||
      executionSession.status === "in_progress");
  return (
    <div className="grid gap-4 lg:grid-cols-[minmax(0,1.45fr)_minmax(320px,0.95fr)] lg:gap-6 xl:grid-cols-[minmax(0,1.55fr)_minmax(360px,1fr)]">
      <TodayCard
        title="Session Status"
        accent="highlight"
        className="lg:col-span-2 lg:row-start-1"
      >
        <div className="space-y-3">
          <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
            <div className="space-y-2">
              <p className="text-2xl font-semibold uppercase tracking-[0.12em] text-slate-950">
                {statusLabel.replaceAll("_", " ")}
              </p>
              <p className="text-sm font-semibold text-slate-800">
                {statusSummaryLine(
                  approvedPlan,
                  preview,
                  viewMode,
                  summaryStatus,
                  plannedVsActualSummary,
                )}
              </p>
            </div>
            <StatusPill
              label={statusLabel.replaceAll("_", " ")}
              tone={statusTone}
            />
          </div>

          <div className="flex flex-wrap gap-2">
            {topMetrics.map((item) => (
              <span
                key={item}
                className="rounded-full bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 ring-1 ring-slate-200"
              >
                {item}
              </span>
            ))}
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

      {plannedVsActualSummary ? (
        <TodayCard
          title="Execution Summary"
          accent="subtle"
          className="lg:col-start-2 lg:row-start-2"
        >
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="rounded-2xl bg-white px-4 py-3 ring-1 ring-slate-200">
              <p className="text-xs uppercase tracking-[0.16em] text-slate-500">
                Completion
              </p>
              <p className="mt-2 text-xl font-semibold text-slate-900">
                {compactMetric(plannedVsActualSummary.completion_percentage, "%")}
              </p>
            </div>
            <div className="rounded-2xl bg-white px-4 py-3 ring-1 ring-slate-200">
              <p className="text-xs uppercase tracking-[0.16em] text-slate-500">
                Completed Sets
              </p>
              <p className="mt-2 text-xl font-semibold text-slate-900">
                {plannedVsActualSummary.completed_set_count}/
                {plannedVsActualSummary.planned_set_count}
              </p>
            </div>
            <div className="rounded-2xl bg-white px-4 py-3 ring-1 ring-slate-200">
              <p className="text-xs uppercase tracking-[0.16em] text-slate-500">
                Average Actual RIR
              </p>
              <p className="mt-2 text-xl font-semibold text-slate-900">
                {compactMetric(plannedVsActualSummary.average_actual_rir)}
              </p>
            </div>
            <div className="rounded-2xl bg-white px-4 py-3 ring-1 ring-slate-200">
              <p className="text-xs uppercase tracking-[0.16em] text-slate-500">
                Rep Range Match
              </p>
              <p className="mt-2 text-xl font-semibold text-slate-900">
                {plannedVsActualSummary.sets_inside_planned_reps}
              </p>
            </div>
          </div>
        </TodayCard>
      ) : null}

      <TodayCard
        title={canLogWorkout ? "Exercises And Logging" : "Exercises"}
        className="lg:col-start-1 lg:row-start-2"
      >
        <div className="space-y-4">
          {!isPersistedState && !isCompletedState ? (
            <div className="rounded-2xl bg-slate-50 px-4 py-4">
              <div className="space-y-3">
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
                <div className="flex flex-wrap gap-3">
                  <button
                    type="button"
                    onClick={handleTryDifferentVersion}
                    disabled={isLoadingPreview || isSubmitting}
                    className="rounded-2xl bg-white px-4 py-3 text-sm font-semibold text-slate-900 ring-1 ring-slate-200 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    Try different version
                  </button>
                  <button
                    type="button"
                    onClick={() => void handleSelectWorkout()}
                    disabled={approvedPlan === null || isLoadingPreview || isSubmitting}
                    className="rounded-2xl bg-emerald-900 px-4 py-3 text-sm font-semibold text-emerald-50 transition hover:bg-emerald-800 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    Select this workout
                  </button>
                </div>
              </div>
            </div>
          ) : null}

          {canStartWorkout || canCompleteWorkout ? (
            <div className="flex flex-wrap gap-3">
              {canStartWorkout ? (
                <button
                  type="button"
                  onClick={() => void handleStartWorkout()}
                  disabled={isLoadingPreview || isSubmitting}
                  className="rounded-2xl bg-slate-950 px-4 py-3 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  Start workout
                </button>
              ) : null}
              {canCompleteWorkout ? (
                <button
                  type="button"
                  onClick={() => void handleCompleteWorkout()}
                  disabled={isSubmitting}
                  className="rounded-2xl bg-amber-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-amber-500 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  Complete workout
                </button>
              ) : null}
            </div>
          ) : null}

          {plannedExercises.length ? (
            <div className="grid gap-3 lg:grid-cols-2">
              {plannedExercises.map((exercise) => {
                const activeSubstitution = activeSubstitutionByExerciseId.get(
                  exercise.id,
                );
                const formState = formStateByExerciseId[exercise.id] ?? {
                  actualReps: String(exercise.reps_min),
                  actualWeight: "0",
                  actualRir: String(exercise.rir_max),
                  notes: "",
                };
                const displayExerciseName =
                  activeSubstitution?.replacement_exercise_name ?? exercise.name;
                const history =
                  progressionHistoryByExerciseName[
                    normalizeExerciseHistoryKey(displayExerciseName)
                  ] ??
                  progressionHistoryByExerciseName[
                    normalizeExerciseHistoryKey(exercise.name)
                  ];

                return (
                  <article
                    key={exercise.id}
                    className="rounded-[24px] border border-slate-200 bg-slate-50/80 p-4"
                  >
                    <div className="space-y-2">
                      <h2 className="text-xl font-semibold text-slate-950">
                        {displayExerciseName}
                      </h2>
                      <div className="flex flex-wrap gap-2">
                        {exerciseMeta(exercise).map((item) => (
                          <span
                            key={`${exercise.id}-${item}`}
                            className="rounded-full bg-white px-3 py-1 text-xs font-medium text-slate-700"
                          >
                            {item}
                          </span>
                        ))}
                        {exercise.equipment_required.map((item) => (
                          <span
                            key={`${exercise.id}-${item}`}
                            className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-900"
                          >
                            {item}
                          </span>
                        ))}
                      </div>
                      <PreviousPerformanceLine history={history} />
                    </div>

                    {canLogWorkout ? (
                      <div className="mt-5 rounded-[20px] bg-white px-4 py-4 ring-1 ring-slate-200">
                        <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
                          <div>
                            <p className="text-sm font-semibold text-slate-950">
                              Log next set
                            </p>
                            <p className="text-xs uppercase tracking-[0.16em] text-slate-500">
                              Set{" "}
                              {nextSetNumberForExercise(actualSets, exercise.id)}
                            </p>
                          </div>
                          <button
                            type="button"
                            onClick={() => void handleLogSet(exercise)}
                            disabled={isSubmitting}
                            className="rounded-2xl bg-emerald-900 px-4 py-2 text-sm font-semibold text-emerald-50 transition hover:bg-emerald-800 disabled:cursor-not-allowed disabled:opacity-60"
                          >
                            Save set
                          </button>
                        </div>

                        <div className="mt-4 grid gap-3 sm:grid-cols-3">
                          <label className="space-y-2 text-sm text-slate-700">
                            <span className="font-medium">Reps</span>
                            <input
                              type="number"
                              min="0"
                              value={formState.actualReps}
                              onChange={(event) =>
                                updateExerciseFormState(
                                  exercise.id,
                                  "actualReps",
                                  event.target.value,
                                )
                              }
                              className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-950 outline-none ring-0 focus:border-emerald-400"
                            />
                          </label>
                          <label className="space-y-2 text-sm text-slate-700">
                            <span className="font-medium">Weight</span>
                            <input
                              type="number"
                              min="0"
                              step="5"
                              value={formState.actualWeight}
                              onChange={(event) =>
                                updateExerciseFormState(
                                  exercise.id,
                                  "actualWeight",
                                  event.target.value,
                                )
                              }
                              className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-950 outline-none ring-0 focus:border-emerald-400"
                            />
                          </label>
                          <label className="space-y-2 text-sm text-slate-700">
                            <span className="font-medium">RIR</span>
                            <input
                              type="number"
                              min="0"
                              max="10"
                              value={formState.actualRir}
                              onChange={(event) =>
                                updateExerciseFormState(
                                  exercise.id,
                                  "actualRir",
                                  event.target.value,
                                )
                              }
                              className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-950 outline-none ring-0 focus:border-emerald-400"
                            />
                          </label>
                        </div>

                        <label className="mt-3 block space-y-2 text-sm text-slate-700">
                          <span className="font-medium">Notes</span>
                          <textarea
                            rows={2}
                            value={formState.notes}
                            onChange={(event) =>
                              updateExerciseFormState(
                                exercise.id,
                                "notes",
                                event.target.value,
                              )
                            }
                            className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-950 outline-none ring-0 focus:border-emerald-400"
                            placeholder="Optional: form note, pain note, or context."
                          />
                        </label>
                      </div>
                    ) : null}
                  </article>
                );
              })}
            </div>
          ) : approvedPlan?.exercises.length ? (
            <div className="grid gap-3 lg:grid-cols-2">
              {approvedPlan.exercises.map((exercise, index) => {
                const history =
                  progressionHistoryByExerciseName[
                    normalizeExerciseHistoryKey(exercise.name)
                  ];

                return (
                  <article
                    key={`${exercise.name}-${index + 1}`}
                    className="rounded-[24px] border border-slate-200 bg-slate-50/80 p-4"
                  >
                    <div className="space-y-2">
                      <h2 className="text-xl font-semibold text-slate-950">
                        {exercise.name}
                      </h2>
                      <div className="flex flex-wrap gap-2">
                        {exerciseMeta(exercise).map((item) => (
                          <span
                            key={`${exercise.name}-${item}`}
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
                      <PreviousPerformanceLine history={history} />
                    </div>
                  </article>
                );
              })}
            </div>
          ) : (
            <p className="text-sm leading-6 text-slate-700">
              No exercise details are available for this workout yet.
            </p>
          )}
        </div>
      </TodayCard>

    </div>
  );
}
