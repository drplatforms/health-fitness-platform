"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import {
  AFFECTED_REGION_OPTIONS,
  clearTemporaryWorkoutLimitation,
  computeLimitationExpiresAt,
  fetchLimitationExerciseCatalog,
  fetchTemporaryWorkoutLimitation,
  limitationSummary,
  limitationTokenLabel,
  saveTemporaryWorkoutLimitation,
  type LimitationCatalogExercise,
  type TemporaryWorkoutLimitationResponse,
} from "@/lib/temporaryWorkoutLimitation";

interface Props {
  className?: string;
  userId: number;
  refreshVersion?: number;
  onChanged: () => void;
}

type DurationChoice =
  | "until_cleared"
  | "3_days"
  | "7_days"
  | "14_days"
  | "existing";

function toggleValue<T>(values: T[], value: T): T[] {
  return values.includes(value)
    ? values.filter((item) => item !== value)
    : [...values, value];
}

export function TemporaryWorkoutLimitationCard({
  className = "",
  userId,
  refreshVersion = 0,
  onChanged,
}: Props) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const [state, setState] = useState<TemporaryWorkoutLimitationResponse | null>(null);
  const [catalog, setCatalog] = useState<LimitationCatalogExercise[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [affectedRegions, setAffectedRegions] = useState<string[]>([]);
  const [restrictedMovements, setRestrictedMovements] = useState<string[]>([]);
  const [excludedIds, setExcludedIds] = useState<number[]>([]);
  const [duration, setDuration] = useState<DurationChoice>("until_cleared");
  const [search, setSearch] = useState("");

  useEffect(() => {
    let cancelled = false;
    void fetchTemporaryWorkoutLimitation(userId)
      .then((next) => {
        if (!cancelled) {
          setState(next);
          setError(null);
        }
      })
      .catch((requestError: unknown) => {
        if (!cancelled) {
          setError(
            requestError instanceof Error ? requestError.message : "Unable to load.",
          );
        }
      })
      .finally(() => {
        if (!cancelled) {
          setIsLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [refreshVersion, userId]);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) {
      return;
    }
    if (isEditing && !dialog.open) {
      dialog.showModal();
    } else if (!isEditing && dialog.open) {
      dialog.close();
    }
  }, [isEditing]);

  const movementOptions = useMemo(
    () =>
      Array.from(new Set(catalog.map((exercise) => exercise.movement_pattern))).sort(),
    [catalog],
  );
  const selectedExercises = useMemo(
    () => catalog.filter((exercise) => excludedIds.includes(exercise.id)),
    [catalog, excludedIds],
  );
  const searchResults = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (query.length < 2) return [];
    return catalog
      .filter(
        (exercise) =>
          !excludedIds.includes(exercise.id) &&
          exercise.name.toLowerCase().includes(query),
      )
      .slice(0, 8);
  }, [catalog, excludedIds, search]);

  async function openEditor() {
    setError(null);
    try {
      const exercises = catalog.length ? catalog : await fetchLimitationExerciseCatalog();
      setCatalog(exercises);
      const limitation = state?.limitation;
      setAffectedRegions(limitation?.affected_regions ?? []);
      setRestrictedMovements(limitation?.restricted_movement_patterns ?? []);
      setExcludedIds(limitation?.excluded_catalog_exercise_ids ?? []);
      setDuration(limitation?.expires_at ? "existing" : "until_cleared");
      setSearch("");
      setIsEditing(true);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to edit.");
    }
  }

  async function handleSave() {
    setIsSaving(true);
    setError(null);
    try {
      const next = await saveTemporaryWorkoutLimitation(userId, {
        affected_regions: affectedRegions,
        restricted_movement_patterns: restrictedMovements,
        excluded_catalog_exercise_ids: excludedIds,
        expires_at: computeLimitationExpiresAt(
          duration,
          state?.limitation?.expires_at ?? null,
        ),
      });
      setState(next);
      setIsEditing(false);
      onChanged();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to save.");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleClear() {
    setIsSaving(true);
    setError(null);
    try {
      const next = await clearTemporaryWorkoutLimitation(userId);
      setState(next);
      setIsEditing(false);
      onChanged();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to clear.");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <>
      <section
        className={`min-w-0 rounded-xl bg-surface-subtle px-3 py-2 ring-1 ring-border ${className}`}
      >
        <div className="flex min-w-0 items-center justify-between gap-2">
          <div className="min-w-0">
            <p className="type-field-label text-text-strong">
              Temporary limitation
            </p>
            <p className="type-compact-metadata truncate text-text-body">
              {isLoading
                ? "Loading…"
                : state?.active && state.limitation
                  ? limitationSummary(state.limitation)
                  : "None active"}
            </p>
          </div>
          <button
            type="button"
            onClick={() => void openEditor()}
            className="type-button shrink-0 rounded-lg bg-surface px-3 py-1.5 text-text-body ring-1 ring-border hover:bg-surface-highlighted"
          >
            Edit
          </button>
        </div>

        {state?.current_plan_conflicts.length ? (
          <p
            role="status"
            className="type-feedback mt-2 rounded-lg bg-warning-surface px-2.5 py-2 font-medium text-warning-foreground"
          >
            This workout includes {state.current_plan_conflicts.length} exercise
            {state.current_plan_conflicts.length === 1 ? "" : "s"} that{" "}
            {state.current_plan_conflicts.length === 1 ? "is" : "are"} now
            temporarily restricted.
          </p>
        ) : null}

        {!isEditing && error ? (
          <p
            role="alert"
            className="type-feedback mt-2 font-medium text-danger-foreground"
          >
            {error}
          </p>
        ) : null}
      </section>

      <dialog
        ref={dialogRef}
        aria-labelledby="temporary-limitation-dialog-title"
        onCancel={(event) => {
          if (isSaving) {
            event.preventDefault();
          } else {
            setIsEditing(false);
          }
        }}
        onClose={() => setIsEditing(false)}
        className="m-auto max-h-[calc(100dvh-2rem)] w-[min(42rem,calc(100vw-2rem))] overflow-y-auto rounded-2xl border border-border bg-surface p-0 text-text-strong shadow-2xl backdrop:bg-modal-backdrop"
      >
        <div className="p-4 sm:p-5">
          <div className="flex items-start justify-between gap-3">
            <div>
              <h2
                id="temporary-limitation-dialog-title"
                className="type-section-title text-text-strong"
              >
                Temporary limitation
              </h2>
              <p className="type-body mt-1 text-text-body">
                Only selected movements and exercises are blocked.
              </p>
            </div>
            <button
              type="button"
              onClick={() => setIsEditing(false)}
              disabled={isSaving}
              aria-label="Close temporary limitation editor"
              className="type-button rounded-lg px-3 py-2 text-text-body hover:bg-surface-muted disabled:opacity-50"
            >
              Close
            </button>
          </div>

          <div className="mt-5 space-y-4">
            {error ? (
              <p
                role="alert"
                className="type-feedback rounded-xl bg-danger-surface px-3 py-2 font-medium text-danger-foreground"
              >
                {error}
              </p>
            ) : null}

            <fieldset>
              <legend className="type-field-label text-text-strong">
                Affected area (optional)
              </legend>
              <div className="mt-2 flex flex-wrap gap-2">
                {AFFECTED_REGION_OPTIONS.map((region) => (
                  <label
                    key={region}
                    className="type-compact-metadata flex items-center gap-1.5 rounded-lg bg-surface px-2 py-1.5 text-text-body ring-1 ring-border"
                  >
                    <input
                      type="checkbox"
                      checked={affectedRegions.includes(region)}
                      onChange={() =>
                        setAffectedRegions(toggleValue(affectedRegions, region))
                      }
                    />
                    {limitationTokenLabel(region)}
                  </label>
                ))}
              </div>
            </fieldset>

            <fieldset>
              <legend className="type-field-label text-text-strong">
                Avoid movements
              </legend>
              <div className="mt-2 flex max-h-32 flex-wrap gap-2 overflow-y-auto p-0.5">
                {movementOptions.map((movement) => (
                  <label
                    key={movement}
                    className="type-compact-metadata flex items-center gap-1.5 rounded-lg bg-surface px-2 py-1.5 text-text-body ring-1 ring-border"
                  >
                    <input
                      type="checkbox"
                      checked={restrictedMovements.includes(movement)}
                      onChange={() =>
                        setRestrictedMovements(
                          toggleValue(restrictedMovements, movement),
                        )
                      }
                    />
                    {limitationTokenLabel(movement)}
                  </label>
                ))}
              </div>
            </fieldset>

            <div>
              <label
                htmlFor="temporary-limitation-exercise-search"
                className="type-field-label text-text-strong"
              >
                Avoid specific exercises
              </label>
              <input
                id="temporary-limitation-exercise-search"
                type="search"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Search exercise catalog"
                className="mt-2 w-full rounded-lg bg-surface px-3 py-2 text-sm text-text-strong ring-1 ring-border outline-none focus:ring-2 focus:ring-action-primary"
              />
              {searchResults.length ? (
                <div
                  className="mt-2 grid gap-1"
                  role="list"
                  aria-label="Exercise search results"
                >
                  {searchResults.map((exercise) => (
                    <button
                      key={exercise.id}
                      type="button"
                      onClick={() => {
                        setExcludedIds([...excludedIds, exercise.id]);
                        setSearch("");
                      }}
                      className="type-body rounded-lg bg-surface px-3 py-2 text-left text-text-body ring-1 ring-border hover:bg-surface-highlighted"
                    >
                      {exercise.name}
                    </button>
                  ))}
                </div>
              ) : null}
              {selectedExercises.length ? (
                <div className="mt-2 flex flex-wrap gap-2">
                  {selectedExercises.map((exercise) => (
                    <button
                      key={exercise.id}
                      type="button"
                      aria-label={`Remove ${exercise.name} from avoided exercises`}
                      onClick={() =>
                        setExcludedIds(
                          excludedIds.filter((id) => id !== exercise.id),
                        )
                      }
                      className="type-compact-metadata rounded-full bg-surface px-2.5 py-1 text-text-body ring-1 ring-border"
                    >
                      {exercise.name} ×
                    </button>
                  ))}
                </div>
              ) : null}
            </div>

            <label className="type-field-label block text-text-strong">
              Duration
              <select
                value={duration}
                onChange={(event) =>
                  setDuration(event.target.value as DurationChoice)
                }
                className="mt-2 w-full rounded-lg bg-surface px-3 py-2 text-sm font-normal text-text-strong ring-1 ring-border"
              >
                {state?.limitation?.expires_at ? (
                  <option value="existing">Keep current end date</option>
                ) : null}
                <option value="until_cleared">Until I clear it</option>
                <option value="3_days">3 days</option>
                <option value="7_days">1 week</option>
                <option value="14_days">2 weeks</option>
              </select>
            </label>

            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => void handleSave()}
                disabled={
                  isSaving ||
                  (!restrictedMovements.length && !excludedIds.length)
                }
                className="type-button rounded-lg bg-action-primary px-3 py-2 text-action-primary-foreground disabled:opacity-50"
              >
                {isSaving ? "Saving…" : "Save"}
              </button>
              <button
                type="button"
                onClick={() => setIsEditing(false)}
                disabled={isSaving}
                className="type-button rounded-lg px-3 py-2 text-text-body hover:bg-surface-highlighted"
              >
                Cancel
              </button>
              {state?.active ? (
                <button
                  type="button"
                  onClick={() => void handleClear()}
                  disabled={isSaving}
                  className="type-button rounded-lg px-3 py-2 text-text-body hover:bg-surface-highlighted"
                >
                  Clear limitation
                </button>
              ) : null}
            </div>
          </div>
        </div>
      </dialog>
    </>
  );
}
