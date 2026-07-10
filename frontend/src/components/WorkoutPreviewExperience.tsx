"use client";

import { useCallback, useEffect, useState } from "react";

import { StatusPill } from "@/components/StatusPill";
import { TodayCard } from "@/components/TodayCard";
import {
  completeWorkout,
  deleteWorkoutActualSet,
  fetchWorkoutCurrent,
  fetchWorkoutPlannedVsActual,
  fetchWorkoutPreview,
  fetchWorkoutProgressionHistory,
  logWorkoutActualSet,
  selectWorkoutPreview,
  startWorkoutPlan,
  updateWorkoutActualSet,
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

function actualSetFormStateFromSet(
  actualSet: WorkoutActualSetSummary,
): ActualSetFormState {
  return {
    actualReps:
      actualSet.actual_reps === null ? "" : String(actualSet.actual_reps),
    actualWeight:
      actualSet.actual_weight === null ? "" : String(actualSet.actual_weight),
    actualRir: actualSet.actual_rir === null ? "" : String(actualSet.actual_rir),
    notes: actualSet.notes ?? "",
  };
}

function actualSetFormStateForDefaults(
  actualSet: WorkoutActualSetSummary,
): ActualSetFormState {
  return {
    ...actualSetFormStateFromSet(actualSet),
    notes: "",
  };
}

function plannedActualSetFormState(
  exercise: PlannedWorkoutExerciseSummary,
): ActualSetFormState {
  return {
    actualReps: String(exercise.reps_min),
    actualWeight: "0",
    actualRir: String(exercise.rir_max),
    notes: "",
  };
}

function plannedExerciseIdForActualSet(
  actualSet: WorkoutActualSetSummary,
): number | null {
  return (
    actualSet.substitution_for_planned_exercise_id ??
    actualSet.planned_workout_exercise_id ??
    null
  );
}

function latestActualSetForExerciseDefaults(
  actualSets: WorkoutActualSetSummary[],
  plannedExerciseId: number,
): WorkoutActualSetSummary | null {
  const loggedActualSets = loggedSetsForExercise(
    actualSets,
    plannedExerciseId,
  ).filter((actualSet) => actualSet.completed && !actualSet.skipped);

  if (!loggedActualSets.length) {
    return null;
  }

  const latestActualSet = [...loggedActualSets].sort(
    (first, second) =>
      (second.set_number || 0) - (first.set_number || 0) ||
      second.id - first.id,
  )[0];

  return latestActualSet ?? null;
}

function nextActualSetFormState(
  exercise: PlannedWorkoutExerciseSummary,
  actualSets: WorkoutActualSetSummary[],
): ActualSetFormState {
  const latestActualSet = latestActualSetForExerciseDefaults(
    actualSets,
    exercise.id,
  );

  return latestActualSet
    ? actualSetFormStateForDefaults(latestActualSet)
    : plannedActualSetFormState(exercise);
}

function formatActualSetLine(actualSet: WorkoutActualSetSummary): string {
  if (actualSet.skipped) {
    return `Set ${actualSet.set_number}: skipped`;
  }

  const parts = [`Set ${actualSet.set_number}`];
  if (actualSet.actual_reps !== null) {
    parts.push(`${actualSet.actual_reps} reps`);
  }
  if (actualSet.actual_weight !== null) {
    parts.push(`${actualSet.actual_weight} lb`);
  }
  if (actualSet.actual_rir !== null) {
    parts.push(`RIR ${actualSet.actual_rir}`);
  }

  return parts.join(" · ");
}

function loggedSetCountLabel(
  actualSets: WorkoutActualSetSummary[],
  plannedSets: number,
): string {
  const completedCount = completedSetCount(actualSets);

  return `${completedCount} / ${plannedSets} logged`;
}

function completedSetCount(actualSets: WorkoutActualSetSummary[]): number {
  return actualSets.filter((actualSet) => actualSet.completed && !actualSet.skipped)
    .length;
}

function remainingSetLabel(completedCount: number, plannedSets: number): string {
  const remaining = Math.max(plannedSets - completedCount, 0);

  if (remaining === 0) {
    return "All planned sets logged";
  }

  return `${remaining} set${remaining === 1 ? "" : "s"} remaining`;
}

function missingSetCount(summary: WorkoutPlannedVsActualSummary): number {
  return Math.max(summary.planned_set_count - summary.completed_set_count, 0);
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
  const [noteInputExpandedByExerciseId, setNoteInputExpandedByExerciseId] =
    useState<Record<number, boolean>>({});
  const [editingActualSetId, setEditingActualSetId] = useState<number | null>(
    null,
  );
  const [editFormStateByActualSetId, setEditFormStateByActualSetId] = useState<
    Record<number, ActualSetFormState>
  >({});
  const [isCompletionReviewOpen, setIsCompletionReviewOpen] = useState(false);
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
      setIsCompletionReviewOpen(false);

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
          setNoteInputExpandedByExerciseId({});
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
          setNoteInputExpandedByExerciseId({});
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
        setNoteInputExpandedByExerciseId({});
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
    setIsCompletionReviewOpen(false);
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
    setIsCompletionReviewOpen(false);
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

  function toggleExerciseNoteInput(plannedExerciseId: number) {
    setNoteInputExpandedByExerciseId((current) => ({
      ...current,
      [plannedExerciseId]: !current[plannedExerciseId],
    }));
  }

  function updateActualSetEditFormState(
    actualSetId: number,
    field: keyof ActualSetFormState,
    value: string,
  ) {
    setEditFormStateByActualSetId((current) => ({
      ...current,
      [actualSetId]: {
        actualReps: current[actualSetId]?.actualReps ?? "",
        actualWeight: current[actualSetId]?.actualWeight ?? "",
        actualRir: current[actualSetId]?.actualRir ?? "",
        notes: current[actualSetId]?.notes ?? "",
        [field]: value,
      },
    }));
  }

  function handleEditSet(actualSet: WorkoutActualSetSummary) {
    setEditingActualSetId(actualSet.id);
    setEditFormStateByActualSetId((current) => ({
      ...current,
      [actualSet.id]: actualSetFormStateFromSet(actualSet),
    }));
    setActionMessage(null);
    setErrorMessage(null);
  }

  function handleCancelEditSet(actualSetId: number) {
    setEditingActualSetId(null);
    setEditFormStateByActualSetId((current) => {
      const next = { ...current };
      delete next[actualSetId];
      return next;
    });
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
      setNoteInputExpandedByExerciseId({});
      setEditingActualSetId(null);
      setEditFormStateByActualSetId({});
      setIsCompletionReviewOpen(false);
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
      setEditingActualSetId(null);
      setEditFormStateByActualSetId({});
      setIsCompletionReviewOpen(false);
      setActionMessage(`Started workout plan ${selectedPlan.id}.`);
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleLogSet(exercise: PlannedWorkoutExerciseSummary) {
    if (selectedPlan === null) {
      return;
    }

    const exerciseActualSets = loggedSetsForExercise(actualSets, exercise.id);
    if (completedSetCount(exerciseActualSets) >= exercise.sets) {
      return;
    }

    const activeSubstitution = activeSubstitutionByExerciseId.get(exercise.id);
    const formState =
      formStateByExerciseId[exercise.id] ??
      nextActualSetFormState(exercise, actualSets);
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
        set_number: Math.min(
          nextSetNumberForExercise(actualSets, exercise.id),
          exercise.sets,
        ),
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
      const nextActualSets = result.data?.actual_sets ?? actualSets;
      setActualSets(nextActualSets);
      setViewMode("persisted");
      setActionMessage(
        `Logged ${result.data?.actual_set.exercise_name ?? exercise.name} set ${result.data?.actual_set.set_number ?? nextSetNumberForExercise(actualSets, exercise.id)}.`,
      );
      setFormStateByExerciseId((current) => ({
        ...current,
        [exercise.id]: nextActualSetFormState(exercise, nextActualSets),
      }));
      setNoteInputExpandedByExerciseId((current) => ({
        ...current,
        [exercise.id]: false,
      }));
      setIsCompletionReviewOpen(false);

      if (latestPlan && latestExecution) {
        await loadPlannedVsActualSummary(latestPlan.id, latestExecution.status);
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleUpdateActualSet(actualSet: WorkoutActualSetSummary) {
    if (selectedPlan === null) {
      return;
    }

    const formState =
      editFormStateByActualSetId[actualSet.id] ??
      actualSetFormStateFromSet(actualSet);

    setIsSubmitting(true);
    try {
      setErrorMessage(null);
      const result = await updateWorkoutActualSet(selectedPlan.id, actualSet.id, {
        actual_reps:
          formState.actualReps === "" ? undefined : Number(formState.actualReps),
        actual_weight:
          formState.actualWeight === ""
            ? undefined
            : Number(formState.actualWeight),
        actual_rir:
          formState.actualRir === "" ? undefined : Number(formState.actualRir),
        notes: formState.notes.trim() || undefined,
      });

      if (result.error) {
        setActionMessage(null);
        setErrorMessage(result.error.message);
        return;
      }

      const updatedActualSet = result.data?.actual_set;
      const nextActualSets = updatedActualSet
        ? actualSets.map((item) =>
            item.id === updatedActualSet.id ? updatedActualSet : item,
          )
        : actualSets;
      if (updatedActualSet) {
        setActualSets(nextActualSets);
      }
      const plannedExerciseId = plannedExerciseIdForActualSet(
        updatedActualSet ?? actualSet,
      );
      const plannedExercise =
        plannedExerciseId === null
          ? null
          : plannedExercises.find((exercise) => exercise.id === plannedExerciseId) ??
            null;
      if (plannedExercise) {
        setFormStateByExerciseId((current) => ({
          ...current,
          [plannedExercise.id]: nextActualSetFormState(
            plannedExercise,
            nextActualSets,
          ),
        }));
      }
      setSelectedPlan(result.data?.workout_plan_instance ?? selectedPlan);
      setExecutionSession(result.data?.execution_session ?? executionSession);
      setPlannedVsActualSummary(
        result.data?.planned_vs_actual_summary ?? plannedVsActualSummary,
      );
      handleCancelEditSet(actualSet.id);
      setIsCompletionReviewOpen(false);
      setActionMessage(`Updated ${actualSet.exercise_name} set ${actualSet.set_number}.`);
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleDeleteActualSet(actualSet: WorkoutActualSetSummary) {
    if (selectedPlan === null) {
      return;
    }

    setIsSubmitting(true);
    try {
      setErrorMessage(null);
      const result = await deleteWorkoutActualSet(selectedPlan.id, actualSet.id);

      if (result.error) {
        setActionMessage(null);
        setErrorMessage(result.error.message);
        return;
      }

      const nextActualSets = result.data?.actual_sets ?? [];
      const plannedExerciseId = plannedExerciseIdForActualSet(actualSet);
      const plannedExercise =
        plannedExerciseId === null
          ? null
          : plannedExercises.find((exercise) => exercise.id === plannedExerciseId) ??
            null;

      setSelectedPlan(result.data?.workout_plan_instance ?? selectedPlan);
      setExecutionSession(result.data?.execution_session ?? executionSession);
      setActualSets(nextActualSets);
      if (plannedExercise) {
        setFormStateByExerciseId((current) => ({
          ...current,
          [plannedExercise.id]: nextActualSetFormState(
            plannedExercise,
            nextActualSets,
          ),
        }));
      }
      setPlannedVsActualSummary(
        result.data?.planned_vs_actual_summary ?? plannedVsActualSummary,
      );
      handleCancelEditSet(actualSet.id);
      setIsCompletionReviewOpen(false);
      setActionMessage(`Deleted ${actualSet.exercise_name} set ${actualSet.set_number}.`);
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleOpenCompletionReview() {
    setActionMessage(null);
    setErrorMessage(null);
    setIsCompletionReviewOpen(true);

    if (selectedPlan !== null && plannedVsActualSummary === null) {
      await loadPlannedVsActualSummary(selectedPlan.id, summaryStatus);
    }
  }

  function handleCancelCompletionReview() {
    setIsCompletionReviewOpen(false);
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
      setIsCompletionReviewOpen(false);
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
  const completionReviewMissingSets = plannedVsActualSummary
    ? missingSetCount(plannedVsActualSummary)
    : 0;
  const hasCompletionReviewMissingSets =
    plannedVsActualSummary !== null && completionReviewMissingSets > 0;
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
            <div className="space-y-3">
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
                {canCompleteWorkout && !isCompletionReviewOpen ? (
                  <button
                    type="button"
                    onClick={() => void handleOpenCompletionReview()}
                    disabled={isSubmitting}
                    className="rounded-2xl bg-amber-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-amber-500 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    Complete workout
                  </button>
                ) : null}
              </div>

              {canCompleteWorkout && isCompletionReviewOpen ? (
                <div className="rounded-xl bg-white px-3 py-3 ring-1 ring-amber-200">
                  <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                    <div className="space-y-2">
                      <p className="text-sm font-semibold text-slate-950">
                        Complete workout?
                      </p>
                      {plannedVsActualSummary ? (
                        <div className="flex flex-wrap gap-2 text-xs font-semibold">
                          <span className="rounded-full bg-slate-50 px-3 py-1 text-slate-700 ring-1 ring-slate-200">
                            Logged: {plannedVsActualSummary.completed_set_count} /{" "}
                            {plannedVsActualSummary.planned_set_count} sets
                          </span>
                          <span className="rounded-full bg-slate-50 px-3 py-1 text-slate-700 ring-1 ring-slate-200">
                            Exercises:{" "}
                            {plannedVsActualSummary.completed_exercise_count} /{" "}
                            {plannedVsActualSummary.planned_exercise_count}
                          </span>
                          <span className="rounded-full bg-slate-50 px-3 py-1 text-slate-700 ring-1 ring-slate-200">
                            Avg RIR:{" "}
                            {compactMetric(plannedVsActualSummary.average_actual_rir)}
                          </span>
                        </div>
                      ) : (
                        <p className="text-sm font-medium text-slate-600">
                          Workout summary is still loading.
                        </p>
                      )}
                      {plannedVsActualSummary ? (
                        <p
                          className={`text-sm font-medium ${
                            hasCompletionReviewMissingSets
                              ? "text-amber-800"
                              : "text-emerald-800"
                          }`}
                        >
                          {hasCompletionReviewMissingSets
                            ? `${completionReviewMissingSets} planned set${
                                completionReviewMissingSets === 1 ? " is" : "s are"
                              } not logged yet. You can complete anyway, or go back and finish logging.`
                            : "All planned sets are logged."}
                        </p>
                      ) : null}
                    </div>
                    <div className="flex shrink-0 flex-wrap gap-2">
                      <button
                        type="button"
                        onClick={handleCancelCompletionReview}
                        disabled={isSubmitting}
                        className="rounded-xl bg-slate-100 px-3 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-200 disabled:cursor-not-allowed disabled:opacity-60"
                      >
                        Cancel
                      </button>
                      <button
                        type="button"
                        onClick={() => void handleCompleteWorkout()}
                        disabled={isSubmitting || plannedVsActualSummary === null}
                        className="rounded-xl bg-amber-600 px-3 py-2 text-sm font-semibold text-white transition hover:bg-amber-500 disabled:cursor-not-allowed disabled:opacity-60"
                      >
                        {hasCompletionReviewMissingSets
                          ? "Complete anyway"
                          : "Complete workout"}
                      </button>
                    </div>
                  </div>
                </div>
              ) : null}
            </div>
          ) : null}

          {plannedExercises.length ? (
            <div className="grid gap-3 lg:grid-cols-2">
              {plannedExercises.map((exercise) => {
                const activeSubstitution = activeSubstitutionByExerciseId.get(
                  exercise.id,
                );
                const formState =
                  formStateByExerciseId[exercise.id] ??
                  nextActualSetFormState(exercise, actualSets);
                const displayExerciseName =
                  activeSubstitution?.replacement_exercise_name ?? exercise.name;
                const exerciseActualSets = loggedSetsForExercise(
                  actualSets,
                  exercise.id,
                );
                const completedLoggedSetCount =
                  completedSetCount(exerciseActualSets);
                const allPlannedSetsLogged =
                  completedLoggedSetCount >= exercise.sets;
                const nextSetNumber = Math.min(
                  nextSetNumberForExercise(actualSets, exercise.id),
                  exercise.sets,
                );
                const exerciseNoteInputExpanded =
                  Boolean(noteInputExpandedByExerciseId[exercise.id]) ||
                  Boolean(formState.notes);
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
                      {exerciseActualSets.length ? (
                        <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs font-semibold text-emerald-800">
                          <span>{loggedSetCountLabel(exerciseActualSets, exercise.sets)}</span>
                          <span className="text-slate-500">
                            {remainingSetLabel(completedLoggedSetCount, exercise.sets)}
                          </span>
                        </div>
                      ) : null}
                      <PreviousPerformanceLine history={history} />
                    </div>

                    {exerciseActualSets.length ? (
                      <div className="mt-4 space-y-2">
                        {exerciseActualSets.map((actualSet) => {
                          const isEditing = editingActualSetId === actualSet.id;
                          const editFormState =
                            editFormStateByActualSetId[actualSet.id] ??
                            actualSetFormStateFromSet(actualSet);

                          return (
                            <div
                              key={actualSet.id}
                              className="rounded-lg bg-white/90 px-3 py-2 ring-1 ring-slate-200"
                            >
                              {isEditing ? (
                                <div className="space-y-2">
                                  <div className="grid gap-2 sm:grid-cols-3">
                                    <label className="space-y-1 text-xs font-medium text-slate-700">
                                      <span>Reps</span>
                                      <input
                                        type="number"
                                        min="0"
                                        value={editFormState.actualReps}
                                        onChange={(event) =>
                                          updateActualSetEditFormState(
                                            actualSet.id,
                                            "actualReps",
                                            event.target.value,
                                          )
                                        }
                                        className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-950 outline-none focus:border-emerald-400"
                                      />
                                    </label>
                                    <label className="space-y-1 text-xs font-medium text-slate-700">
                                      <span>Weight</span>
                                      <input
                                        type="number"
                                        min="0"
                                        step="5"
                                        value={editFormState.actualWeight}
                                        onChange={(event) =>
                                          updateActualSetEditFormState(
                                            actualSet.id,
                                            "actualWeight",
                                            event.target.value,
                                          )
                                        }
                                        className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-950 outline-none focus:border-emerald-400"
                                      />
                                    </label>
                                    <label className="space-y-1 text-xs font-medium text-slate-700">
                                      <span>RIR</span>
                                      <input
                                        type="number"
                                        min="0"
                                        max="10"
                                        value={editFormState.actualRir}
                                        onChange={(event) =>
                                          updateActualSetEditFormState(
                                            actualSet.id,
                                            "actualRir",
                                            event.target.value,
                                          )
                                        }
                                        className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-950 outline-none focus:border-emerald-400"
                                      />
                                    </label>
                                  </div>
                                  <label className="block space-y-1 text-xs font-medium text-slate-700">
                                    <span>Notes</span>
                                    <textarea
                                      rows={2}
                                      value={editFormState.notes}
                                      onChange={(event) =>
                                        updateActualSetEditFormState(
                                          actualSet.id,
                                          "notes",
                                          event.target.value,
                                        )
                                      }
                                      className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-950 outline-none focus:border-emerald-400"
                                    />
                                  </label>
                                  <div className="flex flex-wrap gap-3">
                                    <button
                                      type="button"
                                      onClick={() => void handleUpdateActualSet(actualSet)}
                                      disabled={isSubmitting}
                                      className="text-xs font-semibold text-emerald-800 transition hover:text-emerald-950 disabled:cursor-not-allowed disabled:opacity-60"
                                    >
                                      Save
                                    </button>
                                    <button
                                      type="button"
                                      onClick={() => handleCancelEditSet(actualSet.id)}
                                      disabled={isSubmitting}
                                      className="text-xs font-semibold text-slate-500 transition hover:text-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
                                    >
                                      Cancel
                                    </button>
                                  </div>
                                </div>
                              ) : (
                                <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-1">
                                  <div className="min-w-0">
                                    <p className="flex flex-wrap items-center gap-x-3 gap-y-1 text-sm font-semibold text-slate-900">
                                      {formatActualSetLine(actualSet)}
                                    </p>
                                    {actualSet.notes ? (
                                      <p className="mt-0.5 text-xs text-slate-600">
                                        {actualSet.notes}
                                      </p>
                                    ) : null}
                                  </div>
                                  {canLogWorkout ? (
                                    <div className="flex shrink-0 flex-wrap gap-2 text-xs font-semibold">
                                      <button
                                        type="button"
                                        onClick={() => handleEditSet(actualSet)}
                                        disabled={isSubmitting}
                                        className="text-slate-600 transition hover:text-slate-950 disabled:cursor-not-allowed disabled:opacity-60"
                                      >
                                        Edit
                                      </button>
                                      <span className="text-slate-300">·</span>
                                      <button
                                        type="button"
                                        onClick={() => void handleDeleteActualSet(actualSet)}
                                        disabled={isSubmitting}
                                        className="text-slate-500 transition hover:text-rose-700 disabled:cursor-not-allowed disabled:opacity-60"
                                      >
                                        Delete
                                      </button>
                                    </div>
                                  ) : null}
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    ) : canLogWorkout ? (
                      <div className="mt-4 rounded-[18px] bg-white px-3 py-3 text-sm font-medium text-slate-600 ring-1 ring-slate-200">
                        No sets logged for this exercise yet.
                      </div>
                    ) : null}

                    {canLogWorkout && allPlannedSetsLogged ? (
                      <div className="mt-3 rounded-lg bg-emerald-50 px-3 py-2 text-sm font-semibold text-emerald-900 ring-1 ring-emerald-100">
                        All planned sets logged
                      </div>
                    ) : canLogWorkout ? (
                      <div className="mt-4 rounded-xl bg-white px-3 py-3 ring-1 ring-slate-200">
                        <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
                          <div>
                            <p className="text-sm font-semibold text-slate-950">
                              Log next set
                            </p>
                            <p className="text-xs font-medium text-slate-500">
                              Set {nextSetNumber} of {exercise.sets} ·{" "}
                              {remainingSetLabel(
                                completedLoggedSetCount,
                                exercise.sets,
                              )}
                            </p>
                          </div>
                          <button
                            type="button"
                            onClick={() => void handleLogSet(exercise)}
                            disabled={isSubmitting}
                            className="rounded-xl bg-emerald-900 px-3 py-2 text-sm font-semibold text-emerald-50 transition hover:bg-emerald-800 disabled:cursor-not-allowed disabled:opacity-60"
                          >
                            Save set
                          </button>
                        </div>

                        <div className="mt-3 grid gap-2 sm:grid-cols-3">
                          <label className="space-y-1 text-sm text-slate-700">
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
                              className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-950 outline-none ring-0 focus:border-emerald-400"
                            />
                          </label>
                          <label className="space-y-1 text-sm text-slate-700">
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
                              className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-950 outline-none ring-0 focus:border-emerald-400"
                            />
                          </label>
                          <label className="space-y-1 text-sm text-slate-700">
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
                              className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-950 outline-none ring-0 focus:border-emerald-400"
                            />
                          </label>
                        </div>

                        {exerciseNoteInputExpanded ? (
                          <div className="mt-3 space-y-1 text-sm text-slate-700">
                            <div className="flex items-center justify-between">
                              <span className="font-medium">Notes</span>
                              <button
                                type="button"
                                onClick={() => toggleExerciseNoteInput(exercise.id)}
                                className="text-xs font-semibold text-slate-500 transition hover:text-slate-900"
                              >
                                Hide
                              </button>
                            </div>
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
                              className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-950 outline-none ring-0 focus:border-emerald-400"
                              placeholder="Optional: form note, pain note, or context."
                            />
                          </div>
                        ) : (
                          <button
                            type="button"
                            onClick={() => toggleExerciseNoteInput(exercise.id)}
                            className="mt-3 text-xs font-semibold text-slate-500 transition hover:text-slate-900"
                          >
                            Add note
                          </button>
                        )}
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
