"use client";

import { useEffect, useState } from "react";

import { StatusPill } from "@/components/StatusPill";
import { TodayCard } from "@/components/TodayCard";
import {
  fetchRecoveryCheckIn,
  saveRecoveryCheckIn,
} from "@/lib/recoveryCheckinApi";
import { readinessStatusLabel } from "@/lib/appUiStandards";
import {
  AFFECTED_REGION_OPTIONS,
  limitationTokenLabel,
} from "@/lib/temporaryWorkoutLimitation";
import { DailyDriverReadinessSummary } from "@/types/dailyDriver";
import {
  PainArea,
  PainConcern,
  RecoveryCheckInRecord,
} from "@/types/recoveryCheckin";

interface RecoveryCheckInCardProps {
  userId: number;
  targetDate: string;
  readiness: DailyDriverReadinessSummary;
}

interface RecoveryFormState {
  bodyWeight: string;
  sleepHours: string;
  sleepQuality: number | null;
  energyLevel: number;
  sorenessLevel: number;
  stressLevel: number | null;
  trainingMotivation: number | null;
  mood: string | null;
  painConcern: PainConcern | null;
  painArea: PainArea | null;
  painOrRestrictionNote: string;
  generalNotes: string;
}

const DEFAULT_FORM_STATE: RecoveryFormState = {
  bodyWeight: "",
  sleepHours: "",
  sleepQuality: null,
  energyLevel: 5,
  sorenessLevel: 3,
  stressLevel: null,
  trainingMotivation: null,
  mood: null,
  painConcern: null,
  painArea: null,
  painOrRestrictionNote: "",
  generalNotes: "",
};

const readinessToneMap = {
  ready: "positive",
  light: "caution",
  recover: "warning",
  unknown: "neutral",
} as const;

const moodOptions = [
  { label: "Low", value: "low" },
  { label: "Steady", value: "steady" },
  { label: "Good", value: "good" },
] as const;

const sleepQualityOptions = [
  { label: "Not set", value: "" },
  { label: "1 · Poor", value: "1" },
  { label: "2 · Restless", value: "2" },
  { label: "3 · Fair", value: "3" },
  { label: "4 · Good", value: "4" },
  { label: "5 · Great", value: "5" },
] as const;

const levelOptions = [
  { label: "Not set", value: "" },
  { label: "1 · Very low", value: "1" },
  { label: "2 · Low", value: "2" },
  { label: "3 · Moderate", value: "3" },
  { label: "4 · High", value: "4" },
  { label: "5 · Very high", value: "5" },
] as const;

const painConcernOptions: { label: string; value: PainConcern }[] = [
  { label: "None", value: "none" },
  { label: "Mild / note it", value: "mild" },
  { label: "May affect training", value: "significant" },
];

const painAreaOptions: PainArea[] = [...AFFECTED_REGION_OPTIONS, "other"];

function normalizeMood(value: string | null | undefined): string | null {
  const normalizedValue = value?.trim();
  return normalizedValue || null;
}

function normalizeOptionalScale(value: number | null | undefined): number | null {
  return typeof value === "number" && value >= 1 && value <= 5 ? value : null;
}

function parseOptionalScale(value: string): number | null {
  if (!value) return null;
  const parsed = Number.parseInt(value, 10);
  return Number.isInteger(parsed) && parsed >= 1 && parsed <= 5 ? parsed : null;
}

function parseNotes(notes: string | null): Pick<
  RecoveryFormState,
  "painOrRestrictionNote" | "generalNotes"
> {
  if (!notes?.trim()) {
    return {
      painOrRestrictionNote: "",
      generalNotes: "",
    };
  }

  let painOrRestrictionNote = "";
  let generalNotes = "";
  const lines = notes.split("\n").map((line) => line.trim()).filter(Boolean);

  for (const line of lines) {
    if (line.startsWith("Pain/restriction:")) {
      painOrRestrictionNote = line.replace("Pain/restriction:", "").trim();
      continue;
    }
    if (line.startsWith("General notes:")) {
      generalNotes = line.replace("General notes:", "").trim();
      continue;
    }
  }

  if (!painOrRestrictionNote && !generalNotes) {
    generalNotes = notes.trim();
  }

  return {
    painOrRestrictionNote,
    generalNotes,
  };
}

