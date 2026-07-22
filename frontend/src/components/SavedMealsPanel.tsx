"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";

import { AIRunTelemetrySummary } from "@/components/AIRunTelemetrySummary";
import { SavedMealEditor } from "@/components/SavedMealEditor";
import {
  instructionReplacementConfirmationMessage,
  needsInstructionReplacementConfirmation,
} from "@/lib/instructionRegeneration";
import { fetchMealIdeaModelOptions } from "@/lib/mealIdeasApi";
import {
  archiveSavedMeal,
  deleteSavedMeal,
  fetchScaledSavedMeal,
  fetchSavedMeals,
  generateSavedMealInstructions,
  logSavedMeal,
  restoreSavedMeal,
} from "@/lib/savedMealApi";
import { CANONICAL_FOOD_LOGGED_EVENT } from "@/types/canonicalFood";
import {
  MealIdeaModelOptionsResponse,
  MealIdeaProvider,
} from "@/types/mealIdea";
import { PERSONAL_FOOD_LOGGED_EVENT } from "@/types/personalFood";
import {
  SAVED_MEAL_CHANGED_EVENT,
  SavedMeal,
  ScaledSavedMealRecipe,
} from "@/types/savedMeal";

interface SavedMealsPanelProps {
  userId: number;
  targetDate: string;
}

const MEAL_TYPES = ["breakfast", "lunch", "dinner", "snack", "other"];
const RECIPE_SCALES = [1, 2, 3, 4] as const;

