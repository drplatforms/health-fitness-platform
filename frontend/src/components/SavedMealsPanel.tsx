"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { SavedMealEditor } from "@/components/SavedMealEditor";
import { CANONICAL_FOOD_LOGGED_EVENT } from "@/types/canonicalFood";
import { PERSONAL_FOOD_LOGGED_EVENT } from "@/types/personalFood";
import {
  archiveSavedMeal,
  fetchSavedMeals,
  logSavedMeal,
  restoreSavedMeal,
} from "@/lib/savedMealApi";
import { SavedMeal } from "@/types/savedMeal";

interface SavedMealsPanelProps {
  userId: number;
  targetDate: string;
}

const MEAL_TYPES = ["breakfast", "lunch", "dinner", "snack", "other"];

export function SavedMealsPanel({ userId, targetDate }: SavedMealsPanelProps) {
  const router = useRouter();
  const [meals, setMeals] = useState<SavedMeal[]>([]);
  const [includeArchived, setIncludeArchived] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [pendingMealId, setPendingMealId] = useState<number | null>(null);
  const [editingMeal, setEditingMeal] = useState<SavedMeal | "new" | null>(null);
  const [mealTypeOverrides, setMealTypeOverrides] = useState<Record<number, string>>(
    {},
  );
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadMeals = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await fetchSavedMeals({ userId, includeArchived });
      setMeals(response.results);
      setError(null);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Unable to load meals.");
    } finally {
      setIsLoading(false);
    }
  }, [includeArchived, userId]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadMeals();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [loadMeals]);

  async function handleLog(meal: SavedMeal) {
    const selectedMealType =
      meal.default_meal_type || mealTypeOverrides[meal.id] || "";
    if (!selectedMealType) {
      setError("Choose a meal type before logging this meal.");
      return;
    }
    setPendingMealId(meal.id);
    setError(null);
    setMessage(null);
    try {
      const response = await logSavedMeal({
        userId,
        savedMealId: meal.id,
        entryDate: targetDate,
        mealType: selectedMealType,
      });
      window.dispatchEvent(new Event(CANONICAL_FOOD_LOGGED_EVENT));
      window.dispatchEvent(new Event(PERSONAL_FOOD_LOGGED_EVENT));
      router.refresh();
      setMessage(`${response.meal_name} logged · ${response.logged_item_count} items`);
    } catch (logError) {
      setError(logError instanceof Error ? logError.message : "Unable to log meal.");
    } finally {
      setPendingMealId(null);
    }
  }

  async function handleArchiveToggle(meal: SavedMeal) {
    setPendingMealId(meal.id);
    setError(null);
    try {
      if (meal.active) {
        await archiveSavedMeal(userId, meal.id);
      } else {
        await restoreSavedMeal(userId, meal.id);
      }
      await loadMeals();
      setMessage(`${meal.display_name} ${meal.active ? "archived" : "restored"}.`);
    } catch (actionError) {
      setError(
        actionError instanceof Error ? actionError.message : "Unable to update meal.",
      );
    } finally {
      setPendingMealId(null);
    }
  }

  if (editingMeal) {
    return (
      <SavedMealEditor
        key={editingMeal === "new" ? "new" : editingMeal.id}
        userId={userId}
        initialMeal={editingMeal === "new" ? undefined : editingMeal}
        onCancel={() => setEditingMeal(null)}
        onSaved={(meal) => {
          setEditingMeal(null);
          setMessage(`${meal.display_name} saved.`);
          void loadMeals();
        }}
      />
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h3 className="text-base font-semibold text-text-strong">Saved Meals</h3>
          <p className="text-xs text-text-muted">Log a full meal to {targetDate}.</p>
        </div>
        <button
          type="button"
          onClick={() => setEditingMeal("new")}
          className="rounded-xl bg-action-primary px-3 py-2.5 text-sm font-semibold text-action-primary-foreground hover:bg-action-primary-hover"
        >
          Create meal
        </button>
      </div>

      <label className="flex w-fit items-center gap-2 text-xs font-medium text-text-muted">
        <input
          type="checkbox"
          checked={includeArchived}
          onChange={(event) => setIncludeArchived(event.target.checked)}
        />
        Show archived
      </label>

      {message ? (
        <p role="status" className="rounded-lg bg-positive-surface px-3 py-2 text-sm text-positive-foreground-strong">
          {message}
        </p>
      ) : null}
      {error ? (
        <p role="alert" className="rounded-lg bg-danger-surface px-3 py-2 text-sm text-danger-foreground">
          {error}
        </p>
      ) : null}
      {isLoading ? <p className="text-sm text-text-muted">Loading saved meals…</p> : null}
      {!isLoading && meals.length === 0 ? (
        <div className="rounded-xl border border-dashed border-border px-4 py-5 text-center">
          <p className="text-sm font-semibold text-text-strong">No saved meals yet</p>
          <p className="mt-1 text-xs text-text-muted">Build one once, then log it in one tap.</p>
        </div>
      ) : null}

      <div className="space-y-2">
        {meals.map((meal) => {
          const isPending = pendingMealId === meal.id;
          const invalidReason = meal.items.find(
            (item) => item.validation_status === "invalid",
          )?.validation_reason;
          return (
            <article
              key={meal.id}
              className={`rounded-xl border p-3 ${
                meal.active
                  ? "border-border-subtle bg-surface-muted/50"
                  : "border-border-subtle bg-surface-muted opacity-75"
              }`}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <h4 className="truncate text-sm font-semibold text-text-strong">
                    {meal.display_name}
                  </h4>
                  <p className="mt-0.5 text-xs text-text-muted">
                    {meal.item_count} {meal.item_count === 1 ? "item" : "items"}
                    {macroLine(meal)}
                  </p>
                  {meal.validation_status !== "valid" ? (
                    <p className="mt-1 text-xs text-danger-foreground">
                      {invalidReason ?? "This meal needs attention before logging."}
                    </p>
                  ) : null}
                </div>
                {!meal.active ? (
                  <span className="rounded-full bg-surface px-2 py-1 text-[0.68rem] font-semibold uppercase text-text-muted">
                    Archived
                  </span>
                ) : null}
              </div>

              {meal.active && !meal.default_meal_type ? (
                <label className="mt-2 block text-xs text-text-muted">
                  Meal type
                  <select
                    value={mealTypeOverrides[meal.id] ?? ""}
                    onChange={(event) =>
                      setMealTypeOverrides((current) => ({
                        ...current,
                        [meal.id]: event.target.value,
                      }))
                    }
                    className="ml-2 rounded-lg border border-border bg-surface px-2 py-1.5 text-sm text-text-strong"
                  >
                    <option value="">Choose</option>
                    {MEAL_TYPES.map((mealType) => (
                      <option key={mealType} value={mealType}>
                        {mealType[0].toUpperCase() + mealType.slice(1)}
                      </option>
                    ))}
                  </select>
                </label>
              ) : null}

              <div className="mt-3 flex flex-wrap gap-2">
                {meal.active ? (
                  <button
                    type="button"
                    onClick={() => void handleLog(meal)}
                    disabled={isPending || meal.validation_status !== "valid"}
                    className="rounded-lg bg-action-primary px-3 py-2 text-sm font-semibold text-action-primary-foreground hover:bg-action-primary-hover disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {isPending ? "Working…" : "Log"}
                  </button>
                ) : null}
                <button
                  type="button"
                  onClick={() => setEditingMeal(meal)}
                  disabled={isPending}
                  className="rounded-lg border border-border px-3 py-2 text-sm font-semibold text-text-body disabled:opacity-50"
                >
                  Edit
                </button>
                <button
                  type="button"
                  onClick={() => void handleArchiveToggle(meal)}
                  disabled={isPending}
                  className="rounded-lg border border-border-subtle px-3 py-2 text-sm font-semibold text-text-muted disabled:opacity-50"
                >
                  {meal.active ? "Archive" : "Restore"}
                </button>
              </div>
            </article>
          );
        })}
      </div>
    </div>
  );
}

function macroLine(meal: SavedMeal) {
  const { calories, protein_g, carbs_g, fat_g } = meal.current_macros;
  if ([calories, protein_g, carbs_g, fat_g].some((value) => value === null)) {
    return " · limited nutrition data";
  }
  return ` · ${Math.round(calories ?? 0)} cal · ${Math.round(
    protein_g ?? 0,
  )}P · ${Math.round(carbs_g ?? 0)}C · ${Math.round(fat_g ?? 0)}F`;
}
