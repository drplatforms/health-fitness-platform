"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { TodayCard } from "@/components/TodayCard";
import {
  deleteCanonicalFoodLog,
  fetchCanonicalFoodServingUnits,
  fetchCanonicalFoodLogs,
  updateCanonicalFoodLog,
} from "@/lib/canonicalFoodApi";
import {
  CANONICAL_FOOD_LOGGED_EVENT,
  CanonicalFoodLoggedEntry,
  CanonicalFoodServingUnit,
} from "@/types/canonicalFood";

interface LoggedFoodsListProps {
  initialEntries: CanonicalFoodLoggedEntry[];
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

function formatMacroLine(entry: CanonicalFoodLoggedEntry): string {
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

function formatLoggedAmount(entry: CanonicalFoodLoggedEntry): string {
  if (entry.serving_display) {
    return `${entry.serving_display} (${formatCompactNumber(entry.grams, "g")})`;
  }

  return formatCompactNumber(entry.grams, "g");
}

function buildPreviewEntry(
  entry: CanonicalFoodLoggedEntry,
  gramsText: string,
): CanonicalFoodLoggedEntry {
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

function groupEntriesByMeal(entries: CanonicalFoodLoggedEntry[]) {
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
  const router = useRouter();
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
  const mealGroups = groupEntriesByMeal(entries);

  const refreshLoggedFoods = useCallback(async () => {
    setIsRefreshing(true);
    try {
      const response = await fetchCanonicalFoodLogs({
        userId,
        date: targetDate,
      });
      setEntries(response.entries);
      setError(null);
    } catch (refreshError) {
      setError(
        refreshError instanceof Error
          ? refreshError.message
          : "Logged foods are unavailable right now.",
      );
    } finally {
      setIsRefreshing(false);
    }
  }, [targetDate, userId]);

  useEffect(() => {
    window.addEventListener(CANONICAL_FOOD_LOGGED_EVENT, refreshLoggedFoods);

    return () => {
      window.removeEventListener(CANONICAL_FOOD_LOGGED_EVENT, refreshLoggedFoods);
    };
  }, [refreshLoggedFoods]);

  function startEditing(entry: CanonicalFoodLoggedEntry) {
    setActionError(null);
    setConfirmingDeleteEntryId(null);
    setEditingEntryId(entry.entry_id);
    setEditAmount(
      entry.serving_unit_id && entry.serving_quantity !== undefined
        ? formatCompactNumber(entry.serving_quantity)
        : formatCompactNumber(entry.grams),
    );
    setEditUnitKey(
      entry.serving_unit_id === undefined ? "grams" : String(entry.serving_unit_id),
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

  async function loadServingUnitsForEntry(entry: CanonicalFoodLoggedEntry) {
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

  async function saveEntry(entry: CanonicalFoodLoggedEntry) {
    const amount = Number(editAmount);
    const servingUnits = servingUnitsByFoodId[entry.canonical_food_id] ?? [];
    const selectedServingUnit =
      editUnitKey === "grams"
        ? null
        : (servingUnits.find(
            (unit) => String(unit.serving_unit_id) === editUnitKey,
          ) ?? null);

    if (!Number.isFinite(amount) || amount <= 0) {
      setActionError("Amount must be greater than 0.");
      return;
    }
    if (editUnitKey !== "grams" && selectedServingUnit === null) {
      setActionError("Serving unit is still loading. Try again in a moment.");
      return;
    }

    setPendingEntryId(entry.entry_id);
    setActionError(null);
    try {
      const response = await updateCanonicalFoodLog({
        user_id: userId,
        entry_id: entry.entry_id,
        ...(selectedServingUnit
          ? {
              serving_unit_id: selectedServingUnit.serving_unit_id,
              quantity: amount,
            }
          : {
              grams: amount,
            }),
        meal_type: editMealType,
        entry_date: targetDate,
      });
      setEntries((currentEntries) =>
        currentEntries.map((currentEntry) =>
          currentEntry.entry_id === entry.entry_id
            ? response.entry
            : currentEntry,
        ),
      );
      setEditingEntryId(null);
      setEditAmount("");
      setEditUnitKey("grams");
      setEditMealType("other");
      window.dispatchEvent(new Event(CANONICAL_FOOD_LOGGED_EVENT));
      router.refresh();
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

  async function deleteEntry(entry: CanonicalFoodLoggedEntry) {
    if (confirmingDeleteEntryId !== entry.entry_id) {
      setActionError(null);
      setEditingEntryId(null);
      setConfirmingDeleteEntryId(entry.entry_id);
      return;
    }

    setPendingEntryId(entry.entry_id);
    setActionError(null);
    try {
      await deleteCanonicalFoodLog({
        user_id: userId,
        entry_id: entry.entry_id,
        entry_date: targetDate,
      });
      setEntries((currentEntries) =>
        currentEntries.filter(
          (currentEntry) => currentEntry.entry_id !== entry.entry_id,
        ),
      );
      setConfirmingDeleteEntryId(null);
      window.dispatchEvent(new Event(CANONICAL_FOOD_LOGGED_EVENT));
      router.refresh();
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
          <p className="rounded-2xl bg-slate-50 px-4 py-3 text-sm text-slate-700">
            Updating logged foods...
          </p>
        ) : null}

        {error ? (
          <p className="rounded-2xl bg-slate-50 px-4 py-3 text-sm text-slate-700">
            {error}
          </p>
        ) : null}

        {actionError ? (
          <p className="rounded-2xl bg-rose-50 px-4 py-3 text-sm font-medium text-rose-900">
            {actionError}
          </p>
        ) : null}

        {!error && entries.length === 0 ? (
          <p className="rounded-2xl bg-slate-50 px-4 py-3 text-sm text-slate-700">
            No foods logged yet today.
          </p>
        ) : null}

        {!error && entries.length > 0 ? (
          <div className="max-h-[26rem] space-y-3 overflow-y-auto rounded-2xl bg-slate-50 px-3 py-3">
            {mealGroups.map((group) => (
              <section key={group.mealType} className="space-y-1.5">
                <div className="flex items-center justify-between gap-2 px-1">
                  <h3 className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
                    {formatMealType(group.mealType)}
                  </h3>
                  <span className="text-xs font-medium text-slate-500">
                    {group.entries.length}{" "}
                    {group.entries.length === 1 ? "item" : "items"}
                  </span>
                </div>
                <div className="divide-y divide-slate-100 rounded-xl bg-white">
                  {group.entries.map((entry) => (
                    <div
                      key={entry.entry_id}
                      className="px-3 py-2.5 text-sm"
                    >
                      {editingEntryId === entry.entry_id ? (
                        <div className="space-y-2">
                          <p className="font-semibold text-slate-950">
                            {entry.food_name}
                          </p>
                          <div className="grid gap-2 sm:grid-cols-[minmax(0,0.65fr)_minmax(0,0.75fr)_auto] sm:items-end">
                            <label className="space-y-1 text-xs font-medium text-slate-600">
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
                                  className="min-w-0 flex-1 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm font-semibold text-slate-950 outline-none focus:border-emerald-400"
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
                                  className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm font-semibold text-slate-950 outline-none focus:border-emerald-400 disabled:opacity-70"
                                >
                                  <option value="grams">grams</option>
                                  {editUnitKey !== "grams" &&
                                  entry.serving_display &&
                                  !(
                                    servingUnitsByFoodId[
                                      entry.canonical_food_id
                                    ] ?? []
                                  ).some(
                                    (unit) =>
                                      String(unit.serving_unit_id) === editUnitKey,
                                  ) ? (
                                    <option value={editUnitKey}>
                                      {entry.serving_display}
                                    </option>
                                  ) : null}
                                  {(
                                    servingUnitsByFoodId[entry.canonical_food_id] ??
                                    []
                                  ).map((unit) => (
                                    <option
                                      key={unit.serving_unit_id}
                                      value={String(unit.serving_unit_id)}
                                    >
                                      {unit.display_label}
                                    </option>
                                  ))}
                                </select>
                              </div>
                            </label>
                            <label className="space-y-1 text-xs font-medium text-slate-600">
                              <span>Meal</span>
                              <select
                                value={editMealType}
                                onChange={(event) =>
                                  setEditMealType(event.target.value)
                                }
                                className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm font-semibold text-slate-950 outline-none focus:border-emerald-400"
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
                                className="rounded-xl bg-emerald-900 px-3 py-2 text-xs font-semibold text-emerald-50 transition hover:bg-emerald-800 disabled:cursor-not-allowed disabled:opacity-60"
                              >
                                Save
                              </button>
                              <button
                                type="button"
                                onClick={cancelEditing}
                                disabled={pendingEntryId === entry.entry_id}
                                className="rounded-xl bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700 transition hover:bg-slate-200 disabled:cursor-not-allowed disabled:opacity-60"
                              >
                                Cancel
                              </button>
                            </div>
                          </div>
                          <p className="text-xs font-medium text-slate-600">
                            {(() => {
                              const amount = Number(editAmount);
                              const servingUnits =
                                servingUnitsByFoodId[entry.canonical_food_id] ??
                                [];
                              const selectedServingUnit =
                                editUnitKey === "grams"
                                  ? null
                                  : (servingUnits.find(
                                      (unit) =>
                                        String(unit.serving_unit_id) ===
                                        editUnitKey,
                                    ) ?? null);
                              const resolvedGrams =
                                selectedServingUnit === null
                                  ? amount
                                  : amount * selectedServingUnit.grams_per_unit;

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
                        <div className="grid gap-1 sm:grid-cols-[minmax(0,1fr)_auto_auto] sm:items-baseline">
                          <span className="font-semibold text-slate-950">
                            {entry.food_name}
                          </span>
                          <span className="text-slate-600 sm:text-right">
                            {formatLoggedAmount(entry)}
                          </span>
                          <div className="flex gap-2 text-xs font-semibold sm:justify-end">
                            <button
                              type="button"
                              onClick={() => startEditing(entry)}
                              disabled={pendingEntryId === entry.entry_id}
                              className="text-emerald-800 transition hover:text-emerald-950 disabled:cursor-not-allowed disabled:opacity-60"
                            >
                              Edit
                            </button>
                            <button
                              type="button"
                              onClick={() => void deleteEntry(entry)}
                              disabled={pendingEntryId === entry.entry_id}
                              className={
                                confirmingDeleteEntryId === entry.entry_id
                                  ? "text-rose-700 transition hover:text-rose-900 disabled:cursor-not-allowed disabled:opacity-60"
                                  : "text-slate-500 transition hover:text-rose-700 disabled:cursor-not-allowed disabled:opacity-60"
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
                                className="text-slate-500 transition hover:text-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
                              >
                                Cancel
                              </button>
                            ) : null}
                          </div>
                          <span className="text-xs font-medium text-slate-600 sm:col-span-3">
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