function serializeNotes({
  painOrRestrictionNote,
  generalNotes,
}: Pick<RecoveryFormState, "painOrRestrictionNote" | "generalNotes">): string | null {
  const sections: string[] = [];
  if (painOrRestrictionNote.trim()) {
    sections.push(`Pain/restriction: ${painOrRestrictionNote.trim()}`);
  }
  if (generalNotes.trim()) {
    sections.push(`General notes: ${generalNotes.trim()}`);
  }
  return sections.length > 0 ? sections.join("\n") : null;
}

function toFormState(checkin: RecoveryCheckInRecord): RecoveryFormState {
  const parsedNotes = parseNotes(checkin.notes);

  return {
    bodyWeight:
      typeof checkin.body_weight === "number" ? String(checkin.body_weight) : "",
    sleepHours:
      typeof checkin.sleep_hours === "number" ? String(checkin.sleep_hours) : "",
    sleepQuality: normalizeOptionalScale(checkin.sleep_quality),
    energyLevel:
      typeof checkin.energy_level === "number" ? checkin.energy_level : 5,
    sorenessLevel:
      typeof checkin.soreness_level === "number" ? checkin.soreness_level : 3,
    stressLevel: normalizeOptionalScale(checkin.stress_level),
    trainingMotivation: normalizeOptionalScale(checkin.training_motivation),
    mood: normalizeMood(checkin.mood),
    painConcern: checkin.pain_concern,
    painArea: checkin.pain_area,
    painOrRestrictionNote: parsedNotes.painOrRestrictionNote,
    generalNotes: parsedNotes.generalNotes,
  };
}

