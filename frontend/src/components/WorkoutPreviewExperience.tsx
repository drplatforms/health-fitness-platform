"use client";

import Link from "next/link";
import { useCallback, useEffect, useState, useSyncExternalStore } from "react";

import { ExerciseInstructionDisclosure } from "@/components/ExerciseInstructionDisclosure";
import { StatusPill } from "@/components/StatusPill";
import { TodayCard } from "@/components/TodayCard";
import {
  getBrowserLocalDateString,
  isHistoricalRequestedDate,
} from "@/lib/dateFormatting";
import {
  applyWorkoutSubstitution,
  completeWorkout,
  deleteWorkoutActualSet,
  fetchWorkoutCurrent,
  fetchWorkoutPlannedVsActual,
  fetchWorkoutPreview,
  fetchWorkoutProgressionDecisions,
  fetchWorkoutProgressionHistory,
  fetchWorkoutSubstitutionCandidates,
  logWorkoutActualSet,
  selectWorkoutPreview,
  startWorkoutPlan,
  updateWorkoutActualSet,
} from "@/lib/todayWorkoutApi";
import { buildWeeklyWorkoutHref } from "@/lib/weeklyTrainingPlanApi";
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
  WorkoutProgressionDecision,
  WorkoutProgressionDecisionRequestExercise,
  WorkoutSizePreference,
  WorkoutSubstitutionCandidate,
  WeeklyTrainingContext,
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

