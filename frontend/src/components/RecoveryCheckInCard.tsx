"use client";

import { useEffect, useState } from "react";

import { StatusPill } from "@/components/StatusPill";
import { TodayCard } from "@/components/TodayCard";
import {
  fetchRecoveryCheckIn,
  saveRecoveryCheckIn,
} from "@/lib/recoveryCheckinApi";
import { DailyDriverReadinessSummary } from "@/types/dailyDriver";
import { RecoveryCheckInRecord } from "@/types/recoveryCheckin";

interface RecoveryCheckInCardProps {
  userId: number;
  targetDate: string;
  readiness: DailyDriverReadinessSummary;
}

interface RecoveryFormState {
  sleepHours: string;
  energyLevel: number;
  sorenessLevel: number;
  stressLevel: string;
  painOrRestrictionNote: string;
  generalNotes: string;
}

const DEFAULT_FORM_STATE: RecoveryFormState = {
  sleepHours: "",
  energyLevel: 5,
  sorenessLevel: 3,
  stressLevel: "managed",
  painOrRestrictionNote: "",
  generalNotes: "",
};

const readinessToneMap = {
  ready: "positive",
  light: "caution",
  recover: "warning",
  unknown: "neutral",
} as const;

const stressOptions = [
  { label: "Low", value: "low" },
  { label: "Managed", value: "managed" },
  { label: "High", value: "high" },
];

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
    sleepHours:
      typeof checkin.sleep_hours === "number" ? String(checkin.sleep_hours) : "",
    energyLevel:
      typeof checkin.energy_level === "number" ? checkin.energy_level : 5,
    sorenessLevel:
      typeof checkin.soreness_level === "number" ? checkin.soreness_level : 3,
    stressLevel: checkin.mood?.trim() || "managed",
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
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

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
        setFormState(response.checkin ? toFormState(response.checkin) : DEFAULT_FORM_STATE);
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
    const sleepHours = Number.parseFloat(formState.sleepHours);
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
        sleep_hours: sleepHours,
        energy_level: formState.energyLevel,
        soreness_level: formState.sorenessLevel,
        mood: formState.stressLevel,
        notes: serializeNotes(formState),
      });
      const currentResponse = await fetchRecoveryCheckIn(userId, targetDate);

      setSavedCheckIn(currentResponse.checkin);
      if (currentResponse.checkin) {
        setFormState(toFormState(currentResponse.checkin));
      }
      setActionMessage(saveResponse.message);
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
    <TodayCard
      title="Recovery Check-In"
      eyebrow="Daily Driver"
      className="lg:col-start-2 lg:row-start-1"
    >
      <div className="space-y-4">
        <div className="grid gap-3 sm:grid-cols-[auto_1fr] sm:items-start">
          <div className="rounded-2xl bg-slate-50 px-4 py-3">
            <p className="text-[0.68rem] font-semibold uppercase tracking-[0.16em] text-slate-500">
              Readiness
            </p>
            <p className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">
              {readiness.score ?? "--"}
            </p>
          </div>
          <div className="space-y-2">
            <StatusPill
              label={readiness.status.replace("_", " ")}
              tone={readinessToneMap[readiness.status]}
            />
            <p className="text-lg font-semibold text-slate-950">
              {readiness.headline}
            </p>
            <p className="text-sm leading-6 text-slate-700">{readiness.reason}</p>
          </div>
        </div>

        <div className="grid gap-3 sm:grid-cols-2">
          <label className="space-y-2">
            <span className="text-sm font-semibold text-slate-900">Sleep</span>
            <input
              type="number"
              min="0"
              max="24"
              step="0.5"
              value={formState.sleepHours}
              onChange={(event) =>
                setFormState((current) => ({
                  ...current,
                  sleepHours: event.target.value,
                }))
              }
              className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-emerald-500"
              placeholder="Hours slept"
            />
          </label>

          <div className="space-y-2">
            <span className="text-sm font-semibold text-slate-900">Stress / fatigue</span>
            <div className="flex flex-wrap gap-2">
              {stressOptions.map((option) => {
                const isActive = formState.stressLevel === option.value;
                return (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() =>
                      setFormState((current) => ({
                        ...current,
                        stressLevel: option.value,
                      }))
                    }
                    className={`rounded-full px-4 py-2 text-sm font-semibold transition ${
                      isActive
                        ? "bg-slate-950 text-white"
                        : "bg-slate-50 text-slate-700 ring-1 ring-slate-200 hover:bg-slate-100"
                    }`}
                  >
                    {option.label}
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        <div className="grid gap-3 sm:grid-cols-2">
          <label className="space-y-2 rounded-2xl bg-slate-50 px-4 py-3">
            <span className="flex items-center justify-between text-sm font-semibold text-slate-900">
              Energy
              <span className="text-slate-500">{formState.energyLevel}/10</span>
            </span>
            <input
              type="range"
              min="1"
              max="10"
              step="1"
              value={formState.energyLevel}
              onChange={(event) =>
                setFormState((current) => ({
                  ...current,
                  energyLevel: Number.parseInt(event.target.value, 10),
                }))
              }
              className="w-full accent-emerald-700"
            />
          </label>

          <label className="space-y-2 rounded-2xl bg-slate-50 px-4 py-3">
            <span className="flex items-center justify-between text-sm font-semibold text-slate-900">
              Soreness
              <span className="text-slate-500">{formState.sorenessLevel}/10</span>
            </span>
            <input
              type="range"
              min="1"
              max="10"
              step="1"
              value={formState.sorenessLevel}
              onChange={(event) =>
                setFormState((current) => ({
                  ...current,
                  sorenessLevel: Number.parseInt(event.target.value, 10),
                }))
              }
              className="w-full accent-amber-600"
            />
          </label>
        </div>

        <label className="space-y-2">
          <span className="text-sm font-semibold text-slate-900">
            Anything hurt or restricted?
          </span>
          <textarea
            value={formState.painOrRestrictionNote}
            onChange={(event) =>
              setFormState((current) => ({
                ...current,
                painOrRestrictionNote: event.target.value,
              }))
            }
            rows={2}
            className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-emerald-500"
            placeholder="Optional"
          />
        </label>

        <label className="space-y-2">
          <span className="text-sm font-semibold text-slate-900">Notes</span>
          <textarea
            value={formState.generalNotes}
            onChange={(event) =>
              setFormState((current) => ({
                ...current,
                generalNotes: event.target.value,
              }))
            }
            rows={3}
            className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-emerald-500"
            placeholder="Optional"
          />
        </label>

        {savedCheckIn ? (
          <p className="text-xs uppercase tracking-[0.16em] text-slate-500">
            Saved for {savedCheckIn.checkin_date}
          </p>
        ) : null}
        {actionMessage ? (
          <p className="rounded-2xl bg-emerald-50 px-4 py-3 text-sm text-emerald-900">
            {actionMessage}
          </p>
        ) : null}
        {errorMessage ? (
          <p className="rounded-2xl bg-rose-50 px-4 py-3 text-sm text-rose-900">
            {errorMessage}
          </p>
        ) : null}

        <button
          type="button"
          onClick={() => void handleSave()}
          disabled={isLoading || isSaving}
          className="inline-flex rounded-2xl bg-emerald-900 px-4 py-3 text-sm font-semibold text-emerald-50 transition hover:bg-emerald-800 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isSaving ? "Saving..." : "Save check-in"}
        </button>
      </div>
    </TodayCard>
  );
}