export function SavedMealsPanel({ userId, targetDate }: SavedMealsPanelProps) {
  const router = useRouter();
  const [meals, setMeals] = useState<SavedMeal[]>([]);
  const [includeArchived, setIncludeArchived] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [pendingMealId, setPendingMealId] = useState<number | null>(null);
  const [selectedMealId, setSelectedMealId] = useState<number | null>(null);
  const [editingMeal, setEditingMeal] = useState<SavedMeal | null>(null);
  const [isConfirmingDelete, setIsConfirmingDelete] = useState(false);
  const [confirmingInstructionMealId, setConfirmingInstructionMealId] = useState<
    number | null
  >(null);
  const [recipeScales, setRecipeScales] = useState<
    Record<number, (typeof RECIPE_SCALES)[number]>
  >({});
  const [scaledRecipes, setScaledRecipes] = useState<
    Record<number, ScaledSavedMealRecipe>
  >({});
  const [instructionProvider, setInstructionProvider] =
    useState<MealIdeaProvider>("local");
  const [instructionModels, setInstructionModels] =
    useState<MealIdeaModelOptionsResponse | null>(null);
  const [selectedInstructionModels, setSelectedInstructionModels] = useState<
    Record<MealIdeaProvider, string>
  >({ local: "", openai: "" });
  const [mealTypeOverrides, setMealTypeOverrides] = useState<Record<number, string>>(
    {},
  );
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const dialogRef = useRef<HTMLElement>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);
  const returnFocusRef = useRef<HTMLElement | null>(null);

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
    const timer = window.setTimeout(() => void loadMeals(), 0);
    const handleSavedMealChanged = () => void loadMeals();
    window.addEventListener(SAVED_MEAL_CHANGED_EVENT, handleSavedMealChanged);
    return () => {
      window.clearTimeout(timer);
      window.removeEventListener(SAVED_MEAL_CHANGED_EVENT, handleSavedMealChanged);
    };
  }, [loadMeals]);

  useEffect(() => {
    let active = true;
    void fetchMealIdeaModelOptions()
      .then((options) => {
        if (!active) return;
        setInstructionModels(options);
        setSelectedInstructionModels({
          local: options.providers.local.default_model,
          openai: options.providers.openai.default_model,
        });
      })
      .catch(() => {
        // Recipe browsing and logging remain available without provider discovery.
      });
    return () => {
      active = false;
    };
  }, []);

  const selectedMeal = meals.find((meal) => meal.id === selectedMealId) ?? null;
  const isDetailOpen = selectedMeal !== null;

  useEffect(() => {
    if (!isDetailOpen) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        closeDetail();
        return;
      }
      if (event.key !== "Tab") return;
      const focusable = dialogRef.current?.querySelectorAll<HTMLElement>(
        'button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [href], [tabindex]:not([tabindex="-1"])',
      );
      if (!focusable?.length) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }
    window.addEventListener("keydown", handleKeyDown);
    window.requestAnimationFrame(() => closeButtonRef.current?.focus());
    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", handleKeyDown);
      returnFocusRef.current?.focus();
    };
  }, [isDetailOpen]);

  useEffect(() => {
    if (
      selectedMealId !== null &&
      !isLoading &&
      !meals.some((meal) => meal.id === selectedMealId)
    ) {
      closeDetail();
    }
  }, [isLoading, meals, selectedMealId]);

  const selectedScale = selectedMeal ? (recipeScales[selectedMeal.id] ?? 1) : 1;
  const selectedScaledRecipe =
    selectedMeal && scaledRecipes[selectedMeal.id]?.multiplier === selectedScale
      ? scaledRecipes[selectedMeal.id]
      : null;

  function openDetail(meal: SavedMeal) {
    returnFocusRef.current = document.activeElement as HTMLElement | null;
    setSelectedMealId(meal.id);
    setEditingMeal(null);
    setIsConfirmingDelete(false);
    setConfirmingInstructionMealId(null);
    setError(null);
  }

  function closeDetail() {
    setSelectedMealId(null);
    setEditingMeal(null);
    setIsConfirmingDelete(false);
    setConfirmingInstructionMealId(null);
  }

  async function handleScale(
    meal: SavedMeal,
    multiplier: (typeof RECIPE_SCALES)[number],
  ) {
    setRecipeScales((current) => ({ ...current, [meal.id]: multiplier }));
    setError(null);
    try {
      const scaled = await fetchScaledSavedMeal({
        userId,
        savedMealId: meal.id,
        multiplier,
      });
      setScaledRecipes((current) => ({ ...current, [meal.id]: scaled }));
    } catch (scaleError) {
      setError(
        scaleError instanceof Error ? scaleError.message : "Unable to scale recipe.",
      );
    }
  }

  async function handleGenerateInstructions(meal: SavedMeal) {
    const model = selectedInstructionModels[instructionProvider];
    if (!model) {
      setError("Choose an instruction model before generating.");
      return;
    }
    setConfirmingInstructionMealId(null);
    setPendingMealId(meal.id);
    setError(null);
    setMessage(null);
    try {
      const response = await generateSavedMealInstructions({
        userId,
        savedMealId: meal.id,
        provider: instructionProvider,
        model,
      });
      setMeals((current) =>
        current.map((candidate) =>
          candidate.id === meal.id ? response.saved_meal : candidate,
        ),
      );
      setMessage(`Cooking instructions saved to ${meal.display_name}.`);
    } catch (instructionError) {
      setError(
        instructionError instanceof Error
          ? instructionError.message
          : "Unable to generate cooking instructions.",
      );
    } finally {
      setPendingMealId(null);
    }
  }

  function requestInstructionGeneration(meal: SavedMeal) {
    if (needsInstructionReplacementConfirmation(meal.cooking_instructions)) {
      setIsConfirmingDelete(false);
      setConfirmingInstructionMealId(meal.id);
      return;
    }
    void handleGenerateInstructions(meal);
  }

  async function handleLog(meal: SavedMeal) {
    const selectedMealType =
      meal.default_meal_type || mealTypeOverrides[meal.id] || "";
    if (!selectedMealType) {
      openDetail(meal);
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
      if (meal.active) await archiveSavedMeal(userId, meal.id);
      else await restoreSavedMeal(userId, meal.id);
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

  async function handleDelete(meal: SavedMeal) {
    setPendingMealId(meal.id);
    setError(null);
    try {
      await deleteSavedMeal(userId, meal.id);
      closeDetail();
      setMessage(`${meal.display_name} was permanently deleted. Existing food logs were kept.`);
      await loadMeals();
      window.dispatchEvent(new Event(SAVED_MEAL_CHANGED_EVENT));
    } catch (deleteError) {
      setError(
        deleteError instanceof Error ? deleteError.message : "Unable to delete recipe.",
      );
    } finally {
      setPendingMealId(null);
    }
  }

  const displayedIngredients = selectedMeal
    ? selectedScaledRecipe?.ingredients ??
      selectedMeal.items.map((item) => ({
        food_type: item.food_type,
        canonical_food_id: item.canonical_food_id,
        personal_food_id: item.personal_food_id,
        display_name: item.display_name,
        amount_grams: item.resolved_grams * selectedScale,
      }))
    : [];

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="text-base font-semibold text-text-strong">Saved Recipes</h3>
          <p className="text-xs text-text-muted">
            Open a recipe for ingredients, prep scaling, instructions, and editing.
          </p>
        </div>
        <label className="flex items-center gap-2 text-xs font-medium text-text-muted">
          <input
            type="checkbox"
            checked={includeArchived}
            onChange={(event) => setIncludeArchived(event.target.checked)}
          />
          Show archived
        </label>
      </div>

      <details className="rounded-xl border border-border-subtle bg-surface px-3 py-2.5">
        <summary className="cursor-pointer text-xs font-semibold text-text-body">
          Cooking instruction model
        </summary>
        <div className="mt-2 grid gap-2 sm:grid-cols-2">
          <select
            value={instructionProvider}
            onChange={(event) =>
              setInstructionProvider(event.target.value as MealIdeaProvider)
            }
            className="rounded-lg border border-border bg-surface px-2 py-2 text-sm text-text-strong"
          >
            <option value="local">Local</option>
            <option value="openai">OpenAI</option>
          </select>
          <select
            value={selectedInstructionModels[instructionProvider]}
            disabled={!instructionModels}
            onChange={(event) =>
              setSelectedInstructionModels((current) => ({
                ...current,
                [instructionProvider]: event.target.value,
              }))
            }
            className="rounded-lg border border-border bg-surface px-2 py-2 text-sm text-text-strong disabled:opacity-60"
          >
            {!instructionModels ? <option value="">Loading models…</option> : null}
            {instructionModels?.providers[instructionProvider].models.map((option) => (
              <option key={option.id} value={option.id}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
      </details>

      {message ? (
        <p
          role="status"
          className="rounded-lg bg-positive-surface px-3 py-2 text-sm text-positive-foreground-strong"
        >
          {message}
        </p>
      ) : null}
      {error ? (
        <p
          role="alert"
          className="rounded-lg bg-danger-surface px-3 py-2 text-sm text-danger-foreground"
        >
          {error}
        </p>
      ) : null}
      {isLoading ? <p className="text-sm text-text-muted">Loading saved recipes…</p> : null}
      {!isLoading && meals.length === 0 ? (
        <div className="rounded-xl border border-dashed border-border px-4 py-5 text-center">
          <p className="text-sm font-semibold text-text-strong">No saved recipes yet</p>
          <p className="mt-1 text-xs text-text-muted">
            Save an AI idea or create one manually, then reuse it here.
          </p>
        </div>
      ) : null}

      <div className="grid gap-2 md:grid-cols-2">
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
                      {invalidReason ?? "This recipe needs attention before logging."}
                    </p>
                  ) : null}
                </div>
                <div className="flex shrink-0 flex-wrap justify-end gap-1">
                  <span className="rounded-full bg-surface px-2 py-1 text-[0.68rem] font-semibold uppercase text-text-muted">
                    {meal.source_type === "ai" ? "AI" : "Manual"}
                  </span>
                  {!meal.active ? (
                    <span className="rounded-full bg-surface px-2 py-1 text-[0.68rem] font-semibold uppercase text-text-muted">
                      Archived
                    </span>
                  ) : null}
                </div>
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => openDetail(meal)}
                  className="rounded-lg border border-border px-3 py-2 text-sm font-semibold text-text-body"
                >
                  Open recipe
                </button>
                {meal.active && meal.default_meal_type ? (
                  <button
                    type="button"
                    onClick={() => void handleLog(meal)}
                    disabled={isPending || meal.validation_status !== "valid"}
                    className="rounded-lg bg-action-primary px-3 py-2 text-sm font-semibold text-action-primary-foreground hover:bg-action-primary-hover disabled:opacity-50"
                  >
                    {isPending ? "Working…" : "Log 1x"}
                  </button>
                ) : null}
              </div>
            </article>
          );
        })}
      </div>

      {selectedMeal
        ? createPortal(
            <div className="fixed inset-0 z-[90]" role="presentation">
          <button
            type="button"
            aria-label="Close recipe details"
            onClick={closeDetail}
            className="absolute inset-0 bg-slate-950/45 backdrop-blur-[1px]"
          />
              <section
                ref={dialogRef}
                role="dialog"
                aria-modal="true"
                aria-labelledby="saved-recipe-detail-title"
                className="absolute inset-0 overflow-y-auto overscroll-contain bg-surface p-4 pb-8 shadow-2xl sm:inset-y-3 sm:right-3 sm:left-auto sm:w-full sm:max-w-2xl sm:rounded-2xl sm:border sm:border-border-subtle sm:p-5"
              >
            <div className="sticky top-0 z-10 -mx-1 mb-4 flex items-start justify-between gap-3 bg-surface/95 px-1 pb-3 backdrop-blur">
              <div className="min-w-0">
                <p className="text-[0.68rem] font-semibold uppercase tracking-wide text-text-muted">
                  Saved recipe
                </p>
                <h3
                  id="saved-recipe-detail-title"
                  className="truncate text-lg font-semibold text-text-strong"
                >
                  {selectedMeal.display_name}
                </h3>
              </div>
              <button
                ref={closeButtonRef}
                type="button"
                onClick={closeDetail}
                className="rounded-lg border border-border px-3 py-2 text-sm font-semibold text-text-body"
              >
                Close
              </button>
            </div>

            {message ? (
              <p
                role="status"
                className="mb-3 rounded-lg bg-positive-surface px-3 py-2 text-sm text-positive-foreground-strong"
              >
                {message}
              </p>
            ) : null}
            {error ? (
              <p
                role="alert"
                className="mb-3 rounded-lg bg-danger-surface px-3 py-2 text-sm text-danger-foreground"
              >
                {error}
              </p>
            ) : null}

            {editingMeal ? (
              <SavedMealEditor
                key={editingMeal.id}
                userId={userId}
                initialMeal={editingMeal}
                onCancel={() => setEditingMeal(null)}
                onSaved={(meal) => {
                  setEditingMeal(null);
                  setSelectedMealId(meal.id);
                  setMessage(`${meal.display_name} saved.`);
                  void loadMeals();
                }}
              />
            ) : (
              <div className="space-y-4">
                {selectedMeal.source_type === "ai" ? (
                  <p className="text-xs text-text-muted">
                    Source: AI · {providerName(selectedMeal.source_provider)}
                    {selectedMeal.source_model ? ` · ${selectedMeal.source_model}` : ""}
                  </p>
                ) : (
                  <p className="text-xs text-text-muted">Source: Manual recipe</p>
                )}

                {!selectedMeal.default_meal_type ? (
                  <label className="block text-xs font-semibold text-text-muted">
                    Meal type for logging
                    <select
                      value={mealTypeOverrides[selectedMeal.id] ?? ""}
                      onChange={(event) =>
                        setMealTypeOverrides((current) => ({
                          ...current,
                          [selectedMeal.id]: event.target.value,
                        }))
                      }
                      className="mt-1.5 w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text-strong sm:max-w-xs"
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

                <div>
                  <p className="text-[0.68rem] font-semibold uppercase tracking-wide text-text-muted">
                    Prep scale
                  </p>
                  <div className="mt-1.5 flex gap-1.5">
                    {RECIPE_SCALES.map((scale) => (
                      <button
                        key={scale}
                        type="button"
                        aria-pressed={selectedScale === scale}
                        onClick={() => void handleScale(selectedMeal, scale)}
                        className={`rounded-lg border px-2.5 py-1.5 text-xs font-semibold ${
                          selectedScale === scale
                            ? "border-border-accent bg-positive-surface text-positive-foreground-strong"
                            : "border-border bg-surface text-text-body"
                        }`}
                      >
                        {scale}x
                      </button>
                    ))}
                  </div>
                  <p className="mt-1.5 text-xs text-text-muted">
                    Prep scaling changes this view only. Logging always adds the saved 1x recipe.
                  </p>
                </div>

                <div className="rounded-xl border border-border-subtle bg-surface-muted/40 p-3">
                  <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">
                    Ingredients
                  </p>
                  <ul className="mt-2 space-y-1.5 text-sm text-text-body">
                    {displayedIngredients.map((ingredient) => (
                      <li
                        key={`${ingredient.food_type}:${ingredient.canonical_food_id ?? ingredient.personal_food_id}`}
                        className="flex items-baseline justify-between gap-3"
                      >
                        <span>{ingredient.display_name}</span>
                        <span className="shrink-0 text-xs text-text-muted">
                          {formatAmount(ingredient.amount_grams)} g
                        </span>
                      </li>
                    ))}
                  </ul>
                  <p className="mt-3 border-t border-border-subtle pt-2 text-xs font-semibold text-text-body">
                    {scaledMacroLine(selectedMeal, selectedScale, selectedScaledRecipe)}
                  </p>
                </div>

                <div className="rounded-xl border border-border-subtle bg-surface-muted/40 p-3">
                  <p className="text-xs font-semibold text-text-strong">
                    Cooking instructions
                  </p>
                  {selectedMeal.cooking_instructions.length > 0 ? (
                    <>
                      <ol className="mt-2 list-decimal space-y-1.5 pl-5 text-sm text-text-body">
                        {selectedMeal.cooking_instructions.map((step, index) => (
                          <li key={`${index}:${step}`}>{step}</li>
                        ))}
                      </ol>
                      {selectedScale > 1 ? (
                        <p className="mt-2 text-xs text-text-muted">
                          Instructions are saved for 1x; use the scaled quantities above for this prep batch.
                        </p>
                      ) : null}
                    </>
                  ) : (
                    <p className="mt-1.5 text-sm text-text-muted">
                      No cooking instructions saved yet.
                    </p>
                  )}
                  {selectedMeal.active ? (
                    <button
                      type="button"
                      onClick={() => requestInstructionGeneration(selectedMeal)}
                      disabled={
                        pendingMealId === selectedMeal.id ||
                        !selectedInstructionModels[instructionProvider]
                      }
                      className="mt-3 rounded-lg border border-border px-3 py-2 text-xs font-semibold text-text-body disabled:opacity-50"
                    >
                      {pendingMealId === selectedMeal.id
                        ? "Generating…"
                        : selectedMeal.cooking_instructions.length > 0
                          ? "Regenerate instructions"
                          : "Generate instructions"}
                    </button>
                  ) : null}
                  {confirmingInstructionMealId === selectedMeal.id ? (
                    <div
                      role="alert"
                      aria-labelledby="replace-saved-instructions-title"
                      className="mt-3 rounded-xl border border-warning-foreground/30 bg-warning-surface p-3"
                    >
                      <p
                        id="replace-saved-instructions-title"
                        className="text-sm font-semibold text-warning-foreground"
                      >
                        Replace cooking instructions?
                      </p>
                      <p className="mt-1 text-xs text-warning-foreground">
                        {instructionReplacementConfirmationMessage(
                          providerName(instructionProvider),
                          selectedInstructionModels[instructionProvider],
                        )}
                      </p>
                      <div className="mt-3 flex gap-2">
                        <button
                          type="button"
                          onClick={() => setConfirmingInstructionMealId(null)}
                          className="rounded-lg border border-border px-3 py-2 text-sm font-semibold text-text-body"
                        >
                          Cancel
                        </button>
                        <button
                          type="button"
                          onClick={() => void handleGenerateInstructions(selectedMeal)}
                          disabled={
                            pendingMealId === selectedMeal.id ||
                            !selectedInstructionModels[instructionProvider]
                          }
                          className="rounded-lg bg-action-primary px-3 py-2 text-sm font-semibold text-action-primary-foreground hover:bg-action-primary-hover disabled:opacity-50"
                        >
                          Regenerate
                        </button>
                      </div>
                    </div>
                  ) : null}
                  {selectedMeal.instruction_telemetry ? (
                    <AIRunTelemetrySummary
                      telemetry={selectedMeal.instruction_telemetry}
                      className="mt-3 border-t border-border-subtle pt-3"
                    />
                  ) : null}
                </div>

                <div className="flex flex-wrap gap-2 border-t border-border-subtle pt-4">
                  {selectedMeal.active ? (
                    <button
                      type="button"
                      onClick={() => void handleLog(selectedMeal)}
                      disabled={
                        pendingMealId === selectedMeal.id ||
                        selectedMeal.validation_status !== "valid"
                      }
                      className="rounded-lg bg-action-primary px-3 py-2 text-sm font-semibold text-action-primary-foreground hover:bg-action-primary-hover disabled:opacity-50"
                    >
                      {pendingMealId === selectedMeal.id ? "Working…" : "Log saved 1x"}
                    </button>
                  ) : null}
                  <button
                    type="button"
                    onClick={() => {
                      setIsConfirmingDelete(false);
                      setConfirmingInstructionMealId(null);
                      setEditingMeal(selectedMeal);
                    }}
                    disabled={pendingMealId === selectedMeal.id}
                    className="rounded-lg border border-border px-3 py-2 text-sm font-semibold text-text-body disabled:opacity-50"
                  >
                    Edit
                  </button>
                  <button
                    type="button"
                    onClick={() => void handleArchiveToggle(selectedMeal)}
                    disabled={pendingMealId === selectedMeal.id}
                    className="rounded-lg border border-border-subtle px-3 py-2 text-sm font-semibold text-text-muted disabled:opacity-50"
                  >
                    {selectedMeal.active ? "Archive" : "Restore"}
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setConfirmingInstructionMealId(null);
                      setIsConfirmingDelete(true);
                    }}
                    disabled={pendingMealId === selectedMeal.id}
                    className="rounded-lg border border-danger-foreground/40 px-3 py-2 text-sm font-semibold text-danger-foreground disabled:opacity-50"
                  >
                    Delete
                  </button>
                </div>

                {isConfirmingDelete ? (
                  <div
                    role="alert"
                    className="rounded-xl border border-danger-foreground/30 bg-danger-surface p-3"
                  >
                    <p className="text-sm font-semibold text-danger-foreground">
                      Permanently delete {selectedMeal.display_name}?
                    </p>
                    <p className="mt-1 text-xs text-danger-foreground">
                      The saved recipe and its editable ingredients will be removed. Existing nutrition logs stay intact.
                    </p>
                    <div className="mt-3 flex gap-2">
                      <button
                        type="button"
                        onClick={() => setIsConfirmingDelete(false)}
                        className="rounded-lg border border-border px-3 py-2 text-sm font-semibold text-text-body"
                      >
                        Cancel
                      </button>
                      <button
                        type="button"
                        onClick={() => void handleDelete(selectedMeal)}
                        disabled={pendingMealId === selectedMeal.id}
                        className="rounded-lg bg-danger-foreground px-3 py-2 text-sm font-semibold text-white disabled:opacity-50"
                      >
                        {pendingMealId === selectedMeal.id ? "Deleting…" : "Delete permanently"}
                      </button>
                    </div>
                  </div>
                ) : null}
              </div>
            )}
              </section>
            </div>,
            document.body,
          )
        : null}
    </div>
  );
}