function subscribeToHydration() {
  return () => undefined;
}

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
): payload is WorkoutPreviewResponse & {
  approved_workout_plan: ApprovedWorkoutPlanPreview;
  workout_exercise_count: NonNullable<WorkoutPreviewResponse["workout_exercise_count"]>;
} {
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

function initialFocusedExerciseId(
  plannedExercises: PlannedWorkoutExerciseSummary[],
  actualSets: WorkoutActualSetSummary[],
): number | null {
  const firstIncompleteExercise = plannedExercises.find(
    (exercise) =>
      completedSetCount(loggedSetsForExercise(actualSets, exercise.id)) <
      exercise.sets,
  );

  return (
    firstIncompleteExercise?.id ??
    plannedExercises[plannedExercises.length - 1]?.id ??
    null
  );
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

function completionStatusToneClass(summary: ExerciseActualsSummary): string {
  if (summary.plannedSets > 0 && summary.loggedSets >= summary.plannedSets) {
    return "bg-positive-surface text-positive-foreground-strong";
  }
  if (summary.loggedSets === 0) {
    return "bg-danger-surface text-danger-foreground";
  }
  return "bg-caution-surface text-caution-foreground";
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
              <span
                className={`rounded-full px-2 py-1 text-xs font-semibold ${completionStatusToneClass(summary)}`}
              >
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

function progressionDecisionKey(
  catalogExerciseId: number | null,
  exerciseName: string,
): string {
  return catalogExerciseId !== null
    ? `catalog:${catalogExerciseId}`
    : `name:${normalizeExerciseHistoryKey(exerciseName)}`;
}

function mapProgressionDecisions(
  decisions: WorkoutProgressionDecision[],
): Record<string, WorkoutProgressionDecision> {
  return decisions.reduce<Record<string, WorkoutProgressionDecision>>(
    (mapped, decision) => {
      mapped[
        progressionDecisionKey(
          decision.catalog_exercise_id,
          decision.exercise_name,
        )
      ] = decision;
      mapped[`name:${normalizeExerciseHistoryKey(decision.exercise_name)}`] =
        decision;
      return mapped;
    },
    {},
  );
}

function progressionRequestExercise(
  exercise: WorkoutPreviewExercise | PlannedWorkoutExerciseSummary,
  activeSubstitution?: WorkoutActiveSubstitutionSummary,
): WorkoutProgressionDecisionRequestExercise {
  return {
    exercise_name:
      activeSubstitution?.replacement_exercise_name ?? exercise.name,
    catalog_exercise_id:
      activeSubstitution?.replacement_catalog_exercise_id ??
      exercise.catalog_exercise_id,
    sets: exercise.sets,
    reps_min: exercise.reps_min,
    reps_max: exercise.reps_max,
    rir_min: exercise.rir_min,
    rir_max: exercise.rir_max,
  };
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
      <div className="py-2 text-xs font-medium text-text-secondary">
        {history.message}
      </div>
    );
  }

  return (
    <div className="space-y-1 py-2 text-xs text-text-body">
      {history.last_session_summary ? (
        <p>
          <span className="font-semibold text-text-primary">Last time:</span>{" "}
          {history.last_session_summary}
        </p>
      ) : null}
      <details>
        <summary className="cursor-pointer font-semibold text-text-secondary">
          History details
        </summary>
        <div className="mt-1 space-y-1 text-text-secondary">
          {history.recent_best_set ? (
            <p>Recent best: {history.recent_best_set.summary}</p>
          ) : null}
          <p>
            {history.completed_session_count} completed{" "}
            {history.completed_session_count === 1 ? "session" : "sessions"} in
            the last {HISTORY_LOOKBACK_DAYS} days
          </p>
          {history.logging_quality !== "complete" ? (
            <p className="font-medium text-caution-foreground">
              {history.message}
            </p>
          ) : null}
        </div>
      </details>
    </div>
  );
}

function NextTargetBlock({
  decision,
}: {
  decision: WorkoutProgressionDecision | undefined;
}) {
  if (!decision) {
    return null;
  }

  return (
    <div className="py-2 text-xs text-text-body">
      <p className="text-[0.68rem] font-semibold uppercase tracking-[0.14em] text-text-muted">
        Next target
      </p>
      <p className="mt-1 font-semibold text-text-primary">
        {decision.headline}
      </p>
      <p className="mt-0.5 leading-5">{decision.target_guidance}</p>
      <details className="mt-1.5">
        <summary className="cursor-pointer font-semibold text-text-secondary">
          Why?
        </summary>
        <p className="mt-1 leading-5 text-text-secondary">
          {decision.why_this_recommendation}
        </p>
      </details>
    </div>
  );
}

function SubstitutionCandidateOption({
  candidate,
  applyingCandidateId,
  onApply,
}: {
  candidate: WorkoutSubstitutionCandidate;
  applyingCandidateId: number | null;
  onApply: (candidate: WorkoutSubstitutionCandidate) => void;
}) {
  const isApplying = applyingCandidateId === candidate.catalog_exercise_id;

  return (
    <div className="rounded-xl bg-surface px-3 py-3 ring-1 ring-border">
      <div className="flex min-w-0 flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <p className="text-sm font-semibold text-text-strong">
            {candidate.name}
          </p>
          <p className="mt-1 text-xs leading-5 text-text-secondary">
            {candidate.why_this_fits}
          </p>
          {candidate.required_equipment.length ? (
            <p className="mt-1 text-xs font-medium text-text-muted">
              Equipment: {candidate.required_equipment.join(", ")}
            </p>
          ) : null}
        </div>
        <button
          type="button"
          onClick={() => onApply(candidate)}
          disabled={applyingCandidateId !== null}
          aria-label={`Use this exercise: ${candidate.name}`}
          className="min-h-11 shrink-0 rounded-xl bg-action-primary px-3 py-2 text-sm font-semibold text-action-primary-foreground transition hover:bg-action-primary-hover disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isApplying ? "Applying…" : "Use this exercise"}
        </button>
      </div>
    </div>
  );
}

function WorkoutSubstitutionPanel({
  exercise,
  candidates,
  isLoading,
  loadError,
  applyError,
  applyingCandidateId,
  onApply,
  onClose,
}: {
  exercise: PlannedWorkoutExerciseSummary;
  candidates: WorkoutSubstitutionCandidate[];
  isLoading: boolean;
  loadError: boolean;
  applyError: boolean;
  applyingCandidateId: number | null;
  onApply: (candidate: WorkoutSubstitutionCandidate) => void;
  onClose: () => void;
}) {
  const bestMatch = candidates.find(
    (candidate) => candidate.match_tier === "best_match",
  );
  const alsoCompatible = candidates.filter(
    (candidate) => candidate.match_tier === "also_compatible",
  );

  return (
    <section
      id={`workout-substitutions-${exercise.id}`}
      aria-label={`Substitution options for ${exercise.name}`}
      className="mt-3 min-w-0 rounded-2xl bg-surface-subtle p-3 ring-1 ring-border"
    >
      <div className="flex items-center justify-between gap-3">
        <h3 className="text-sm font-semibold text-text-strong">
          Swap exercise
        </h3>
        <button
          type="button"
          onClick={onClose}
          aria-label={`Close substitution options for ${exercise.name}`}
          className="min-h-11 rounded-lg px-3 py-2 text-sm font-semibold text-text-muted transition hover:bg-surface hover:text-text-primary"
        >
          Close
        </button>
      </div>

      {isLoading ? (
        <p className="py-3 text-sm font-medium text-text-secondary">
          Finding compatible options…
        </p>
      ) : loadError ? (
        <p className="py-3 text-sm font-medium text-danger-action">
          Unable to load substitutions right now.
        </p>
      ) : candidates.length === 0 ? (
        <p className="py-3 text-sm font-medium text-text-secondary">
          No compatible substitutions are available for your current equipment.
        </p>
      ) : (
        <div className="max-h-80 space-y-4 overflow-y-auto overflow-x-hidden pr-1">
          {bestMatch ? (
            <div className="space-y-2">
              <p className="text-xs font-semibold uppercase tracking-[0.12em] text-positive-foreground">
                Best Match
              </p>
              <SubstitutionCandidateOption
                candidate={bestMatch}
                applyingCandidateId={applyingCandidateId}
                onApply={onApply}
              />
            </div>
          ) : null}
          {alsoCompatible.length ? (
            <div className="space-y-2">
              <p className="text-xs font-semibold uppercase tracking-[0.12em] text-text-muted">
                Also Compatible
              </p>
              {alsoCompatible.map((candidate) => (
                <SubstitutionCandidateOption
                  key={candidate.catalog_exercise_id}
                  candidate={candidate}
                  applyingCandidateId={applyingCandidateId}
                  onApply={onApply}
                />
              ))}
            </div>
          ) : null}
        </div>
      )}

      {applyError ? (
        <p className="mt-3 text-sm font-medium text-danger-action">
          Unable to apply that substitution.
        </p>
      ) : null}
    </section>
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
  const [sizePreferenceInitialized, setSizePreferenceInitialized] = useState(false);
  const [trainAnywayOverride, setTrainAnywayOverride] = useState(false);
  const [preview, setPreview] = useState<WorkoutPreviewResponse | null>(null);
  const [weeklyTrainingContext, setWeeklyTrainingContext] =
    useState<WeeklyTrainingContext | null>(null);
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
  const [substitutionPanelExerciseId, setSubstitutionPanelExerciseId] = useState<
    number | null
  >(null);
  const [substitutionCandidates, setSubstitutionCandidates] = useState<
    WorkoutSubstitutionCandidate[]
  >([]);
  const [isLoadingSubstitutions, setIsLoadingSubstitutions] = useState(false);
  const [substitutionLoadError, setSubstitutionLoadError] = useState(false);
  const [substitutionApplyError, setSubstitutionApplyError] = useState(false);
  const [applyingSubstitutionCandidateId, setApplyingSubstitutionCandidateId] =
    useState<number | null>(null);
  const [plannedVsActualSummary, setPlannedVsActualSummary] =
    useState<WorkoutPlannedVsActualSummary | null>(null);
  const [progressionHistoryByExerciseName, setProgressionHistoryByExerciseName] =
    useState<Record<string, WorkoutExerciseHistorySummary>>({});
  const [progressionDecisionByExerciseKey, setProgressionDecisionByExerciseKey] =
    useState<Record<string, WorkoutProgressionDecision>>({});
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
  const [focusedExerciseId, setFocusedExerciseId] = useState<number | null>(null);
  const [isCompletionReviewOpen, setIsCompletionReviewOpen] = useState(false);
  const [expandedInstructionKey, setExpandedInstructionKey] = useState<
    string | null
  >(null);
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isLoadingPreview, setIsLoadingPreview] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const isHydrated = useSyncExternalStore(
    subscribeToHydration,
    () => true,
    () => false,
  );
  const isHistoricalReadOnly = requestedDate
    ? isHydrated
      ? isHistoricalRequestedDate(requestedDate)
      : null
    : false;

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
    isHistoricalReadOnly === false && !isPersistedState && !isCompletedState
      ? `Version ${previewVariationIndex + 1}`
      : null,
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

  const loadProgressionDecisionsForExercises = useCallback(
    async function (
      exercises: WorkoutProgressionDecisionRequestExercise[],
    ): Promise<Record<string, WorkoutProgressionDecision>> {
      if (!exercises.length) {
        return {};
      }

      const result = await fetchWorkoutProgressionDecisions(
        userId,
        requestedDate ?? getBrowserLocalDateString(),
        exercises,
      );
      if (result.error || !result.data) {
        return {};
      }

      return mapProgressionDecisions(result.data.progression_decisions);
    },
    [requestedDate, userId],
  );

  useEffect(() => {
    if (isHistoricalReadOnly === null) {
      return;
    }

    let cancelled = false;

    async function loadWorkoutState() {
      setIsLoadingPreview(true);
      setErrorMessage(null);
      setActionMessage(null);
      setIsCompletionReviewOpen(false);
      setSubstitutionPanelExerciseId(null);
      setSubstitutionCandidates([]);
      setSubstitutionLoadError(false);
      setSubstitutionApplyError(false);
      setApplyingSubstitutionCandidateId(null);

      try {
        const currentResult = await fetchWorkoutCurrent({
          userId,
          date: requestedDate ?? getBrowserLocalDateString(),
        });

        if (cancelled) {
          return;
        }

        const currentData = currentResult.data;
        setDailyState(currentData?.workout_daily_state ?? null);
        setWeeklyTrainingContext(currentData?.weekly_training_context ?? null);

        if (!sizePreferenceInitialized) {
          const weeklyDefault =
            currentData?.weekly_training_context
              .default_workout_size_preference;
          const initialSize = weeklyDefault === "extended" ? "full" : weeklyDefault;
          setSizePreferenceInitialized(true);
          if (initialSize && initialSize !== workoutSizePreference) {
            setWorkoutSizePreference(initialSize);
            return;
          }
        }

        if (currentData?.workout_daily_state.state === "completed_today") {
          const currentExecution = currentData.current_execution_state;
          setPreview(null);
          setViewMode("completed");
          setPersistedPlan(currentExecution?.approved_workout_plan ?? null);
          setSelectedPlan(currentExecution?.workout_plan_instance ?? null);
          setExecutionSession(currentExecution?.execution_session ?? null);
          setPlannedExercises(currentExecution?.planned_exercises ?? []);
          setActualSets(currentExecution?.actual_sets ?? []);
          setFocusedExerciseId(null);
          setActiveSubstitutions(currentExecution?.active_substitutions ?? []);
          setFormStateByExerciseId({});
          setNoteInputExpandedByExerciseId({});
          setProgressionHistoryByExerciseName(
            await loadProgressionHistoryForNames(
              currentExecution?.planned_exercises.map((exercise) => exercise.name) ??
                [],
            ),
          );
          setProgressionDecisionByExerciseKey({});
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
          setFocusedExerciseId(
            currentExecution.workout_plan_instance.status === "started" ||
              currentExecution.workout_plan_instance.status === "in_progress" ||
              currentExecution.execution_session.status === "started" ||
              currentExecution.execution_session.status === "in_progress"
              ? initialFocusedExerciseId(
                  currentExecution.planned_exercises,
                  currentExecution.actual_sets,
                )
              : null,
          );
          setActiveSubstitutions(currentExecution.active_substitutions);
          setFormStateByExerciseId({});
          setNoteInputExpandedByExerciseId({});
          setProgressionHistoryByExerciseName(
            await loadProgressionHistoryForNames(
              currentExecution.planned_exercises.map((exercise) => exercise.name),
            ),
          );
          const substitutionsByExerciseId = new Map(
            currentExecution.active_substitutions.map((substitution) => [
              substitution.planned_workout_exercise_id,
              substitution,
            ]),
          );
          setProgressionDecisionByExerciseKey(
            await loadProgressionDecisionsForExercises(
              currentExecution.planned_exercises.map((exercise) =>
                progressionRequestExercise(
                  exercise,
                  substitutionsByExerciseId.get(exercise.id),
                ),
              ),
            ),
          );
          await loadPlannedVsActualSummary(
            currentExecution.workout_plan_instance.id,
            currentExecution.execution_session.status,
          );
          return;
        }

        if (isHistoricalReadOnly) {
          setPreview(null);
          setViewMode("preview");
          setPersistedPlan(null);
          setSelectedPlan(null);
          setExecutionSession(null);
          setPlannedExercises([]);
          setActualSets([]);
          setFocusedExerciseId(null);
          setActiveSubstitutions([]);
          setPlannedVsActualSummary(null);
          setProgressionHistoryByExerciseName({});
          setProgressionDecisionByExerciseKey({});
          setErrorMessage(currentResult.error?.message ?? null);
          return;
        }

        const previewResult = await fetchWorkoutPreview({
          userId,
          workoutSizePreference,
          previewVariationIndex,
          targetDate: requestedDate ?? getBrowserLocalDateString(),
          trainAnyway: trainAnywayOverride,
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
          setFocusedExerciseId(null);
          setActiveSubstitutions([]);
          setPlannedVsActualSummary(null);
          setProgressionHistoryByExerciseName({});
          setProgressionDecisionByExerciseKey({});
          setErrorMessage(
            previewResult.error.message ??
              currentResult.error?.message ??
              "Workout preview is not available right now.",
          );
          return;
        }

        if (previewResult.data?.rest_day) {
          setPreview(previewResult.data);
          setWeeklyTrainingContext(previewResult.data.weekly_training_context);
          setViewMode("preview");
          setPersistedPlan(null);
          setSelectedPlan(null);
          setExecutionSession(null);
          setPlannedExercises([]);
          setActualSets([]);
          setFocusedExerciseId(null);
          setActiveSubstitutions([]);
          setPlannedVsActualSummary(null);
          setProgressionHistoryByExerciseName({});
          setProgressionDecisionByExerciseKey({});
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
          setFocusedExerciseId(null);
          setActiveSubstitutions([]);
          setPlannedVsActualSummary(null);
          setProgressionHistoryByExerciseName({});
          setProgressionDecisionByExerciseKey({});
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
        setFocusedExerciseId(null);
        setActiveSubstitutions([]);
        setPlannedVsActualSummary(null);
        setPreview(previewResult.data);
        setWeeklyTrainingContext(previewResult.data.weekly_training_context);
        setProgressionHistoryByExerciseName(
          await loadProgressionHistoryForNames(
            previewResult.data.approved_workout_plan.exercises.map(
              (exercise) => exercise.name,
            ),
          ),
        );
        setProgressionDecisionByExerciseKey(
          await loadProgressionDecisionsForExercises(
            previewResult.data.approved_workout_plan.exercises.map((exercise) =>
              progressionRequestExercise(exercise),
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
    isHistoricalReadOnly,
    loadProgressionHistoryForNames,
    loadProgressionDecisionsForExercises,
    previewVariationIndex,
    requestedDate,
    sizePreferenceInitialized,
    trainAnywayOverride,
    userId,
    workoutSizePreference,
  ]);

  function handleSizeChange(nextValue: WorkoutSizePreference) {
    setExpandedInstructionKey(null);
    setWorkoutSizePreference(nextValue);
    setSizePreferenceInitialized(true);
    setPreviewVariationIndex(0);
    setViewMode("preview");
    setDailyState(null);
    setPersistedPlan(null);
    setSelectedPlan(null);
    setExecutionSession(null);
    setPlannedExercises([]);
    setActualSets([]);
    setFocusedExerciseId(null);
    setActiveSubstitutions([]);
    setPlannedVsActualSummary(null);
    setProgressionHistoryByExerciseName({});
    setProgressionDecisionByExerciseKey({});
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
    setFocusedExerciseId(null);
    setActiveSubstitutions([]);
    setPlannedVsActualSummary(null);
    setProgressionHistoryByExerciseName({});
    setProgressionDecisionByExerciseKey({});
    setIsCompletionReviewOpen(false);
    setActionMessage(null);
    setErrorMessage(null);
  }

  function handleTrainAnyway() {
    setTrainAnywayOverride(true);
    setPreviewVariationIndex(0);
    setPreview(null);
    setActionMessage("Building an optional workout without changing the weekly plan.");
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

  function closeSubstitutionPanel() {
    setSubstitutionPanelExerciseId(null);
    setSubstitutionCandidates([]);
    setIsLoadingSubstitutions(false);
    setSubstitutionLoadError(false);
    setSubstitutionApplyError(false);
  }

  async function handleToggleSubstitutionPanel(
    exercise: PlannedWorkoutExerciseSummary,
  ) {
    if (substitutionPanelExerciseId === exercise.id) {
      closeSubstitutionPanel();
      return;
    }
    if (selectedPlan === null) {
      return;
    }

    setSubstitutionPanelExerciseId(exercise.id);
    setSubstitutionCandidates([]);
    setSubstitutionLoadError(false);
    setSubstitutionApplyError(false);
    setIsLoadingSubstitutions(true);

    const result = await fetchWorkoutSubstitutionCandidates(
      selectedPlan.id,
      exercise.id,
    );

    if (result.error || !result.data) {
      setSubstitutionLoadError(true);
      setIsLoadingSubstitutions(false);
      return;
    }

    setSubstitutionCandidates(result.data.substitution_candidates);
    setIsLoadingSubstitutions(false);
  }

  async function handleApplySubstitution(
    exercise: PlannedWorkoutExerciseSummary,
    candidate: WorkoutSubstitutionCandidate,
  ) {
    if (selectedPlan === null) {
      return;
    }

    setApplyingSubstitutionCandidateId(candidate.catalog_exercise_id);
    setSubstitutionApplyError(false);
    const result = await applyWorkoutSubstitution(
      selectedPlan.id,
      exercise.id,
      candidate.catalog_exercise_id,
    );

    if (result.error || !result.data?.active_substitution) {
      setSubstitutionApplyError(true);
      setApplyingSubstitutionCandidateId(null);
      return;
    }

    const activeSubstitution = result.data.active_substitution;
    setActiveSubstitutions((current) => [
      ...current.filter(
        (substitution) =>
          substitution.planned_workout_exercise_id !== exercise.id,
      ),
      activeSubstitution,
    ]);
    setSelectedPlan(result.data.workout_plan_instance ?? selectedPlan);
    const replacementHistory = await loadProgressionHistoryForNames([
      activeSubstitution.replacement_exercise_name,
    ]);
    setProgressionHistoryByExerciseName((current) => ({
      ...current,
      ...replacementHistory,
    }));
    const replacementDecisions = await loadProgressionDecisionsForExercises([
      progressionRequestExercise(exercise, activeSubstitution),
    ]);
    setProgressionDecisionByExerciseKey((current) => ({
      ...current,
      ...replacementDecisions,
    }));
    setActionMessage(
      `Using ${activeSubstitution.replacement_exercise_name} instead of ${exercise.name}.`,
    );
    setApplyingSubstitutionCandidateId(null);
    closeSubstitutionPanel();
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
      setFocusedExerciseId(null);
      setActiveSubstitutions([]);
      setPlannedVsActualSummary(null);
      setProgressionHistoryByExerciseName(
        await loadProgressionHistoryForNames(
          result.data?.planned_exercises.map((exercise) => exercise.name) ?? [],
        ),
      );
      setProgressionDecisionByExerciseKey(
        await loadProgressionDecisionsForExercises(
          (result.data?.planned_exercises ?? []).map((exercise) =>
            progressionRequestExercise(exercise),
          ),
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
      const nextPlannedExercises =
        result.data?.planned_exercises ?? plannedExercises;
      setPlannedExercises(nextPlannedExercises);
      setActualSets([]);
      setFocusedExerciseId(initialFocusedExerciseId(nextPlannedExercises, []));
      setActiveSubstitutions([]);
      setPlannedVsActualSummary(null);
      setProgressionHistoryByExerciseName(
        await loadProgressionHistoryForNames(
          (result.data?.planned_exercises ?? plannedExercises).map(
            (exercise) => exercise.name,
          ),
        ),
      );
      setProgressionDecisionByExerciseKey(
        await loadProgressionDecisionsForExercises(
          (result.data?.planned_exercises ?? plannedExercises).map((exercise) =>
            progressionRequestExercise(exercise),
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
      setActionMessage(null);
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
      setProgressionDecisionByExerciseKey({});
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
    isHistoricalReadOnly === false &&
    selectedPlan !== null &&
    executionSession !== null &&
    selectedPlan.status === "selected" &&
    executionSession.status === "selected";
  const canLogWorkout =
    isHistoricalReadOnly === false &&
    selectedPlan !== null &&
    executionSession !== null &&
    (selectedPlan.status === "started" ||
      selectedPlan.status === "in_progress" ||
      executionSession.status === "started" ||
      executionSession.status === "in_progress");
  const canCompleteWorkout =
    isHistoricalReadOnly === false &&
    selectedPlan !== null &&
    executionSession !== null &&
    (selectedPlan.status === "in_progress" ||
      executionSession.status === "in_progress");
  const effectiveFocusedExerciseId =
    canLogWorkout &&
    focusedExerciseId !== null &&
    plannedExercises.some((exercise) => exercise.id === focusedExerciseId)
      ? focusedExerciseId
      : canLogWorkout
        ? initialFocusedExerciseId(plannedExercises, actualSets)
        : null;
  const focusedExerciseIndex = plannedExercises.findIndex(
    (exercise) => exercise.id === effectiveFocusedExerciseId,
  );
  const focusedExercise =
    focusedExerciseIndex >= 0 ? plannedExercises[focusedExerciseIndex] : null;
  const completedWorkoutSetCount = completedSetCount(actualSets);
  const plannedWorkoutSetCount = plannedExercises.reduce(
    (total, exercise) => total + exercise.sets,
    0,
  );
  const workoutCompletionPercentage =
    plannedWorkoutSetCount > 0
      ? Math.min(
          100,
          Math.round(
            (completedWorkoutSetCount / plannedWorkoutSetCount) * 100,
          ),
        )
      : 0;
  const completionReviewMissingSets = plannedVsActualSummary
    ? missingSetCount(plannedVsActualSummary)
    : 0;
  const hasCompletionReviewMissingSets =
    plannedVsActualSummary !== null && completionReviewMissingSets > 0;
  const targetDate = requestedDate ?? (isHydrated ? getBrowserLocalDateString() : "");

  if (
    preview?.rest_day &&
    weeklyTrainingContext?.day_type === "rest" &&
    !trainAnywayOverride &&
    !isPersistedState &&
    !isCompletedState
  ) {
    return (
      <section className="rounded-2xl bg-surface px-4 py-4 ring-1 ring-border">
        <p className="text-xs font-semibold uppercase tracking-[0.14em] text-text-muted">
          This week
        </p>
        <h2 className="mt-1 text-xl font-semibold text-text-strong">Rest day</h2>
        <p className="mt-1 text-sm text-text-body">
          No training session is scheduled today.
        </p>
        <div className="mt-4 grid grid-cols-2 gap-2 sm:flex">
          <button
            type="button"
            onClick={handleTrainAnyway}
            className="rounded-xl bg-action-primary px-4 py-2.5 text-sm font-semibold text-action-primary-foreground hover:bg-action-primary-hover"
          >
            Train anyway
          </button>
          <Link
            href={buildWeeklyWorkoutHref(userId, targetDate)}
            className="rounded-xl bg-surface-muted px-4 py-2.5 text-center text-sm font-semibold text-text-body hover:bg-surface-interactive-hover"
          >
            View week
          </Link>
        </div>
      </section>
    );
  }

  return (
    <div className="grid min-w-0 gap-3 lg:grid-cols-[minmax(0,1.45fr)_minmax(320px,0.95fr)] lg:gap-6 xl:grid-cols-[minmax(0,1.55fr)_minmax(360px,1fr)]">
      {weeklyTrainingContext?.has_weekly_plan &&
      (weeklyTrainingContext.session_title || weeklyTrainingContext.is_override) ? (
        <div className="min-w-0 rounded-xl bg-surface-subtle px-3 py-2 text-sm font-semibold text-text-body ring-1 ring-border lg:col-span-2">
          This week · {weeklyTrainingContext.session_title ?? "Rest day"}
          {weeklyTrainingContext.is_override ? " · Training anyway" : ""}
        </div>
      ) : null}
      {canLogWorkout ? (
        <div className="min-w-0 rounded-2xl bg-surface px-3 py-2.5 ring-1 ring-border md:hidden">
          <div className="flex items-center justify-between gap-2 text-xs font-semibold uppercase tracking-[0.08em]">
            <span className="text-text-strong">In progress</span>
            <span className="text-text-body">
              {completedWorkoutSetCount} / {plannedWorkoutSetCount} sets
            </span>
            <span className="text-positive-foreground-strong">
              {workoutCompletionPercentage}%
            </span>
            {canCompleteWorkout && !isCompletionReviewOpen ? (
              <button
                type="button"
                onClick={() => void handleOpenCompletionReview()}
                disabled={isSubmitting}
                className="rounded-lg bg-caution-action px-2.5 py-1.5 text-[0.7rem] font-semibold normal-case tracking-normal text-text-inverse transition hover:bg-caution-action-hover disabled:cursor-not-allowed disabled:opacity-60"
              >
                Finish
              </button>
            ) : null}
          </div>
          <div
            className="mt-2 h-1.5 overflow-hidden rounded-full bg-surface-muted"
            aria-label={`${workoutCompletionPercentage}% of planned workout sets complete`}
          >
            <div
              className="h-full rounded-full bg-action-primary transition-[width]"
              style={{ width: `${workoutCompletionPercentage}%` }}
            />
          </div>
          {errorMessage ? (
            <div className="mt-2 rounded-xl bg-danger-surface px-3 py-2 text-sm font-medium normal-case tracking-normal text-danger-foreground">
              {errorMessage}
            </div>
          ) : null}
        </div>
      ) : null}

      {!canLogWorkout ? (
        <section className="min-w-0 rounded-2xl bg-surface px-3 py-2.5 ring-1 ring-border md:hidden">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <p className="text-sm font-semibold text-text-strong">
                {statusSummaryLine(
                  approvedPlan,
                  preview,
                  viewMode,
                  summaryStatus,
                  plannedVsActualSummary,
                )}
              </p>
              {topMetrics.length ? (
                <p className="mt-0.5 truncate text-xs text-text-secondary">
                  {topMetrics.slice(0, 2).join(" · ")}
                </p>
              ) : null}
            </div>
            <StatusPill
              label={statusLabel.replaceAll("_", " ")}
              tone={statusTone}
            />
          </div>
          {isHistoricalReadOnly ? (
            <p className="mt-2 text-xs font-semibold text-text-secondary">
              Historical workout · Read only
            </p>
          ) : null}
          {isLoadingPreview ? (
            <p className="mt-2 text-xs font-medium text-neutral-foreground">
              Loading workout preview...
            </p>
          ) : null}
          {actionMessage ? (
            <p className="mt-2 text-xs font-medium text-positive-foreground-strong">
              {actionMessage}
            </p>
          ) : null}
          {errorMessage ? (
            <p className="mt-2 text-xs font-medium text-danger-foreground">
              {errorMessage}
            </p>
          ) : null}
        </section>
      ) : null}

      <TodayCard
        title="Session Status"
        accent="highlight"
        className="hidden min-w-0 md:block lg:col-span-2 lg:row-start-1"
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
            {isHistoricalReadOnly ? (
              <span className="rounded-full bg-surface px-3 py-1.5 text-xs font-semibold text-text-body ring-1 ring-border">
                Historical workout · Read only
              </span>
            ) : null}
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
          className={
            canLogWorkout
              ? "hidden min-w-0 md:block lg:col-span-2"
              : "min-w-0 lg:col-span-2"
          }
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
        className="min-w-0 lg:col-span-2"
      >
        <div className="space-y-4">
          {isHistoricalReadOnly === false &&
          !isPersistedState &&
          !isCompletedState ? (
            <div
              className={`rounded-xl bg-surface-subtle px-3 py-3 md:rounded-2xl md:px-4 md:py-4 ${
                expandedInstructionKey !== null ? "md:hidden" : ""
              }`}
            >
              <div className="space-y-3">
                <div className="grid grid-cols-3 gap-2 sm:flex sm:flex-wrap">
                  {sizeOptions.map((option) => {
                    const isActive = option.value === workoutSizePreference;
                    return (
                      <button
                        key={option.value}
                        type="button"
                        onClick={() => handleSizeChange(option.value)}
                        className={`rounded-xl px-2 py-2 text-sm font-semibold transition sm:rounded-full sm:px-4 ${
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
                <div className="grid grid-cols-2 gap-2 sm:flex sm:flex-wrap sm:gap-3">
                  <button
                    type="button"
                    onClick={handleTryDifferentVersion}
                    disabled={isLoadingPreview || isSubmitting}
                    className="rounded-xl bg-surface px-3 py-2.5 text-sm font-semibold text-text-primary ring-1 ring-border transition hover:bg-surface-subtle disabled:cursor-not-allowed disabled:opacity-60 sm:rounded-2xl sm:px-4 sm:py-3"
                  >
                    Try different version
                  </button>
                  <button
                    type="button"
                    onClick={() => void handleSelectWorkout()}
                    disabled={approvedPlan === null || isLoadingPreview || isSubmitting}
                    className="rounded-xl bg-action-primary px-3 py-2.5 text-sm font-semibold text-action-primary-foreground transition hover:bg-action-primary-hover disabled:cursor-not-allowed disabled:opacity-60 sm:rounded-2xl sm:px-4 sm:py-3"
                  >
                    Select this workout
                  </button>
                </div>
              </div>
            </div>
          ) : null}

          {canLogWorkout && focusedExercise ? (
            <div className="rounded-2xl bg-surface px-3 py-2.5 ring-1 ring-border md:hidden">
              <p className="text-xs font-semibold uppercase tracking-[0.14em] text-text-muted">
                Exercise {focusedExerciseIndex + 1} of {plannedExercises.length}
              </p>

              <div className="mt-2 flex items-center gap-2">
                <button
                  type="button"
                  onClick={() =>
                    setFocusedExerciseId(
                      plannedExercises[focusedExerciseIndex - 1]?.id ??
                        focusedExercise.id,
                    )
                  }
                  disabled={focusedExerciseIndex <= 0}
                  aria-label="Previous exercise"
                  className="min-h-10 rounded-xl bg-surface-muted px-2.5 text-xs font-semibold text-text-body transition hover:bg-surface-interactive-hover disabled:cursor-not-allowed disabled:opacity-40"
                >
                  Previous
                </button>
                <div className="flex min-w-0 flex-1 justify-center gap-1.5 overflow-x-auto py-1 [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
                  {plannedExercises.map((exercise, index) => {
                    const displayName =
                      activeSubstitutionByExerciseId.get(exercise.id)
                        ?.replacement_exercise_name ?? exercise.name;
                    const isComplete =
                      completedSetCount(
                        loggedSetsForExercise(actualSets, exercise.id),
                      ) >= exercise.sets;
                    const isCurrent = exercise.id === focusedExercise.id;

                    return (
                      <button
                        key={exercise.id}
                        type="button"
                        onClick={() => setFocusedExerciseId(exercise.id)}
                        aria-label={`Go to exercise ${index + 1}: ${displayName}`}
                        aria-current={isCurrent ? "step" : undefined}
                        className={`min-h-9 min-w-9 rounded-full text-xs font-semibold ring-1 transition ${
                          isCurrent
                            ? "bg-action-primary text-action-primary-foreground ring-action-primary"
                            : isComplete
                              ? "bg-positive-surface text-positive-foreground-strong ring-positive-surface"
                              : "bg-surface-subtle text-text-body ring-border"
                        }`}
                      >
                        <span aria-hidden="true">{isComplete ? "✓" : index + 1}</span>
                      </button>
                    );
                  })}
                </div>
                <button
                  type="button"
                  onClick={() =>
                    setFocusedExerciseId(
                      plannedExercises[focusedExerciseIndex + 1]?.id ??
                        focusedExercise.id,
                    )
                  }
                  disabled={focusedExerciseIndex >= plannedExercises.length - 1}
                  aria-label="Next exercise"
                  className="min-h-10 rounded-xl bg-surface-muted px-2.5 text-xs font-semibold text-text-body transition hover:bg-surface-interactive-hover disabled:cursor-not-allowed disabled:opacity-40"
                >
                  Next
                </button>
              </div>
            </div>
          ) : null}

          {canStartWorkout || canCompleteWorkout ? (
            <div
              className={`space-y-3 ${
                expandedInstructionKey !== null ? "md:hidden" : ""
              } ${
                canCompleteWorkout &&
                !isCompletionReviewOpen &&
                !canStartWorkout
                  ? "hidden md:block"
                  : ""
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
                    className="hidden rounded-2xl bg-caution-action px-4 py-3 text-sm font-semibold text-text-inverse transition hover:bg-caution-action-hover disabled:cursor-not-allowed disabled:opacity-60 md:block"
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
                const progressionDecision =
                  progressionDecisionByExerciseKey[
                    progressionDecisionKey(
                      displayedCatalogExerciseId,
                      displayExerciseName,
                    )
                  ] ??
                  progressionDecisionByExerciseKey[
                    `name:${normalizeExerciseHistoryKey(displayExerciseName)}`
                  ];
                const instructionKey = `persisted-${exercise.id}-${
                  displayedCatalogExerciseId ?? "legacy"
                }`;
                const isInstructionExpanded =
                  expandedInstructionKey === instructionKey;
                const isEditingExerciseSet = exerciseActualSets.some(
                  (actualSet) => actualSet.id === editingActualSetId,
                );
                const canOfferSubstitution =
                  isHistoricalReadOnly === false &&
                  isPersistedState &&
                  selectedPlan !== null &&
                  ["selected", "started", "in_progress"].includes(
                    selectedPlan.status,
                  ) &&
                  completedLoggedSetCount === 0;
                const isSubstitutionPanelOpen =
                  substitutionPanelExerciseId === exercise.id;

                return (
                  <article
                    key={exercise.id}
                    data-expanded={isInstructionExpanded}
                    className={`border-t border-border-subtle bg-transparent py-3 first:border-t-0 motion-safe:transition-[border-color,background-color,box-shadow] motion-safe:duration-300 md:rounded-[24px] md:border md:border-border md:bg-surface-subtle/80 md:p-4 ${
                      canLogWorkout && effectiveFocusedExerciseId !== exercise.id
                        ? "hidden md:block"
                        : ""
                    } ${
                      isInstructionExpanded
                        ? "md:col-span-full md:border-workout-card-active-border md:[background:var(--theme-workout-card-active-surface)] md:p-6 md:shadow-[0_24px_55px_-40px_rgba(15,118,110,0.65)]"
                        : expandedInstructionKey !== null
                          ? "md:hidden"
                          : ""
                    }`}
                  >
                    <div className="space-y-2">
                      <div className="flex flex-wrap items-start justify-between gap-x-4 gap-y-2">
                        <h2 className="min-w-0 text-lg font-semibold uppercase tracking-[0.04em] text-text-strong md:text-xl md:normal-case md:tracking-normal">
                          {displayExerciseName}
                        </h2>
                        {canOfferSubstitution ? (
                          <button
                            type="button"
                            onClick={() =>
                              void handleToggleSubstitutionPanel(exercise)
                            }
                            disabled={applyingSubstitutionCandidateId !== null}
                            aria-expanded={isSubstitutionPanelOpen}
                            aria-controls={`workout-substitutions-${exercise.id}`}
                            className="min-h-11 rounded-xl bg-surface px-3 py-2 text-sm font-semibold text-accent-text ring-1 ring-border transition hover:bg-surface-interactive-hover disabled:cursor-not-allowed disabled:opacity-60"
                          >
                            Swap exercise
                          </button>
                        ) : null}
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
                      {activeSubstitution ? (
                        <p className="text-xs font-semibold text-positive-foreground">
                          Substituted for {exercise.name}
                        </p>
                      ) : null}
                      {canOfferSubstitution && isSubstitutionPanelOpen ? (
                        <WorkoutSubstitutionPanel
                          exercise={exercise}
                          candidates={substitutionCandidates}
                          isLoading={isLoadingSubstitutions}
                          loadError={substitutionLoadError}
                          applyError={substitutionApplyError}
                          applyingCandidateId={applyingSubstitutionCandidateId}
                          onApply={(candidate) =>
                            void handleApplySubstitution(exercise, candidate)
                          }
                          onClose={closeSubstitutionPanel}
                        />
                      ) : null}
                      <div
                        className={`space-y-2 ${
                          isInstructionExpanded ? "md:hidden" : ""
                        }`}
                      >
                        {canLogWorkout ? (
                          <p className="text-sm font-medium text-text-body md:hidden">
                            {exercise.sets} sets <span aria-hidden="true">•</span>{" "}
                            {exercise.reps_min === exercise.reps_max
                              ? exercise.reps_min
                              : `${exercise.reps_min}-${exercise.reps_max}`} reps{" "}
                            <span aria-hidden="true">•</span> RIR{" "}
                            {exercise.rir_min === exercise.rir_max
                              ? exercise.rir_min
                              : `${exercise.rir_min}-${exercise.rir_max}`}
                          </p>
                        ) : null}
                        <div
                          className={
                            canLogWorkout
                              ? "hidden flex-wrap gap-2 md:flex"
                              : "flex flex-wrap gap-2"
                          }
                        >
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
                          <div
                            className={`flex-wrap items-center gap-x-3 gap-y-1 text-xs font-semibold text-positive-foreground ${
                              canLogWorkout ? "hidden md:flex" : "flex"
                            }`}
                          >
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
                        <div className="divide-y divide-border-subtle rounded-xl bg-surface/65 px-3 ring-1 ring-border">
                          <PreviousPerformanceLine history={history} />
                          {isHistoricalReadOnly === false && !isCompletedState ? (
                            <NextTargetBlock decision={progressionDecision} />
                          ) : null}
                        </div>
                      </div>
                    </div>

                    <div
                      className={isInstructionExpanded ? "md:hidden" : ""}
                    >
                      {canLogWorkout ? (
                        <div className="mt-3 flex items-center gap-3 md:hidden">
                          <span className="text-xs font-semibold uppercase tracking-[0.12em] text-text-muted">
                            Sets
                          </span>
                          <div className="flex flex-wrap gap-2">
                            {Array.from({ length: exercise.sets }, (_, index) => {
                              const setNumber = index + 1;
                              const loggedSet = exerciseActualSets.find(
                                (actualSet) =>
                                  actualSet.set_number === setNumber &&
                                  actualSet.completed &&
                                  !actualSet.skipped,
                              );

                              return loggedSet ? (
                                <button
                                  key={setNumber}
                                  type="button"
                                  onClick={() => handleEditSet(loggedSet)}
                                  disabled={isSubmitting}
                                  aria-label={`Edit logged set ${setNumber}: ${formatActualSetLine(loggedSet)}`}
                                  className="flex min-h-10 min-w-10 items-center justify-center rounded-full bg-positive-surface text-sm font-bold text-positive-foreground-strong ring-1 ring-positive-surface transition hover:bg-surface-highlighted disabled:cursor-not-allowed disabled:opacity-60"
                                >
                                  <span aria-hidden="true">✓</span>
                                </button>
                              ) : (
                                <span
                                  key={setNumber}
                                  aria-label={`Set ${setNumber} not logged`}
                                  className="flex min-h-10 min-w-10 items-center justify-center rounded-full bg-surface text-sm font-semibold text-text-muted ring-1 ring-border"
                                >
                                  {setNumber}
                                </span>
                              );
                            })}
                          </div>
                        </div>
                      ) : null}

                      {exerciseActualSets.length ? (
                        <div
                          className={`space-y-2 md:mt-4 ${
                            isEditingExerciseSet ? "mt-3" : ""
                          }`}
                        >
                        {exerciseActualSets.map((actualSet) => {
                          const isEditing = editingActualSetId === actualSet.id;
                          const editFormState =
                            editFormStateByActualSetId[actualSet.id] ??
                            actualSetFormStateFromSet(actualSet);

                          return (
                            <div
                              key={actualSet.id}
                              className={`rounded-lg bg-surface/90 px-3 py-2 ring-1 ring-border ${
                                isEditing || !canLogWorkout ? "" : "hidden md:block"
                              }`}
                            >
                              {isEditing ? (
                                <div className="space-y-2">
                                  <div className="grid grid-cols-3 gap-2">
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
                                        className="min-w-0 w-full rounded-xl border border-border bg-surface-subtle px-2 py-2 text-base text-text-strong outline-none focus:border-focus-subtle md:px-3 md:text-sm"
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
                                        className="min-w-0 w-full rounded-xl border border-border bg-surface-subtle px-2 py-2 text-base text-text-strong outline-none focus:border-focus-subtle md:px-3 md:text-sm"
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
                                        className="min-w-0 w-full rounded-xl border border-border bg-surface-subtle px-2 py-2 text-base text-text-strong outline-none focus:border-focus-subtle md:px-3 md:text-sm"
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
                                      className="rounded-lg px-3 py-2 text-xs font-semibold text-accent-text transition hover:bg-surface-subtle hover:text-accent-text-hover disabled:cursor-not-allowed disabled:opacity-60"
                                    >
                                      Save
                                    </button>
                                    <button
                                      type="button"
                                      onClick={() => handleCancelEditSet(actualSet.id)}
                                      disabled={isSubmitting}
                                      className="rounded-lg px-3 py-2 text-xs font-semibold text-text-muted transition hover:bg-surface-subtle hover:text-text-primary disabled:cursor-not-allowed disabled:opacity-60"
                                    >
                                      Cancel
                                    </button>
                                    <button
                                      type="button"
                                      onClick={() => void handleDeleteActualSet(actualSet)}
                                      disabled={isSubmitting}
                                      className="rounded-lg px-3 py-2 text-xs font-semibold text-danger-action transition hover:bg-danger-surface disabled:cursor-not-allowed disabled:opacity-60 md:hidden"
                                    >
                                      Delete
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
                                        className="rounded-lg px-2 py-2 text-text-secondary transition hover:bg-surface-subtle hover:text-text-strong disabled:cursor-not-allowed disabled:opacity-60"
                                      >
                                        Edit
                                      </button>
                                      <button
                                        type="button"
                                        onClick={() => void handleDeleteActualSet(actualSet)}
                                        disabled={isSubmitting}
                                        className="rounded-lg px-2 py-2 text-text-muted transition hover:bg-danger-surface hover:text-danger-action disabled:cursor-not-allowed disabled:opacity-60"
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
                        <div className="mt-4 hidden rounded-[18px] bg-surface px-3 py-3 text-sm font-medium text-text-secondary ring-1 ring-border md:block">
                          No sets logged for this exercise yet.
                        </div>
                      ) : null}

                      {canLogWorkout && allPlannedSetsLogged ? (
                        <div className="mt-3 space-y-3">
                          <div className="hidden rounded-lg bg-positive-surface px-3 py-2 text-sm font-semibold text-positive-foreground-strong ring-1 ring-positive-surface md:block">
                            All planned sets logged
                          </div>
                          {focusedExerciseIndex >= 0 &&
                          focusedExerciseIndex < plannedExercises.length - 1 &&
                          effectiveFocusedExerciseId === exercise.id ? (
                            <button
                              type="button"
                              onClick={() =>
                                setFocusedExerciseId(
                                  plannedExercises[focusedExerciseIndex + 1].id,
                                )
                              }
                              className="min-h-11 w-full rounded-xl bg-action-primary px-4 py-3 text-sm font-semibold text-action-primary-foreground transition hover:bg-action-primary-hover md:hidden"
                            >
                              Next exercise
                            </button>
                          ) : null}
                        </div>
                      ) : canLogWorkout ? (
                        <div className="mt-3 border-t border-border-subtle pt-3 md:mt-4 md:rounded-xl md:bg-surface md:px-3 md:py-3 md:ring-1 md:ring-border">
                        <div className="hidden flex-col gap-2 md:flex md:flex-row md:items-center md:justify-between">
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
                            className="hidden rounded-xl bg-action-primary px-3 py-2 text-sm font-semibold text-action-primary-foreground transition hover:bg-action-primary-hover disabled:cursor-not-allowed disabled:opacity-60 md:block"
                          >
                            Save set
                          </button>
                        </div>

                        <div className="grid grid-cols-3 gap-2 md:mt-3">
                          <label className="min-w-0 space-y-1 text-xs text-text-body md:text-sm">
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
                              className="min-w-0 w-full rounded-xl border border-border bg-surface-subtle px-2 py-2 text-base text-text-strong outline-none ring-0 focus:border-focus-subtle md:px-3 md:text-sm"
                            />
                          </label>
                          <label className="min-w-0 space-y-1 text-xs text-text-body md:text-sm">
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
                              className="min-w-0 w-full rounded-xl border border-border bg-surface-subtle px-2 py-2 text-base text-text-strong outline-none ring-0 focus:border-focus-subtle md:px-3 md:text-sm"
                            />
                          </label>
                          <label className="min-w-0 space-y-1 text-xs text-text-body md:text-sm">
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
                              className="min-w-0 w-full rounded-xl border border-border bg-surface-subtle px-2 py-2 text-base text-text-strong outline-none ring-0 focus:border-focus-subtle md:px-3 md:text-sm"
                            />
                          </label>
                        </div>

                        <button
                          type="button"
                          onClick={() => void handleLogSet(exercise)}
                          disabled={isSubmitting}
                          className="mt-2 min-h-11 w-full rounded-xl bg-action-primary px-4 py-2.5 text-base font-semibold text-action-primary-foreground transition hover:bg-action-primary-hover disabled:cursor-not-allowed disabled:opacity-60 md:hidden"
                        >
                          Save set
                        </button>

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
                const progressionDecision =
                  progressionDecisionByExerciseKey[
                    progressionDecisionKey(
                      exercise.catalog_exercise_id,
                      exercise.name,
                    )
                  ] ??
                  progressionDecisionByExerciseKey[
                    `name:${normalizeExerciseHistoryKey(exercise.name)}`
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
                    className={`border-t border-border-subtle bg-transparent py-3 first:border-t-0 motion-safe:transition-[border-color,background-color,box-shadow] motion-safe:duration-300 md:rounded-[24px] md:border md:border-border md:bg-surface-subtle/80 md:p-4 ${
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
                        <div className="divide-y divide-border-subtle rounded-xl bg-surface/65 px-3 ring-1 ring-border">
                          <PreviousPerformanceLine history={history} />
                          {isHistoricalReadOnly === false ? (
                            <NextTargetBlock decision={progressionDecision} />
                          ) : null}
                        </div>
                      </div>
                    </div>
                  </article>
                );
              })}
            </div>
          ) : (
            <p className="text-sm leading-6 text-text-body">
              {isHistoricalReadOnly
                ? "No workout was recorded for this date."
                : "No exercise details are available for this workout yet."}
            </p>
          )}
        </div>
      </TodayCard>

    </div>
  );
}