export function RecoveryCheckInCard({
  userId,
  targetDate,
  readiness,
}: RecoveryCheckInCardProps) {
  const [formState, setFormState] = useState<RecoveryFormState>(DEFAULT_FORM_STATE);
  const [savedCheckIn, setSavedCheckIn] = useState<RecoveryCheckInRecord | null>(null);
  const [recentCheckIns, setRecentCheckIns] = useState<RecoveryCheckInRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  function updateFormState(
    updater: (current: RecoveryFormState) => RecoveryFormState,
  ) {
    setFormState((current) => updater(current));
    setActionMessage(null);
    setErrorMessage(null);
  }

  function handleEnergyLevelChange(nextValue: string) {
    updateFormState((current) => ({
      ...current,
      energyLevel: Number.parseInt(nextValue, 10),
    }));
  }

  function handleSorenessLevelChange(nextValue: string) {
    updateFormState((current) => ({
      ...current,
      sorenessLevel: Number.parseInt(nextValue, 10),
    }));
  }

  useEffect(() => {
    let isActive = true;

    async function loadCheckIn() {
      setIsLoading(true);
      setErrorMessage(null);

      try {
        const response = await fetchRecoveryCheckIn(userId, targetDate);
        if (!isActive) {
          return;
        }

        setSavedCheckIn(response.checkin);
        setRecentCheckIns(response.recent_checkins ?? []);
        setFormState(
          response.checkin ? toFormState(response.checkin) : { ...DEFAULT_FORM_STATE },
        );
      } catch (error) {
        if (!isActive) {
          return;
        }

        setErrorMessage(
          error instanceof Error
            ? error.message
            : "Unable to load today's recovery check-in.",
        );
      } finally {
        if (isActive) {
          setIsLoading(false);
        }
      }
    }

    void loadCheckIn();

    return () => {
      isActive = false;
    };
  }, [targetDate, userId]);

  async function handleSave() {
    const bodyWeightInput = formState.bodyWeight.trim();
    const bodyWeight =
      bodyWeightInput.length > 0 ? Number.parseFloat(bodyWeightInput) : null;
    const sleepHours = Number.parseFloat(formState.sleepHours);

    if (bodyWeightInput.length > 0 && !Number.isFinite(bodyWeight)) {
      setErrorMessage("Enter a valid body weight before saving.");
      return;
    }

    if (!Number.isFinite(sleepHours) || sleepHours <= 0) {
      setErrorMessage("Enter your sleep for last night before saving.");
      return;
    }

    setIsSaving(true);
    setErrorMessage(null);
    setActionMessage(null);

    try {
      const saveResponse = await saveRecoveryCheckIn({
        user_id: userId,
        target_date: targetDate,
        body_weight: bodyWeight,
        sleep_hours: sleepHours,
        sleep_quality: formState.sleepQuality,
        energy_level: formState.energyLevel,
        soreness_level: formState.sorenessLevel,
        stress_level: formState.stressLevel,
        training_motivation: formState.trainingMotivation,
        pain_concern: formState.painConcern,
        pain_area:
          formState.painConcern === "mild" ||
          formState.painConcern === "significant"
            ? formState.painArea
            : null,
        mood: formState.mood,
        notes: serializeNotes(formState),
      });
      const currentResponse = await fetchRecoveryCheckIn(userId, targetDate);

      setSavedCheckIn(currentResponse.checkin);
      setRecentCheckIns(currentResponse.recent_checkins ?? []);
      if (currentResponse.checkin) {
        setFormState(toFormState(currentResponse.checkin));
      }
      setActionMessage(saveResponse.message || "Check-in saved.");
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "Unable to save today's recovery check-in.",
      );
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <TodayCard title="Recovery Check-In" className="lg:col-start-2 lg:row-start-1">
      <div className="space-y-3 sm:space-y-4">
        <div className="flex items-center justify-between gap-3 rounded-2xl bg-surface-subtle px-4 py-3">
          <div>
            <p className="type-status-label uppercase tracking-[0.16em] text-text-muted">
              Readiness
            </p>
            <p className="mt-1 text-3xl font-semibold tracking-tight text-text-strong">
              {readiness.score ?? "--"}
            </p>
          </div>
          <StatusPill
            label={readinessStatusLabel(readiness.status)}
            tone={readinessToneMap[readiness.status]}
          />
        </div>

        <div className="grid grid-cols-2 gap-2 sm:gap-3">
          <label className="min-w-0 space-y-1.5 sm:space-y-2">
            <span className="text-xs font-semibold text-text-primary sm:text-sm">Body Weight</span>
            <input
              type="number"
              min="0"
              step="0.1"
              value={formState.bodyWeight}
              onChange={(event) =>
                updateFormState((current) => ({
                  ...current,
                  bodyWeight: event.target.value,
                }))
              }
              className="min-h-11 w-full min-w-0 rounded-xl border border-border bg-surface px-3 py-2 text-sm text-text-primary outline-none transition focus:border-focus sm:rounded-2xl sm:px-4 sm:py-3"
              placeholder="Optional"
            />
          </label>

          <label className="min-w-0 space-y-1.5 sm:space-y-2">
            <span className="text-xs font-semibold text-text-primary sm:text-sm">Sleep</span>
            <input
              type="number"
              min="0"
              max="24"
              step="0.5"
              value={formState.sleepHours}
              onChange={(event) =>
                updateFormState((current) => ({
                  ...current,
                  sleepHours: event.target.value,
                }))
              }
              className="min-h-11 w-full min-w-0 rounded-xl border border-border bg-surface px-3 py-2 text-sm text-text-primary outline-none transition focus:border-focus sm:rounded-2xl sm:px-4 sm:py-3"
              placeholder="Hours slept"
            />
          </label>
        </div>

        <div className="grid grid-cols-3 gap-2 sm:gap-3">
          <label className="min-w-0 space-y-1.5">
            <span className="text-xs font-semibold text-text-primary">
              Sleep quality
            </span>
            <select
              value={formState.sleepQuality ?? ""}
              onChange={(event) =>
                updateFormState((current) => ({
                  ...current,
                  sleepQuality: parseOptionalScale(event.target.value),
                }))
              }
              className="min-h-10 w-full min-w-0 rounded-xl border border-border bg-surface px-2 py-2 text-xs text-text-primary outline-none transition focus:border-focus sm:text-sm"
            >
              {sleepQualityOptions.map((option) => (
                <option key={option.value || "unset"} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <label className="min-w-0 space-y-1.5">
            <span className="text-xs font-semibold text-text-primary">Stress</span>
            <select
              value={formState.stressLevel ?? ""}
              onChange={(event) =>
                updateFormState((current) => ({
                  ...current,
                  stressLevel: parseOptionalScale(event.target.value),
                }))
              }
              className="min-h-10 w-full min-w-0 rounded-xl border border-border bg-surface px-2 py-2 text-xs text-text-primary outline-none transition focus:border-focus sm:text-sm"
            >
              {levelOptions.map((option) => (
                <option key={option.value || "unset"} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <label className="min-w-0 space-y-1.5">
            <span className="text-xs font-semibold text-text-primary">
              Motivation
            </span>
            <select
              value={formState.trainingMotivation ?? ""}
              onChange={(event) =>
                updateFormState((current) => ({
                  ...current,
                  trainingMotivation: parseOptionalScale(event.target.value),
                }))
              }
              className="min-h-10 w-full min-w-0 rounded-xl border border-border bg-surface px-2 py-2 text-xs text-text-primary outline-none transition focus:border-focus sm:text-sm"
            >
              {levelOptions.map((option) => (
                <option key={option.value || "unset"} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div className="grid grid-cols-2 gap-2 sm:gap-3">
          <label className="space-y-1.5 rounded-xl bg-surface-subtle px-3 py-2 sm:space-y-2 sm:rounded-2xl sm:px-4 sm:py-3">
            <span className="flex items-center justify-between text-sm font-semibold text-text-primary">
              Energy
              <span className="text-text-muted">{formState.energyLevel}/10</span>
            </span>
            <input
              type="range"
              min="1"
              max="10"
              step="1"
              value={formState.energyLevel}
              onChange={(event) => handleEnergyLevelChange(event.target.value)}
              onInput={(event) => handleEnergyLevelChange(event.currentTarget.value)}
              className="w-full accent-control-positive-accent"
            />
          </label>

          <label className="space-y-1.5 rounded-xl bg-surface-subtle px-3 py-2 sm:space-y-2 sm:rounded-2xl sm:px-4 sm:py-3">
            <span className="flex items-center justify-between text-sm font-semibold text-text-primary">
              Soreness
              <span className="text-text-muted">{formState.sorenessLevel}/10</span>
            </span>
            <input
              type="range"
              min="1"
              max="10"
              step="1"
              value={formState.sorenessLevel}
              onChange={(event) => handleSorenessLevelChange(event.target.value)}
              onInput={(event) => handleSorenessLevelChange(event.currentTarget.value)}
              className="w-full accent-control-caution-accent"
            />
          </label>
        </div>

        <div className="space-y-1.5 sm:space-y-2">
          <span className="text-sm font-semibold text-text-primary">Mood</span>
          <div className="grid grid-cols-3 gap-2" role="radiogroup" aria-label="Mood">
            {moodOptions.map((option) => {
              const isActive = formState.mood === option.value;
              return (
                <label key={option.value} className="cursor-pointer">
                  <input
                    type="radio"
                    name="mood"
                    value={option.value}
                    checked={isActive}
                    onChange={() =>
                      updateFormState((current) => ({
                        ...current,
                        mood: option.value,
                      }))
                    }
                    className="sr-only"
                  />
                  <span
                    aria-pressed={isActive}
                    className={`flex min-h-10 items-center justify-center rounded-full px-2 py-2 text-sm font-semibold transition ${
                      isActive
                        ? "bg-control-selected-surface text-text-inverse"
                        : "bg-surface-subtle text-text-body ring-1 ring-border hover:bg-surface-muted"
                    }`}
                  >
                    {option.label}
                  </span>
                </label>
              );
            })}
          </div>
          {formState.mood &&
          !moodOptions.some((option) => option.value === formState.mood) ? (
            <p className="text-xs text-text-muted">
              Existing mood preserved: {formState.mood}
            </p>
          ) : null}
        </div>

        <div className="space-y-2 rounded-xl border border-border px-3 py-3 sm:rounded-2xl sm:px-4">
          <div className="flex items-center justify-between gap-3">
            <span className="text-sm font-semibold text-text-primary">
              Pain or restriction concern
            </span>
            {formState.painConcern ? (
              <button
                type="button"
                onClick={() =>
                  updateFormState((current) => ({
                    ...current,
                    painConcern: null,
                    painArea: null,
                  }))
                }
                className="text-xs font-semibold text-text-muted hover:text-text-primary"
              >
                Clear
              </button>
            ) : (
              <span className="text-xs text-text-muted">Optional</span>
            )}
          </div>
          <div
            className="grid grid-cols-3 gap-2"
            role="radiogroup"
            aria-label="Pain or restriction concern"
          >
            {painConcernOptions.map((option) => {
              const isActive = formState.painConcern === option.value;
              return (
                <label key={option.value} className="cursor-pointer">
                  <input
                    type="radio"
                    name="painConcern"
                    value={option.value}
                    checked={isActive}
                    onChange={() =>
                      updateFormState((current) => ({
                        ...current,
                        painConcern: option.value,
                        painArea:
                          option.value === "none" ? null : current.painArea,
                      }))
                    }
                    className="sr-only"
                  />
                  <span
                    aria-pressed={isActive}
                    className={`flex min-h-10 items-center justify-center rounded-xl px-2 py-2 text-center text-xs font-semibold transition sm:text-sm ${
                      isActive
                        ? "bg-control-selected-surface text-text-inverse"
                        : "bg-surface-subtle text-text-body ring-1 ring-border hover:bg-surface-muted"
                    }`}
                  >
                    {option.label}
                  </span>
                </label>
              );
            })}
          </div>

          {formState.painConcern === "mild" ||
          formState.painConcern === "significant" ? (
            <div className="grid gap-2 sm:grid-cols-2">
              <label className="space-y-1.5">
                <span className="text-xs font-semibold text-text-primary">
                  Broad area
                </span>
                <select
                  value={formState.painArea ?? ""}
                  onChange={(event) =>
                    updateFormState((current) => ({
                      ...current,
                      painArea: (event.target.value || null) as PainArea | null,
                    }))
                  }
                  className="min-h-10 w-full rounded-xl border border-border bg-surface px-3 py-2 text-sm text-text-primary outline-none transition focus:border-focus"
                >
                  <option value="">Not specified</option>
                  {painAreaOptions.map((area) => (
                    <option key={area} value={area}>
                      {limitationTokenLabel(area)}
                    </option>
                  ))}
                </select>
              </label>
              <label className="space-y-1.5">
                <span className="text-xs font-semibold text-text-primary">
                  Optional context
                </span>
                <input
                  value={formState.painOrRestrictionNote}
                  onChange={(event) =>
                    updateFormState((current) => ({
                      ...current,
                      painOrRestrictionNote: event.target.value,
                    }))
                  }
                  className="min-h-10 w-full rounded-xl border border-border bg-surface px-3 py-2 text-sm text-text-primary outline-none transition focus:border-focus"
                  placeholder="Keep it brief"
                />
              </label>
            </div>
          ) : formState.painOrRestrictionNote ? (
            <p className="rounded-xl bg-surface-subtle px-3 py-2 text-xs text-text-body">
              Existing note preserved: {formState.painOrRestrictionNote}
            </p>
          ) : null}
        </div>

        <details className="rounded-xl border border-border px-3 py-2 sm:hidden">
          <summary className="cursor-pointer text-sm font-semibold text-text-primary">
            General notes
          </summary>
          <textarea
            value={formState.generalNotes}
            onChange={(event) =>
              updateFormState((current) => ({
                ...current,
                generalNotes: event.target.value,
              }))
            }
            rows={2}
            className="mt-2 w-full rounded-xl border border-border bg-surface px-3 py-2 text-sm text-text-primary outline-none transition focus:border-focus"
            placeholder="Optional"
          />
        </details>

        <label className="hidden space-y-2 sm:block">
          <span className="text-sm font-semibold text-text-primary">Notes</span>
          <textarea
            value={formState.generalNotes}
            onChange={(event) =>
              updateFormState((current) => ({
                ...current,
                generalNotes: event.target.value,
              }))
            }
            rows={3}
            className="w-full rounded-2xl border border-border bg-surface px-4 py-3 text-sm text-text-primary outline-none transition focus:border-focus"
            placeholder="Optional"
          />
        </label>

        {recentCheckIns.length > 0 ? (
          <details className="rounded-xl border border-border px-3 py-2 sm:rounded-2xl sm:px-4 sm:py-3">
            <summary className="cursor-pointer text-sm font-semibold text-text-primary">
              Recent check-ins ({recentCheckIns.length})
            </summary>
            <div className="mt-3 divide-y divide-border">
              {recentCheckIns.slice(0, 5).map((checkin) => (
                <div key={checkin.id} className="space-y-1 py-2 first:pt-0 last:pb-0">
                  <p className="text-xs font-semibold uppercase tracking-[0.12em] text-text-muted">
                    {checkin.checkin_date}
                  </p>
                  <p className="text-xs leading-5 text-text-body">
                    Sleep {checkin.sleep_hours ?? "unknown"}h
                    {checkin.sleep_quality !== null
                      ? ` · quality ${checkin.sleep_quality}/5`
                      : ""}
                    {checkin.energy_level !== null
                      ? ` · energy ${checkin.energy_level}/10`
                      : ""}
                    {checkin.soreness_level !== null
                      ? ` · soreness ${checkin.soreness_level}/10`
                      : ""}
                  </p>
                  {checkin.stress_level !== null ||
                  checkin.training_motivation !== null ||
                  checkin.pain_concern !== null ? (
                    <p className="text-xs leading-5 text-text-body">
                      {checkin.stress_level !== null
                        ? `Stress ${checkin.stress_level}/5`
                        : "Stress unknown"}
                      {checkin.training_motivation !== null
                        ? ` · motivation ${checkin.training_motivation}/5`
                        : ""}
                      {checkin.pain_concern !== null
                        ? ` · pain ${checkin.pain_concern.replace("_", " ")}`
                        : ""}
                      {checkin.pain_area
                        ? ` (${limitationTokenLabel(checkin.pain_area)})`
                        : ""}
                    </p>
                  ) : null}
                </div>
              ))}
            </div>
          </details>
        ) : null}

        {savedCheckIn ? (
          <p className="text-xs uppercase tracking-[0.16em] text-text-muted">
            Saved for {savedCheckIn.checkin_date}
          </p>
        ) : null}
        {actionMessage ? (
          <p className="text-xs font-semibold text-positive-foreground-strong">
            {actionMessage}
          </p>
        ) : null}
        {errorMessage ? (
          <p className="rounded-2xl bg-danger-surface px-4 py-3 text-sm text-danger-foreground">
            {errorMessage}
          </p>
        ) : null}

        <button
          type="button"
          onClick={() => void handleSave()}
          disabled={isLoading || isSaving}
          className="inline-flex w-full items-center justify-center rounded-xl bg-action-primary px-4 py-3 text-sm font-semibold text-action-primary-foreground transition hover:bg-action-primary-hover disabled:cursor-not-allowed disabled:opacity-60 sm:w-auto sm:rounded-2xl"
        >
          {isSaving ? "Saving..." : "Save check-in"}
        </button>
      </div>
    </TodayCard>
  );
}
