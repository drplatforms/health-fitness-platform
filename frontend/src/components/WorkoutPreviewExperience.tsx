"use client";

import { useCallback, useEffect, useState } from "react";

import { ExerciseInstructionDisclosure } from "@/components/ExerciseInstructionDisclosure";
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

interface ExerciseActualsSummary {
  plannedExerciseId: number;
  exerciseName: string;
  plannedSets: number;
  loggedSets: number;
  setDots: Array<"logged" | "unlogged">;
  extraLoggedSets: number;
  completionStatus: string;
  averageRir: number | null;
  effortStatus: string;
  repRangeStatus: string;
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
  return actualSets
    .filter(
      (actualSet) => plannedExerciseIdForActualSet(actualSet) === plannedExerciseId,
    )
    .sort(
      (first, second) =>
        first.set_number - second.set_number || first.id - second.id,
    );
}

function nextSetNumberForExercise(
  actualSets: WorkoutActualSetSummary[],
  plannedExerciseId: number,
  plannedSets: number,
): number {
  const relatedSets = loggedSetsForExercise(actualSets, plannedExerciseId);
  const occupiedSetNumbers = new Set(
    relatedSets
      .map((actualSet) => actualSet.set_number)
      .filter((setNumber) => Number.isInteger(setNumber) && setNumber > 0),
  );

  for (let setNumber = 1; setNumber <= plannedSets; setNumber += 1) {
    if (!occupiedSetNumbers.has(setNumber)) {
      return setNumber;
    }
  }

  return Math.max(0, ...occupiedSetNumbers) + 1;
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

function average(values: number[]): number | null {
  if (!values.length) {
    return null;
  }

  return values.reduce((total, value) => total + value, 0) / values.length;
}

function formatAverageRir(value: number): string {
  return Number.isInteger(value) ? String(value) : value.toFixed(1);
}

function effortStatusForAverageRir(averageRir: number | null): string {
  if (averageRir === null) {
    return "Limited effort data";
  }
  if (averageRir <= 1.5) {
    return "Hard effort";
  }
  if (averageRir <= 3) {
    return "Moderate effort";
  }
  return "Easy effort";
}

function completionStatusForExercise(
  loggedSets: number,
  plannedSets: number,
): string {
  if (plannedSets <= 0) {
    return "Limited data";
  }
  if (loggedSets > plannedSets) {
    return "Logged extra";
  }
  if (loggedSets === 0) {
    return "Not started";
  }

  const remainingSets = plannedSets - loggedSets;
  if (remainingSets === 0) {
    return "Complete";
  }

  return `${remainingSets} set${remainingSets === 1 ? "" : "s"} remaining`;
}

function repRangeStatusForExercise(
  exercise: PlannedWorkoutExerciseSummary,
  loggedSets: WorkoutActualSetSummary[],
): string {
  const loggedReps = loggedSets
    .map((actualSet) => actualSet.actual_reps)
    .filter((reps): reps is number => reps !== null);

  if (!loggedReps.length) {
    return "No logged reps";
  }

  const belowCount = loggedReps.filter(
    (reps) => reps < exercise.reps_min,
  ).length;
  const aboveCount = loggedReps.filter(
    (reps) => reps > exercise.reps_max,
  ).length;
  const insideCount = loggedReps.length - belowCount - aboveCount;

  if (insideCount === loggedReps.length) {
    return "Reps on target";
  }
  if (belowCount === loggedReps.length) {
    return "Below range";
  }
  if (aboveCount === loggedReps.length) {
    return "Above range";
  }
  return "Mixed reps";
}

function buildExerciseActualsSummaries(
  plannedExercises: PlannedWorkoutExerciseSummary[],
  actualSets: WorkoutActualSetSummary[],
  activeSubstitutionByExerciseId: Map<
    number,
    WorkoutActiveSubstitutionSummary
  >,
): ExerciseActualsSummary[] {
  return plannedExercises.map((exercise) => {
    const loggedSets = loggedSetsForExercise(actualSets, exercise.id).filter(
      (actualSet) => actualSet.completed && !actualSet.skipped,
    );
    const averageRir = average(
      loggedSets
        .map((actualSet) => actualSet.actual_rir)
        .filter((rir): rir is number => rir !== null),
    );
    const plannedSets = Math.max(exercise.sets, 0);
    const loggedSetCount = loggedSets.length;

    return {
      plannedExerciseId: exercise.id,
      exerciseName:
        activeSubstitutionByExerciseId.get(exercise.id)
          ?.replacement_exercise_name ?? exercise.name,
      plannedSets,
      loggedSets: loggedSetCount,
      setDots: Array.from({ length: plannedSets }, (_, index) =>
        index < Math.min(loggedSetCount, plannedSets) ? "logged" : "unlogged",
      ),
      extraLoggedSets: Math.max(loggedSetCount - plannedSets, 0),
      completionStatus: completionStatusForExercise(
        loggedSetCount,
        plannedSets,
      ),
      averageRir,
      effortStatus: effortStatusForAverageRir(averageRir),
      repRangeStatus: repRangeStatusForExercise(exercise, loggedSets),
    };
  });
}

function ExerciseActualsSummaryPanel({
  summaries,
}: {
  summaries: ExerciseActualsSummary[];
}) {
  return (
    <div className="mt-4 border-t border-border pt-4">
      <h3 className="text-sm font-semibold text-text-strong">
        Exercise actuals
      </h3>
      <div className="mt-2 divide-y divide-border">
        {summaries.map((summary) => (
          <div
            key={summary.plannedExerciseId}
            className="grid gap-2 py-3 first:pt-1 last:pb-0 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center"
          >
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold text-text-primary">
                {summary.exerciseName}
              </p>
              <div className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-1 text-xs font-medium text-text-secondary">
                <span
                  className="flex items-center gap-1"
                  aria-label={`${summary.loggedSets} of ${summary.plannedSets} planned sets logged`}
                >
                  {summary.setDots.map((dotStatus, index) => (
                    <span
                      key={`${summary.plannedExerciseId}-${index + 1}`}
                      aria-hidden="true"
                      className={
                        dotStatus === "logged"
                          ? "text-completed-indicator"
                          : "text-incomplete-indicator"
                      }
                    >
                      {dotStatus === "logged" ? "●" : "○"}
                    </span>
                  ))}
                </span>
                <span>
                  {summary.loggedSets} / {summary.plannedSets} sets
                </span>
                {summary.extraLoggedSets ? (
                  <span>+{summary.extraLoggedSets} extra</span>
                ) : null}
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-1.5 sm:justify-end">
              <span className="rounded-full bg-positive-surface px-2 py-1 text-xs font-semibold text-positive-foreground-strong">
                {summary.completionStatus}
              </span>
              {summary.loggedSets > 0 ? (
                <span className="rounded-full bg-neutral-surface px-2 py-1 text-xs font-medium text-neutral-foreground">
                  Avg RIR{" "}
                  {summary.averageRir === null
                    ? "not available"
                    : formatAverageRir(summary.averageRir)}
                </span>
              ) : null}
              <span className="rounded-full bg-neutral-surface px-2 py-1 text-xs font-medium text-neutral-foreground">
                {summary.effortStatus}
              </span>
              <span className="rounded-full bg-neutral-surface px-2 py-1 text-xs font-medium text-neutral-foreground">
                {summary.repRangeStatus}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
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
      <div className="rounded-lg bg-surface px-3 py-2 text-xs font-medium text-text-secondary ring-1 ring-border">
        {history.message}
      </div>
    );
  }

  return (
    <div className="space-y-1 rounded-lg bg-surface px-3 py-2 text-xs text-text-body ring-1 ring-border">
      {history.last_session_summary ? (
        <p>
          <span className="font-semibold text-text-primary">Last time:</span>{" "}
          {history.last_session_summary}
        </p>
      ) : null}
      {history.recent_best_set ? (
        <p>
          <span className="font-semibold text-text-primary">Recent best:</span>{" "}
          {history.recent_best_set.summary}
        </p>
      ) : null}
      <p>
        <span className="font-semibold text-text-primary">History:</span>{" "}
        {history.completed_session_count} completed{" "}
        {history.completed_session_count === 1 ? "session" : "sessions"} in last{" "}
        {HISTORY_LOOKBACK_DAYS} days
      </p>
      {history.logging_quality !== "complete" ? (
        <p className="font-medium text-caution-foreground">{history.message}</p>
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
  const [expandedInstructionKey, setExpandedInstructionKey] = useState<
    string | null
  >(null);
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
  const exerciseActualsSummaries = buildExerciseActualsSummaries(
    plannedExercises,
    actualSets,
    activeSubstitutionByExerciseId,
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
    setExpandedInstructionKey(null);
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
    setExpandedInstructionKey(null);
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

    setExpandedInstructionKey(null);
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
        set_number: nextSetNumberForExercise(
          actualSets,
          exercise.id,
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
        `Logged ${result.data?.actual_set.exercise_name ?? exercise.name} set ${result.data?.actual_set.set_number ?? nextSetNumberForExercise(actualSets, exercise.id, exercise.sets)}.`,
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
              <p className="text-2xl font-semibold uppercase tracking-[0.12em] text-text-strong">
                {statusLabel.replaceAll("_", " ")}
              </p>
              <p className="text-sm font-semibold text-text-body">
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
                className="rounded-full bg-surface px-3 py-1.5 text-xs font-semibold text-text-body ring-1 ring-border"
              >
                {item}
              </span>
            ))}
          </div>

          {isLoadingPreview ? (
            <div className="rounded-2xl bg-neutral-surface px-4 py-3 text-sm font-medium text-neutral-foreground">
              Loading workout preview...
            </div>
          ) : null}
          {actionMessage ? (
            <div className="rounded-2xl bg-positive-surface px-4 py-3 text-sm font-medium text-positive-foreground-strong">
              {actionMessage}
            </div>
          ) : null}
          {errorMessage ? (
            <div className="rounded-2xl bg-danger-surface px-4 py-3 text-sm font-medium text-danger-foreground">
              {errorMessage}
            </div>
          ) : null}
        </div>
      </TodayCard>

      {plannedVsActualSummary ? (
        <TodayCard
          title="Execution Summary"
          accent="subtle"
          className="lg:col-span-2"
        >
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="rounded-2xl bg-surface px-4 py-3 ring-1 ring-border">
              <p className="text-xs uppercase tracking-[0.16em] text-text-muted">
                Completion
              </p>
              <p className="mt-2 text-xl font-semibold text-text-primary">
                {compactMetric(plannedVsActualSummary.completion_percentage, "%")}
              </p>
            </div>
            <div className="rounded-2xl bg-surface px-4 py-3 ring-1 ring-border">
              <p className="text-xs uppercase tracking-[0.16em] text-text-muted">
                Completed Sets
              </p>
              <p className="mt-2 text-xl font-semibold text-text-primary">
                {plannedVsActualSummary.completed_set_count}/
                {plannedVsActualSummary.planned_set_count}
              </p>
              {plannedVsActualSummary.extra_set_count > 0 ? (
                <p className="mt-1 text-xs font-medium text-text-muted">
                  {plannedVsActualSummary.extra_set_count} extra set
                  {plannedVsActualSummary.extra_set_count === 1 ? "" : "s"}
                </p>
              ) : null}
            </div>
            <div className="rounded-2xl bg-surface px-4 py-3 ring-1 ring-border">
              <p className="text-xs uppercase tracking-[0.16em] text-text-muted">
                Average Actual RIR
              </p>
              <p className="mt-2 text-xl font-semibold text-text-primary">
                {compactMetric(plannedVsActualSummary.average_actual_rir)}
              </p>
            </div>
            <div className="rounded-2xl bg-surface px-4 py-3 ring-1 ring-border">
              <p className="text-xs uppercase tracking-[0.16em] text-text-muted">
                Rep Range Match
              </p>
              <p className="mt-2 text-xl font-semibold text-text-primary">
                {plannedVsActualSummary.sets_inside_planned_reps}
              </p>
            </div>
          </div>
          <ExerciseActualsSummaryPanel summaries={exerciseActualsSummaries} />
        </TodayCard>
      ) : null}

      <TodayCard
        title={canLogWorkout ? "Exercises And Logging" : "Exercises"}
        className="lg:col-span-2"
      >
        <div className="space-y-4">
          {!isPersistedState && !isCompletedState ? (
            <div
              className={`rounded-2xl bg-surface-subtle px-4 py-4 ${
                expandedInstructionKey !== null ? "md:hidden" : ""
              }`}
            >
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
                            ? "bg-action-primary text-action-primary-foreground"
                            : "bg-surface text-text-body ring-1 ring-border hover:bg-surface-highlighted"
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
                    className="rounded-2xl bg-surface px-4 py-3 text-sm font-semibold text-text-primary ring-1 ring-border transition hover:bg-surface-subtle disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    Try different version
                  </button>
                  <button
                    type="button"
                    onClick={() => void handleSelectWorkout()}
                    disabled={approvedPlan === null || isLoadingPreview || isSubmitting}
                    className="rounded-2xl bg-action-primary px-4 py-3 text-sm font-semibold text-action-primary-foreground transition hover:bg-action-primary-hover disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    Select this workout
                  </button>
                </div>
              </div>
            </div>
          ) : null}

          {canStartWorkout || canCompleteWorkout ? (
            <div
              className={`space-y-3 ${
                expandedInstructionKey !== null ? "md:hidden" : ""
              }`}
            >
              <div className="flex flex-wrap gap-3">
                {canStartWorkout ? (
                  <button
                    type="button"
                    onClick={() => void handleStartWorkout()}
                    disabled={isLoadingPreview || isSubmitting}
                    className="rounded-2xl bg-control-selected-surface px-4 py-3 text-sm font-semibold text-text-inverse transition hover:bg-control-selected-surface-hover disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    Start workout
                  </button>
                ) : null}
                {canCompleteWorkout && !isCompletionReviewOpen ? (
                  <button
                    type="button"
                    onClick={() => void handleOpenCompletionReview()}
                    disabled={isSubmitting}
                    className="rounded-2xl bg-caution-action px-4 py-3 text-sm font-semibold text-text-inverse transition hover:bg-caution-action-hover disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    Complete workout
                  </button>
                ) : null}
              </div>

              {canCompleteWorkout && isCompletionReviewOpen ? (
                <div className="rounded-xl bg-surface px-3 py-3 ring-1 ring-border-warm">
                  <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                    <div className="space-y-2">
                      <p className="text-sm font-semibold text-text-strong">
                        Complete workout?
                      </p>
                      {plannedVsActualSummary ? (
                        <div className="flex flex-wrap gap-2 text-xs font-semibold">
                          <span className="rounded-full bg-surface-subtle px-3 py-1 text-text-body ring-1 ring-border">
                            Logged: {plannedVsActualSummary.completed_set_count} /{" "}
                            {plannedVsActualSummary.planned_set_count} sets
                          </span>
                          <span className="rounded-full bg-surface-subtle px-3 py-1 text-text-body ring-1 ring-border">
                            Exercises:{" "}
                            {plannedVsActualSummary.completed_exercise_count} /{" "}
                            {plannedVsActualSummary.planned_exercise_count}
                          </span>
                          <span className="rounded-full bg-surface-subtle px-3 py-1 text-text-body ring-1 ring-border">
                            Avg RIR:{" "}
                            {compactMetric(plannedVsActualSummary.average_actual_rir)}
                          </span>
                        </div>
                      ) : (
                        <p className="text-sm font-medium text-text-secondary">
                          Workout summary is still loading.
                        </p>
                      )}
                      {plannedVsActualSummary ? (
                        <p
                          className={`text-sm font-medium ${
                            hasCompletionReviewMissingSets
                              ? "text-caution-foreground"
                              : "text-positive-foreground"
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
                        className="rounded-xl bg-surface-muted px-3 py-2 text-sm font-semibold text-text-body transition hover:bg-surface-interactive-hover disabled:cursor-not-allowed disabled:opacity-60"
                      >
                        Cancel
                      </button>
                      <button
                        type="button"
                        onClick={() => void handleCompleteWorkout()}
                        disabled={isSubmitting || plannedVsActualSummary === null}
                        className="rounded-xl bg-caution-action px-3 py-2 text-sm font-semibold text-text-inverse transition hover:bg-caution-action-hover disabled:cursor-not-allowed disabled:opacity-60"
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
            <div className="grid grid-cols-[repeat(auto-fit,minmax(min(100%,20rem),1fr))] gap-3">
              {plannedExercises.map((exercise) => {
                const activeSubstitution = activeSubstitutionByExerciseId.get(
                  exercise.id,
                );
                const formState =
                  formStateByExerciseId[exercise.id] ??
                  nextActualSetFormState(exercise, actualSets);
                const displayExerciseName =
                  activeSubstitution?.replacement_exercise_name ?? exercise.name;
                const displayedCatalogExerciseId =
                  activeSubstitution?.replacement_catalog_exercise_id ??
                  exercise.catalog_exercise_id;
                const exerciseActualSets = loggedSetsForExercise(
                  actualSets,
                  exercise.id,
                );
                const completedLoggedSetCount =
                  completedSetCount(exerciseActualSets);
                const allPlannedSetsLogged =
                  completedLoggedSetCount >= exercise.sets;
                const nextSetNumber = nextSetNumberForExercise(
                  actualSets,
                  exercise.id,
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
                const instructionKey = `persisted-${exercise.id}-${
                  displayedCatalogExerciseId ?? "legacy"
                }`;
                const isInstructionExpanded =
                  expandedInstructionKey === instructionKey;

                return (
                  <article
                    key={exercise.id}
                    data-expanded={isInstructionExpanded}
                    className={`rounded-[24px] border border-border bg-surface-subtle/80 p-4 motion-safe:transition-[border-color,background-color,box-shadow] motion-safe:duration-300 ${
                      isInstructionExpanded
                        ? "md:col-span-full md:border-workout-card-active-border md:[background:var(--theme-workout-card-active-surface)] md:p-6 md:shadow-[0_24px_55px_-40px_rgba(15,118,110,0.65)]"
                        : expandedInstructionKey !== null
                          ? "md:hidden"
                          : ""
                    }`}
                  >
                    <div className="space-y-2">
                      <div className="flex flex-wrap items-start justify-between gap-x-4 gap-y-2">
                        <h2 className="min-w-0 text-xl font-semibold text-text-strong">
                          {displayExerciseName}
                        </h2>
                        <ExerciseInstructionDisclosure
                          key={displayedCatalogExerciseId ?? "legacy"}
                          catalogExerciseId={displayedCatalogExerciseId}
                          exerciseName={displayExerciseName}
                          isExpanded={isInstructionExpanded}
                          onExpandedChange={(nextIsExpanded) =>
                            setExpandedInstructionKey((current) =>
                              nextIsExpanded
                                ? instructionKey
                                : current === instructionKey
                                  ? null
                                  : current,
                            )
                          }
                        />
                      </div>
                      <div
                        className={`space-y-2 ${
                          isInstructionExpanded ? "md:hidden" : ""
                        }`}
                      >
                        <div className="flex flex-wrap gap-2">
                          {exerciseMeta(exercise).map((item) => (
                            <span
                              key={`${exercise.id}-${item}`}
                              className="rounded-full bg-surface px-3 py-1 text-xs font-medium text-text-body"
                            >
                              {item}
                            </span>
                          ))}
                          {exercise.equipment_required.map((item) => (
                            <span
                              key={`${exercise.id}-${item}`}
                              className="rounded-full bg-surface-highlighted px-3 py-1 text-xs font-medium text-positive-foreground-strong"
                            >
                              {item}
                            </span>
                          ))}
                        </div>
                        {exerciseActualSets.length ? (
                          <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs font-semibold text-positive-foreground">
                            <span>
                              {loggedSetCountLabel(
                                exerciseActualSets,
                                exercise.sets,
                              )}
                            </span>
                            <span className="text-text-muted">
                              {remainingSetLabel(
                                completedLoggedSetCount,
                                exercise.sets,
                              )}
                            </span>
                          </div>
                        ) : null}
                        <PreviousPerformanceLine history={history} />
                      </div>
                    </div>

                    <div
                      className={isInstructionExpanded ? "md:hidden" : ""}
                    >
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
                              className="rounded-lg bg-surface/90 px-3 py-2 ring-1 ring-border"
                            >
                              {isEditing ? (
                                <div className="space-y-2">
                                  <div className="grid gap-2 sm:grid-cols-3">
                                    <label className="space-y-1 text-xs font-medium text-text-body">
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
                                        className="w-full rounded-xl border border-border bg-surface-subtle px-3 py-2 text-sm text-text-strong outline-none focus:border-focus-subtle"
                                      />
                                    </label>
                                    <label className="space-y-1 text-xs font-medium text-text-body">
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
                                        className="w-full rounded-xl border border-border bg-surface-subtle px-3 py-2 text-sm text-text-strong outline-none focus:border-focus-subtle"
                                      />
                                    </label>
                                    <label className="space-y-1 text-xs font-medium text-text-body">
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
                                        className="w-full rounded-xl border border-border bg-surface-subtle px-3 py-2 text-sm text-text-strong outline-none focus:border-focus-subtle"
                                      />
                                    </label>
                                  </div>
                                  <label className="block space-y-1 text-xs font-medium text-text-body">
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
                                      className="w-full rounded-xl border border-border bg-surface-subtle px-3 py-2 text-sm text-text-strong outline-none focus:border-focus-subtle"
                                    />
                                  </label>
                                  <div className="flex flex-wrap gap-3">
                                    <button
                                      type="button"
                                      onClick={() => void handleUpdateActualSet(actualSet)}
                                      disabled={isSubmitting}
                                      className="text-xs font-semibold text-accent-text transition hover:text-accent-text-hover disabled:cursor-not-allowed disabled:opacity-60"
                                    >
                                      Save
                                    </button>
                                    <button
                                      type="button"
                                      onClick={() => handleCancelEditSet(actualSet.id)}
                                      disabled={isSubmitting}
                                      className="text-xs font-semibold text-text-muted transition hover:text-text-primary disabled:cursor-not-allowed disabled:opacity-60"
                                    >
                                      Cancel
                                    </button>
                                  </div>
                                </div>
                              ) : (
                                <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-1">
                                  <div className="min-w-0">
                                    <p className="flex flex-wrap items-center gap-x-3 gap-y-1 text-sm font-semibold text-text-primary">
                                      {formatActualSetLine(actualSet)}
                                    </p>
                                    {actualSet.notes ? (
                                      <p className="mt-0.5 text-xs text-text-secondary">
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
                                        className="text-text-secondary transition hover:text-text-strong disabled:cursor-not-allowed disabled:opacity-60"
                                      >
                                        Edit
                                      </button>
                                      <span className="text-incomplete-indicator">·</span>
                                      <button
                                        type="button"
                                        onClick={() => void handleDeleteActualSet(actualSet)}
                                        disabled={isSubmitting}
                                        className="text-text-muted transition hover:text-danger-action disabled:cursor-not-allowed disabled:opacity-60"
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
                        <div className="mt-4 rounded-[18px] bg-surface px-3 py-3 text-sm font-medium text-text-secondary ring-1 ring-border">
                          No sets logged for this exercise yet.
                        </div>
                      ) : null}

                      {canLogWorkout && allPlannedSetsLogged ? (
                        <div className="mt-3 rounded-lg bg-positive-surface px-3 py-2 text-sm font-semibold text-positive-foreground-strong ring-1 ring-positive-surface">
                          All planned sets logged
                        </div>
                      ) : canLogWorkout ? (
                        <div className="mt-4 rounded-xl bg-surface px-3 py-3 ring-1 ring-border">
                        <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
                          <div>
                            <p className="text-sm font-semibold text-text-strong">
                              Log next set
                            </p>
                            <p className="text-xs font-medium text-text-muted">
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
                            className="rounded-xl bg-action-primary px-3 py-2 text-sm font-semibold text-action-primary-foreground transition hover:bg-action-primary-hover disabled:cursor-not-allowed disabled:opacity-60"
                          >
                            Save set
                          </button>
                        </div>

                        <div className="mt-3 grid gap-2 sm:grid-cols-3">
                          <label className="space-y-1 text-sm text-text-body">
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
                              className="w-full rounded-xl border border-border bg-surface-subtle px-3 py-2 text-sm text-text-strong outline-none ring-0 focus:border-focus-subtle"
                            />
                          </label>
                          <label className="space-y-1 text-sm text-text-body">
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
                              className="w-full rounded-xl border border-border bg-surface-subtle px-3 py-2 text-sm text-text-strong outline-none ring-0 focus:border-focus-subtle"
                            />
                          </label>
                          <label className="space-y-1 text-sm text-text-body">
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
                              className="w-full rounded-xl border border-border bg-surface-subtle px-3 py-2 text-sm text-text-strong outline-none ring-0 focus:border-focus-subtle"
                            />
                          </label>
                        </div>

                        {exerciseNoteInputExpanded ? (
                          <div className="mt-3 space-y-1 text-sm text-text-body">
                            <div className="flex items-center justify-between">
                              <span className="font-medium">Notes</span>
                              <button
                                type="button"
                                onClick={() => toggleExerciseNoteInput(exercise.id)}
                                className="text-xs font-semibold text-text-muted transition hover:text-text-primary"
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
                              className="w-full rounded-xl border border-border bg-surface-subtle px-3 py-2 text-sm text-text-strong outline-none ring-0 focus:border-focus-subtle"
                              placeholder="Optional: form note, pain note, or context."
                            />
                          </div>
                        ) : (
                          <button
                            type="button"
                            onClick={() => toggleExerciseNoteInput(exercise.id)}
                            className="mt-3 text-xs font-semibold text-text-muted transition hover:text-text-primary"
                          >
                            Add note
                          </button>
                        )}
                        </div>
                      ) : null}
                    </div>
                  </article>
                );
              })}
            </div>
          ) : approvedPlan?.exercises.length ? (
            <div className="grid grid-cols-[repeat(auto-fit,minmax(min(100%,20rem),1fr))] gap-3">
              {approvedPlan.exercises.map((exercise, index) => {
                const history =
                  progressionHistoryByExerciseName[
                    normalizeExerciseHistoryKey(exercise.name)
                  ];
                const instructionKey = `preview-${workoutSizePreference}-${previewVariationIndex}-${index}-${
                  exercise.catalog_exercise_id ?? "legacy"
                }`;
                const isInstructionExpanded =
                  expandedInstructionKey === instructionKey;

                return (
                  <article
                    key={`${exercise.name}-${index + 1}`}
                    data-expanded={isInstructionExpanded}
                    className={`rounded-[24px] border border-border bg-surface-subtle/80 p-4 motion-safe:transition-[border-color,background-color,box-shadow] motion-safe:duration-300 ${
                      isInstructionExpanded
                        ? "md:col-span-full md:border-workout-card-active-border md:[background:var(--theme-workout-card-active-surface)] md:p-6 md:shadow-[0_24px_55px_-40px_rgba(15,118,110,0.65)]"
                        : expandedInstructionKey !== null
                          ? "md:hidden"
                          : ""
                    }`}
                  >
                    <div className="space-y-2">
                      <div className="flex flex-wrap items-start justify-between gap-x-4 gap-y-2">
                        <h2 className="min-w-0 text-xl font-semibold text-text-strong">
                          {exercise.name}
                        </h2>
                        <ExerciseInstructionDisclosure
                          key={exercise.catalog_exercise_id ?? "legacy"}
                          catalogExerciseId={exercise.catalog_exercise_id}
                          exerciseName={exercise.name}
                          isExpanded={isInstructionExpanded}
                          onExpandedChange={(nextIsExpanded) =>
                            setExpandedInstructionKey((current) =>
                              nextIsExpanded
                                ? instructionKey
                                : current === instructionKey
                                  ? null
                                  : current,
                            )
                          }
                        />
                      </div>
                      <div
                        className={`space-y-2 ${
                          isInstructionExpanded ? "md:hidden" : ""
                        }`}
                      >
                        <div className="flex flex-wrap gap-2">
                          {exerciseMeta(exercise).map((item) => (
                            <span
                              key={`${exercise.name}-${item}`}
                              className="rounded-full bg-surface px-3 py-1 text-xs font-medium text-text-body"
                            >
                              {item}
                            </span>
                          ))}
                          {exercise.equipment_required.map((item) => (
                            <span
                              key={`${exercise.name}-${item}`}
                              className="rounded-full bg-surface-highlighted px-3 py-1 text-xs font-medium text-positive-foreground-strong"
                            >
                              {item}
                            </span>
                          ))}
                        </div>
                        <PreviousPerformanceLine history={history} />
                      </div>
                    </div>
                  </article>
                );
              })}
            </div>
          ) : (
            <p className="text-sm leading-6 text-text-body">
              No exercise details are available for this workout yet.
            </p>
          )}
        </div>
      </TodayCard>

    </div>
  );
}
