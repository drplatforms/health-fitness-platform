"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { TodayCard } from "@/components/TodayCard";
import {
  deleteCanonicalFoodLog,
  fetchCanonicalFoodServingUnits,
  fetchCanonicalFoodLogs,
  updateCanonicalFoodLog,
} from "@/lib/canonicalFoodApi";
import {
  deletePersonalFoodLog,
  fetchPersonalFoodLogs,
  updatePersonalFoodLog,
} from "@/lib/personalFoodApi";
import {
  CANONICAL_FOOD_LOGGED_EVENT,
  CanonicalFoodLoggedEntry,
  CanonicalFoodServingUnit,
} from "@/types/canonicalFood";
import {
  PERSONAL_FOOD_LOGGED_EVENT,
  PersonalFoodLoggedEntry,
} from "@/types/personalFood";

export type LoggedFoodEntry =
  | (CanonicalFoodLoggedEntry & { food_type: "canonical" })
  | PersonalFoodLoggedEntry;

interface LoggedFoodsListProps {
  initialEntries: LoggedFoodEntry[];
  initialError?: string | null;
  userId: number;
  targetDate: string;
  className?: string;
}

const mealTypeOptions = [
  { value: "breakfast", label: "Breakfast" },
  { value: "lunch", label: "Lunch" },
  { value: "dinner", label: "Dinner" },
  { value: "snack", label: "Snack" },
  { value: "other", label: "Other" },
];

function formatCompactNumber(value: number, suffix = ""): string {
  const normalized =
    Math.abs(value % 1) < 0.001 ? String(Math.round(value)) : value.toFixed(1);
  return `${normalized}${suffix}`;
}

function normalizeMealType(value: string | null): string {
  const normalized = value?.trim().toLowerCase();

  switch (normalized) {
    case "breakfast":
    case "lunch":
    case "dinner":
    case "snack":
      return normalized;
    default:
      return "other";
  }
}

function formatMealType(value: string): string {
  switch (value) {
    case "breakfast":
      return "Breakfast";
    case "lunch":
      return "Lunch";
    case "dinner":
      return "Dinner";
    case "snack":
      return "Snack";
    default:
      return "Other";
  }
}

function formatMacro(value: number | null, label: string): string {
  if (value === null) {
    return "";
  }

  return `${formatCompactNumber(value)}${label}`;
}

function formatMacroLine(entry: LoggedFoodEntry): string {
  const macroParts = [
    entry.calories === null
      ? ""
      : `${formatCompactNumber(entry.calories)} cal`,
    formatMacro(entry.protein_g, "P"),
    formatMacro(entry.carbs_g, "C"),
    formatMacro(entry.fat_g, "F"),
  ].filter(Boolean);

  return macroParts.length ? macroParts.join(" · ") : "Macros unavailable";
}

function formatLoggedAmount(entry: LoggedFoodEntry): string {
  if (entry.food_type === "canonical" && entry.serving_display) {
    return `${entry.serving_display} (${formatCompactNumber(entry.grams, "g")})`;
  }

  return formatCompactNumber(entry.grams, "g");
}

function buildPreviewEntry(
  entry: LoggedFoodEntry,
  gramsText: string,
): LoggedFoodEntry {
  const nextGrams = Number(gramsText);

  if (!Number.isFinite(nextGrams) || nextGrams <= 0 || entry.grams <= 0) {
    return entry;
  }

  const scale = nextGrams / entry.grams;
  const scaleMacro = (value: number | null) =>
    value === null ? null : Math.round(value * scale * 10) / 10;

  return {
    ...entry,
    grams: nextGrams,
    calories: scaleMacro(entry.calories),
    protein_g: scaleMacro(entry.protein_g),
    carbs_g: scaleMacro(entry.carbs_g),
    fat_g: scaleMacro(entry.fat_g),
  };
}

function groupEntriesByMeal(entries: LoggedFoodEntry[]) {
  const mealOrder = ["breakfast", "lunch", "dinner", "snack", "other"];

  return mealOrder
    .map((mealType) => ({
      mealType,
      entries: entries.filter(
        (entry) => normalizeMealType(entry.meal_type) === mealType,
      ),
    }))
    .filter((group) => group.entries.length > 0);
}