function providerName(provider: string | null) {
  if (provider === "openai") return "OpenAI";
  if (provider === "local") return "Local";
  return provider ?? "Unknown provider";
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

function scaledMacroLine(
  meal: SavedMeal,
  multiplier: (typeof RECIPE_SCALES)[number],
  scaled: ScaledSavedMealRecipe | null,
) {
  const source = scaled?.current_macros ?? {
    calories:
      meal.current_macros.calories === null
        ? null
        : meal.current_macros.calories * multiplier,
    protein_g:
      meal.current_macros.protein_g === null
        ? null
        : meal.current_macros.protein_g * multiplier,
    carbs_g:
      meal.current_macros.carbs_g === null
        ? null
        : meal.current_macros.carbs_g * multiplier,
    fat_g:
      meal.current_macros.fat_g === null
        ? null
        : meal.current_macros.fat_g * multiplier,
  };
  if (Object.values(source).some((value) => value === null)) {
    return `${multiplier}x · limited nutrition data`;
  }
  return `${multiplier}x · ${Math.round(source.calories ?? 0)} cal · ${Math.round(
    source.protein_g ?? 0,
  )}P · ${Math.round(source.carbs_g ?? 0)}C · ${Math.round(source.fat_g ?? 0)}F`;
}

function formatAmount(value: number) {
  return Number.isInteger(value) ? String(value) : value.toFixed(1);
}