export function LoggedFoodsList({
  initialEntries,
  initialError,
  userId,
  targetDate,
  className,
}: LoggedFoodsListProps) {
  const [entries, setEntries] = useState(initialEntries);
  const [error, setError] = useState(initialError ?? null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [editingEntryId, setEditingEntryId] = useState<number | null>(null);
  const [editAmount, setEditAmount] = useState("");
  const [editUnitKey, setEditUnitKey] = useState("grams");
  const [editMealType, setEditMealType] = useState("other");
  const [servingUnitsByFoodId, setServingUnitsByFoodId] = useState<
    Record<number, CanonicalFoodServingUnit[]>
  >({});
  const [loadingServingUnitsEntryId, setLoadingServingUnitsEntryId] = useState<
    number | null
  >(null);
  const [confirmingDeleteEntryId, setConfirmingDeleteEntryId] = useState<
    number | null
  >(null);
  const [pendingEntryId, setPendingEntryId] = useState<number | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const refreshRequestIdRef = useRef(0);
  const mealGroups = groupEntriesByMeal(entries);

  const refreshLoggedFoods = useCallback(async () => {
    const requestId = refreshRequestIdRef.current + 1;
    refreshRequestIdRef.current = requestId;
    setIsRefreshing(true);
    const [canonicalResult, personalResult] = await Promise.allSettled([
      fetchCanonicalFoodLogs({ userId, date: targetDate }),
      fetchPersonalFoodLogs({ userId, date: targetDate }),
    ]);

    if (requestId !== refreshRequestIdRef.current) {
      return;
    }

    setEntries((currentEntries) => [
      ...(canonicalResult.status === "fulfilled"
        ? canonicalResult.value.entries.map((entry) => ({
            ...entry,
            food_type: "canonical" as const,
          }))
        : currentEntries.filter((entry) => entry.food_type === "canonical")),
      ...(personalResult.status === "fulfilled"
        ? personalResult.value.entries
        : currentEntries.filter((entry) => entry.food_type === "personal")),
    ]);
    setError(
      canonicalResult.status === "rejected" &&
        personalResult.status === "rejected"
        ? "Logged foods are unavailable right now."
        : canonicalResult.status === "rejected" ||
            personalResult.status === "rejected"
          ? "Some logged foods are unavailable right now."
          : null,
    );
    setIsRefreshing(false);
  }, [targetDate, userId]);

  useEffect(() => {
    window.addEventListener(CANONICAL_FOOD_LOGGED_EVENT, refreshLoggedFoods);
    window.addEventListener(PERSONAL_FOOD_LOGGED_EVENT, refreshLoggedFoods);

    return () => {
      window.removeEventListener(CANONICAL_FOOD_LOGGED_EVENT, refreshLoggedFoods);
      window.removeEventListener(PERSONAL_FOOD_LOGGED_EVENT, refreshLoggedFoods);
    };
  }, [refreshLoggedFoods]);

  function startEditing(entry: LoggedFoodEntry) {
    setActionError(null);
    setConfirmingDeleteEntryId(null);
    setEditingEntryId(entry.entry_id);
    setEditAmount(
      entry.food_type === "canonical" &&
        entry.serving_unit_id &&
        entry.serving_quantity !== undefined
        ? formatCompactNumber(entry.serving_quantity)
        : formatCompactNumber(entry.grams),
    );
    setEditUnitKey(
      entry.food_type === "canonical" && entry.serving_unit_id !== undefined
        ? String(entry.serving_unit_id)
        : "grams",
    );
    setEditMealType(normalizeMealType(entry.meal_type));
    void loadServingUnitsForEntry(entry);
  }

  function cancelEditing() {
    setEditingEntryId(null);
    setEditAmount("");
    setEditUnitKey("grams");
    setEditMealType("other");
    setActionError(null);
  }

  async function loadServingUnitsForEntry(entry: LoggedFoodEntry) {
    if (entry.food_type === "personal") {
      return;
    }
    if (servingUnitsByFoodId[entry.canonical_food_id] !== undefined) {
      return;
    }

    setLoadingServingUnitsEntryId(entry.entry_id);
    try {
      const response = await fetchCanonicalFoodServingUnits(
        entry.canonical_food_id,
      );
      setServingUnitsByFoodId((current) => ({
        ...current,
        [entry.canonical_food_id]: response.serving_units,
      }));
    } catch {
      setServingUnitsByFoodId((current) => ({
        ...current,
        [entry.canonical_food_id]: [],
      }));
    } finally {
      setLoadingServingUnitsEntryId((currentEntryId) =>
        currentEntryId === entry.entry_id ? null : currentEntryId,
      );
    }
  }

  async function saveEntry(entry: LoggedFoodEntry) {
    const amount = Number(editAmount);
    const servingUnits =
      entry.food_type === "canonical"
        ? (servingUnitsByFoodId[entry.canonical_food_id] ?? [])
        : [];
    const selectedServingUnit =
      editUnitKey === "grams" || editUnitKey === "personal-serving"
        ? null
        : (servingUnits.find(
            (unit) => String(unit.serving_unit_id) === editUnitKey,
          ) ?? null);

    if (!Number.isFinite(amount) || amount <= 0) {
      setActionError("Amount must be greater than 0.");
      return;
    }
    const usesPersonalServing =
      entry.food_type === "personal" && editUnitKey === "personal-serving";
    if (
      editUnitKey !== "grams" &&
      !usesPersonalServing &&
      selectedServingUnit === null
    ) {
      setActionError("Serving unit is still loading. Try again in a moment.");
      return;
    }
    if (usesPersonalServing && entry.serving_grams === null) {
      setActionError("This logged revision has no saved serving size.");
      return;
    }
    const resolvedGrams = selectedServingUnit
      ? amount * selectedServingUnit.grams_per_unit
      : usesPersonalServing
        ? amount * (entry.serving_grams as number)
        : amount;
    if (!Number.isFinite(resolvedGrams) || resolvedGrams <= 0 || resolvedGrams > 5_000) {
      setActionError("Resolved amount must be greater than 0 and no more than 5,000g.");
      return;
    }

    setPendingEntryId(entry.entry_id);
    setActionError(null);
    try {
      let responseEntry: LoggedFoodEntry;
      if (entry.food_type === "personal") {
        responseEntry = (
          await updatePersonalFoodLog({
            user_id: userId,
            entry_id: entry.entry_id,
            ...(usesPersonalServing
              ? { serving_quantity: amount }
              : { grams: amount }),
            meal_type: editMealType,
            entry_date: targetDate,
          })
        ).entry;
      } else {
        const canonicalEntry = (
          await updateCanonicalFoodLog({
            user_id: userId,
            entry_id: entry.entry_id,
            ...(selectedServingUnit
              ? {
                  serving_unit_id: selectedServingUnit.serving_unit_id,
                  quantity: amount,
                }
              : { grams: amount }),
            meal_type: editMealType,
            entry_date: targetDate,
          })
        ).entry;
        responseEntry = { ...canonicalEntry, food_type: "canonical" };
      }
      setEntries((currentEntries) =>
        currentEntries.map((currentEntry) =>
          currentEntry.entry_id === entry.entry_id
            ? responseEntry
            : currentEntry,
        ),
      );
      setEditingEntryId(null);
      setEditAmount("");
      setEditUnitKey("grams");
      setEditMealType("other");
      window.dispatchEvent(
        new Event(
          entry.food_type === "personal"
            ? PERSONAL_FOOD_LOGGED_EVENT
            : CANONICAL_FOOD_LOGGED_EVENT,
        ),
      );
    } catch (saveError) {
      setActionError(
        saveError instanceof Error
          ? saveError.message
          : "Unable to update this food right now.",
      );
    } finally {
      setPendingEntryId(null);
    }
  }

  async function deleteEntry(entry: LoggedFoodEntry) {
    if (confirmingDeleteEntryId !== entry.entry_id) {
      setActionError(null);
      setEditingEntryId(null);
      setConfirmingDeleteEntryId(entry.entry_id);
      return;
    }

    setPendingEntryId(entry.entry_id);
    setActionError(null);
    try {
      if (entry.food_type === "personal") {
        await deletePersonalFoodLog({
          userId,
          entryId: entry.entry_id,
          date: targetDate,
        });
      } else {
        await deleteCanonicalFoodLog({
          user_id: userId,
          entry_id: entry.entry_id,
          entry_date: targetDate,
        });
      }
      setEntries((currentEntries) =>
        currentEntries.filter(
          (currentEntry) => currentEntry.entry_id !== entry.entry_id,
        ),
      );
      setConfirmingDeleteEntryId(null);
      window.dispatchEvent(
        new Event(
          entry.food_type === "personal"
            ? PERSONAL_FOOD_LOGGED_EVENT
            : CANONICAL_FOOD_LOGGED_EVENT,
        ),
      );
    } catch (deleteError) {
      setActionError(
        deleteError instanceof Error
          ? deleteError.message
          : "Unable to delete this food right now.",
      );
    } finally {
      setPendingEntryId(null);
    }
  }

  return (
    <TodayCard title="Logged today" className={className}>
      <div className="space-y-2">
        {isRefreshing ? (
          <p className="rounded-2xl bg-surface-subtle px-4 py-3 text-sm text-text-body">
            Updating logged foods...
          </p>
        ) : null}

        {error ? (
          <p className="rounded-2xl bg-surface-subtle px-4 py-3 text-sm text-text-body">
            {error}
          </p>
        ) : null}

        {actionError ? (
          <p className="rounded-2xl bg-danger-surface px-4 py-3 text-sm font-medium text-danger-foreground">
            {actionError}
          </p>
        ) : null}

        {!error && entries.length === 0 ? (
          <p className="rounded-2xl bg-surface-subtle px-4 py-3 text-sm text-text-body">
            No foods logged yet today.
          </p>
        ) : null}

        {entries.length > 0 ? (
          <div className="max-h-[18rem] space-y-2 overflow-y-auto rounded-2xl bg-surface-subtle px-2 py-2 sm:max-h-[26rem] sm:px-3 sm:py-3">
            {mealGroups.map((group) => (
              <section key={group.mealType} className="space-y-1.5">
                <div className="flex items-center justify-between gap-2 px-1">
                  <h3 className="text-xs font-semibold uppercase tracking-[0.16em] text-text-muted">
                    {formatMealType(group.mealType)}
                  </h3>
                  <span className="text-xs font-medium text-text-muted">
                    {group.entries.length}{" "}
                    {group.entries.length === 1 ? "item" : "items"}
                  </span>
                </div>
                <div className="divide-y divide-border-subtle rounded-xl bg-surface">
                  {group.entries.map((entry) => (
                    <div
                      key={entry.entry_id}
                      className="px-3 py-2 text-sm"
                    >
                      {editingEntryId === entry.entry_id ? (
                        <div className="space-y-2">
                          <p className="font-semibold text-text-strong">
                            {entry.food_name}
                          </p>
                          <div className="grid gap-2 sm:grid-cols-[minmax(0,0.65fr)_minmax(0,0.75fr)_auto] sm:items-end">
                            <label className="space-y-1 text-xs font-medium text-text-secondary">
                              <span>Amount</span>
                              <div className="grid gap-2 sm:grid-cols-[minmax(0,0.65fr)_minmax(0,1fr)]">
                                <input
                                  type="number"
                                  min="0"
                                  step={editUnitKey === "grams" ? "1" : "0.25"}
                                  value={editAmount}
                                  onChange={(event) =>
                                    setEditAmount(event.target.value)
                                  }
                                  className="min-w-0 flex-1 rounded-xl border border-border bg-surface-subtle px-3 py-2 text-sm font-semibold text-text-strong outline-none focus:border-focus-subtle"
                                />
                                <select
                                  value={editUnitKey}
                                  disabled={
                                    loadingServingUnitsEntryId === entry.entry_id
                                  }
                                  onChange={(event) => {
                                    const nextUnitKey = event.target.value;
                                    setEditUnitKey(nextUnitKey);
                                    setEditAmount(
                                      nextUnitKey === "grams"
                                        ? formatCompactNumber(entry.grams)
                                        : "1",
                                    );
                                  }}
                                  className="w-full rounded-xl border border-border bg-surface-subtle px-3 py-2 text-sm font-semibold text-text-strong outline-none focus:border-focus-subtle disabled:opacity-70"
                                >
                                  <option value="grams">grams</option>
                                  {entry.food_type === "personal" &&
                                  entry.serving_grams !== null ? (
                                    <option value="personal-serving">
                                      {entry.serving_name || "serving"}
                                    </option>
                                  ) : null}
                                  {entry.food_type === "canonical" &&
                                  editUnitKey !== "grams" &&
                                  entry.serving_display &&
                                  !(servingUnitsByFoodId[
                                    entry.canonical_food_id
                                  ] ?? []).some(
                                    (unit) =>
                                      String(unit.serving_unit_id) === editUnitKey,
                                  ) ? (
                                    <option value={editUnitKey}>
                                      {entry.serving_display}
                                    </option>
                                  ) : null}
                                  {entry.food_type === "canonical"
                                    ? (
                                        servingUnitsByFoodId[
                                          entry.canonical_food_id
                                        ] ?? []
                                      ).map((unit) => (
                                        <option
                                          key={unit.serving_unit_id}
                                          value={String(unit.serving_unit_id)}
                                        >
                                          {unit.display_label}
                                        </option>
                                      ))
                                    : null}
                                </select>
                              </div>
                            </label>
                            <label className="space-y-1 text-xs font-medium text-text-secondary">
                              <span>Meal</span>
                              <select
                                value={editMealType}
                                onChange={(event) =>
                                  setEditMealType(event.target.value)
                                }
                                className="w-full rounded-xl border border-border bg-surface-subtle px-3 py-2 text-sm font-semibold text-text-strong outline-none focus:border-focus-subtle"
                              >
                                {mealTypeOptions.map((option) => (
                                  <option key={option.value} value={option.value}>
                                    {option.label}
                                  </option>
                                ))}
                              </select>
                            </label>
                            <div className="flex gap-2">
                              <button
                                type="button"
                                onClick={() => void saveEntry(entry)}
                                disabled={pendingEntryId === entry.entry_id}
                                className="rounded-xl bg-action-primary px-3 py-2 text-xs font-semibold text-action-primary-foreground transition hover:bg-action-primary-hover disabled:cursor-not-allowed disabled:opacity-60"
                              >
                                Save
                              </button>
                              <button
                                type="button"
                                onClick={cancelEditing}
                                disabled={pendingEntryId === entry.entry_id}
                                className="rounded-xl bg-surface-muted px-3 py-2 text-xs font-semibold text-text-body transition hover:bg-surface-interactive-hover disabled:cursor-not-allowed disabled:opacity-60"
                              >
                                Cancel
                              </button>
                            </div>
                          </div>
                          <p className="text-xs font-medium text-text-secondary">
                            {(() => {
                              const amount = Number(editAmount);
                              const servingUnits =
                                entry.food_type === "canonical"
                                  ? (servingUnitsByFoodId[
                                      entry.canonical_food_id
                                    ] ?? [])
                                  : [];
                              const selectedServingUnit =
                                editUnitKey === "grams" ||
                                editUnitKey === "personal-serving"
                                  ? null
                                  : (servingUnits.find(
                                      (unit) =>
                                        String(unit.serving_unit_id) ===
                                        editUnitKey,
                                    ) ?? null);
                              const resolvedGrams = selectedServingUnit
                                ? amount * selectedServingUnit.grams_per_unit
                                : entry.food_type === "personal" &&
                                    editUnitKey === "personal-serving" &&
                                    entry.serving_grams !== null
                                  ? amount * entry.serving_grams
                                  : amount;

                              return Number.isFinite(resolvedGrams) &&
                                resolvedGrams > 0 ? (
                                <>
                                  Resolved:{" "}
                                  {formatCompactNumber(resolvedGrams, "g")} ·
                                  Preview:{" "}
                                  {formatMacroLine(
                                    buildPreviewEntry(
                                      entry,
                                      String(resolvedGrams),
                                    ),
                                  )}
                                </>
                              ) : (
                                <>Preview: {formatMacroLine(entry)}</>
                              );
                            })()}
                          </p>
                        </div>
                      ) : (
                        <div className="grid grid-cols-[minmax(0,1fr)_auto_auto] items-baseline gap-x-2 gap-y-0.5">
                          <span className="font-semibold text-text-strong">
                            {entry.food_name}
                          </span>
                          <span className="text-right text-text-secondary">
                            {formatLoggedAmount(entry)}
                          </span>
                          <div className="flex gap-2 text-xs font-semibold">
                            <button
                              type="button"
                              onClick={() => startEditing(entry)}
                              disabled={pendingEntryId === entry.entry_id}
                              className="text-accent-text transition hover:text-accent-text-hover disabled:cursor-not-allowed disabled:opacity-60"
                            >
                              Edit
                            </button>
                            <button
                              type="button"
                              onClick={() => void deleteEntry(entry)}
                              disabled={pendingEntryId === entry.entry_id}
                              className={
                                confirmingDeleteEntryId === entry.entry_id
                                  ? "text-danger-action transition hover:text-danger-action-hover disabled:cursor-not-allowed disabled:opacity-60"
                                  : "text-text-muted transition hover:text-danger-action disabled:cursor-not-allowed disabled:opacity-60"
                              }
                            >
                              {confirmingDeleteEntryId === entry.entry_id
                                ? "Confirm delete"
                                : "Delete"}
                            </button>
                            {confirmingDeleteEntryId === entry.entry_id ? (
                              <button
                                type="button"
                                onClick={() => setConfirmingDeleteEntryId(null)}
                                disabled={pendingEntryId === entry.entry_id}
                                className="text-text-muted transition hover:text-text-body disabled:cursor-not-allowed disabled:opacity-60"
                              >
                                Cancel
                              </button>
                            ) : null}
                          </div>
                          <span className="hidden text-xs font-medium text-text-secondary sm:col-span-3 sm:block">
                            {formatMacroLine(entry)}
                          </span>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </section>
            ))}
          </div>
        ) : null}
      </div>
    </TodayCard>
  );
}
