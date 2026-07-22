"use client";

import { FormEvent, useEffect, useRef, useState } from "react";

import { AIRunTelemetrySummary } from "@/components/AIRunTelemetrySummary";
import {
  instructionReplacementConfirmationMessage,
  needsInstructionReplacementConfirmation,
} from "@/lib/instructionRegeneration";
import {
  fetchMealIdeaHistory,
  fetchMealIdeaModelOptions,
  generateMealInstructions,
  generateMealIdeas,
} from "@/lib/mealIdeasApi";
import { createSavedMeal, updateSavedMeal } from "@/lib/savedMealApi";
import {
  GroundedMealIdea,
  MealIdeaGenerationHistoryItem,
  MealIdeaMealType,
  MealIdeaModelOptionsResponse,
  MealIdeaProvider,
  MealIdeaSteering,
  MealIdeasResponse,
  MealInstructionsResponse,
} from "@/types/mealIdea";
import {
  SAVED_MEAL_CHANGED_EVENT,
  SavedMealMutation,
} from "@/types/savedMeal";

interface MealIdeasPanelProps {
  userId: number;
  targetDate: string;
}

const STEERING_OPTIONS: Array<{ value: MealIdeaSteering; label: string }> = [
  { value: "sweet", label: "Sweet" },
  { value: "savory", label: "Savory" },
  { value: "quick", label: "Quick" },
  { value: "high_volume", label: "High volume" },
  { value: "comfort", label: "Comfort" },
  { value: "light_fresh", label: "Light / fresh" },
  { value: "portable", label: "Portable" },
  { value: "surprise_me", label: "Surprise me" },
];

const MEAL_TYPES: Array<{ value: MealIdeaMealType; label: string }> = [
  { value: "breakfast", label: "Breakfast" },
  { value: "lunch", label: "Lunch" },
  { value: "dinner", label: "Dinner" },
  { value: "snack", label: "Snack" },
  { value: "dessert", label: "Dessert" },
];

export function MealIdeasPanel({ userId, targetDate }: MealIdeasPanelProps) {
  const [provider, setProvider] = useState<MealIdeaProvider>("local");
  const [modelOptions, setModelOptions] =
    useState<MealIdeaModelOptionsResponse | null>(null);
  const [selectedModels, setSelectedModels] = useState<
    Record<MealIdeaProvider, string>
  >({ local: "", openai: "" });
  const [modelOptionsError, setModelOptionsError] = useState<string | null>(null);
  const generatedExposureRef = useRef({
    ideaNames: [] as string[],
    foodNames: [] as string[],
  });
  const [steering, setSteering] =
    useState<MealIdeaSteering>("surprise_me");
  const [mealType, setMealType] = useState<MealIdeaMealType | null>(null);
  const [intent, setIntent] = useState("");
  const [result, setResult] = useState<MealIdeasResponse | null>(null);
  const [history, setHistory] = useState<MealIdeaGenerationHistoryItem[]>([]);
  const [selectedHistoryId, setSelectedHistoryId] = useState<number | null>(null);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const [controlsExpanded, setControlsExpanded] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const selectedModel = selectedModels[provider];
  const providerModels = modelOptions?.providers[provider];

  useEffect(() => {
    let active = true;
    void fetchMealIdeaModelOptions()
      .then((options) => {
        if (!active) {
          return;
        }
        setModelOptions(options);
        setSelectedModels((current) => ({
          local: optionStillAvailable(options, "local", current.local)
            ? current.local
            : options.providers.local.default_model,
          openai: optionStillAvailable(options, "openai", current.openai)
            ? current.openai
            : options.providers.openai.default_model,
        }));
        setModelOptionsError(null);
      })
      .catch((loadError) => {
        if (active) {
          setModelOptionsError(
            loadError instanceof Error
              ? loadError.message
              : "Meal idea models are unavailable.",
          );
        }
      });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    let active = true;
    void fetchMealIdeaHistory(userId)
      .then((response) => {
        if (!active) return;
        setHistory(response.results);
        seedDiversityFromHistory(response.results);
        const latest = response.results[0];
        if (latest) {
          restoreGeneration(latest);
          setControlsExpanded(false);
        }
        setHistoryError(null);
      })
      .catch((loadError) => {
        if (!active) return;
        setHistoryError(
          loadError instanceof Error
            ? loadError.message
            : "Recent meal ideas are unavailable.",
        );
      });
    return () => {
      active = false;
    };
  }, [userId]);

  function seedDiversityFromHistory(items: MealIdeaGenerationHistoryItem[]) {
    generatedExposureRef.current = {
      ideaNames: appendBoundedExposure(
        [],
        items.flatMap((item) => item.result.ideas.map((idea) => idea.name)).reverse(),
        20,
      ),
      foodNames: appendBoundedExposure(
        [],
        items
          .flatMap((item) =>
            item.result.ideas.flatMap((idea) =>
              idea.ingredients.map((ingredient) => ingredient.display_name),
            ),
          )
          .reverse(),
        40,
      ),
    };
  }

  function restoreGeneration(item: MealIdeaGenerationHistoryItem) {
    setSelectedHistoryId(item.id);
    setResult(item.result);
    setProvider(item.request.provider);
    setSelectedModels((current) => ({
      ...current,
      [item.request.provider]: item.request.model,
    }));
    setSteering(item.request.creative_steering);
    setMealType(item.request.meal_type);
    setIntent(item.request.intent ?? "");
    setError(null);
  }

  async function refreshHistory() {
    try {
      const response = await fetchMealIdeaHistory(userId);
      setHistory(response.results);
      setSelectedHistoryId(response.results[0]?.id ?? null);
      seedDiversityFromHistory(response.results);
      setHistoryError(null);
    } catch (loadError) {
      setHistoryError(
        loadError instanceof Error
          ? loadError.message
          : "Recent meal ideas are unavailable.",
      );
    }
  }

  async function handleGenerate(event?: FormEvent) {
    event?.preventDefault();
    if (!selectedModel) {
      setError("Choose a model before generating meal ideas.");
      return;
    }
    setIsGenerating(true);
    setError(null);
    try {
      const response = await generateMealIdeas({
        userId,
        targetDate,
        provider,
        model: selectedModel,
        creativeSteering: steering,
        mealType,
        intent,
        generationNonce: generationNonce(),
        previousIdeaNames: generatedExposureRef.current.ideaNames,
        recentGeneratedFoodNames: generatedExposureRef.current.foodNames,
      });
      generatedExposureRef.current = {
        ideaNames: appendBoundedExposure(
          generatedExposureRef.current.ideaNames,
          response.ideas.map((idea) => idea.name),
          20,
        ),
        foodNames: appendBoundedExposure(
          generatedExposureRef.current.foodNames,
          response.ideas.flatMap((idea) =>
            idea.ingredients.map((ingredient) => ingredient.display_name),
          ),
          40,
        ),
      };
      setSelectedHistoryId(null);
      setResult(response);
      setControlsExpanded(false);
      await refreshHistory();
    } catch (generationError) {
      setError(
        generationError instanceof Error
          ? generationError.message
          : "Meal ideas could not be generated. Retry or switch providers.",
      );
    } finally {
      setIsGenerating(false);
    }
  }

  return (
    <section className="space-y-4 rounded-2xl border border-border-subtle bg-surface-muted/35 p-3 sm:p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
          <div>
            <h3 className="text-base font-semibold text-text-strong">AI Meal Ideas</h3>
            <p className="mt-0.5 text-xs text-text-muted">
              Creative concepts, grounded with your food catalog nutrition.
            </p>
          </div>
          {result ? (
            <span className="rounded-full border border-border-subtle bg-surface px-2.5 py-1 text-xs font-semibold text-text-muted">
              Generated with {providerLabel(result.provider)} · {result.model}
            </span>
          ) : null}
          </div>
        </div>
        {result ? (
          <div className="flex shrink-0 flex-wrap gap-2">
            <button
              type="button"
              onClick={() => setControlsExpanded((current) => !current)}
              className="rounded-lg border border-border px-3 py-2 text-xs font-semibold text-text-body"
            >
              {controlsExpanded ? "Hide options" : "Change options"}
            </button>
            <button
              type="button"
              onClick={() => void handleGenerate()}
              disabled={isGenerating || !selectedModel}
              className="rounded-lg bg-action-primary px-3 py-2 text-xs font-semibold text-action-primary-foreground hover:bg-action-primary-hover disabled:opacity-60"
            >
              {isGenerating ? "Generating…" : "Generate another"}
            </button>
          </div>
        ) : null}
      </div>

      {controlsExpanded || !result ? (
      <form onSubmit={handleGenerate} className="space-y-4">
        <fieldset>
          <legend className="text-xs font-semibold uppercase tracking-wide text-text-muted">
            Provider
          </legend>
          <div className="mt-2 grid grid-cols-2 gap-2">
            {(["local", "openai"] as MealIdeaProvider[]).map((option) => (
              <button
                key={option}
                type="button"
                aria-pressed={provider === option}
                onClick={() => setProvider(option)}
                className={`rounded-xl border px-3 py-2.5 text-sm font-semibold transition-colors ${
                  provider === option
                    ? "border-border-accent bg-positive-surface text-positive-foreground-strong"
                    : "border-border bg-surface text-text-body"
                }`}
              >
                {providerLabel(option)}
              </button>
            ))}
          </div>
        </fieldset>

        <label className="block text-xs font-semibold uppercase tracking-wide text-text-muted">
          Model
          <select
            value={selectedModel}
            disabled={!providerModels || providerModels.models.length === 0}
            onChange={(event) =>
              setSelectedModels((current) => ({
                ...current,
                [provider]: event.target.value,
              }))
            }
            className="mt-2 w-full rounded-xl border border-border bg-surface px-3 py-2.5 text-sm font-normal normal-case tracking-normal text-text-strong disabled:opacity-60 sm:max-w-sm"
          >
            {!providerModels ? <option value="">Loading models…</option> : null}
            {providerModels?.models.map((option) => (
              <option key={option.id} value={option.id}>
                {option.label}
              </option>
            ))}
          </select>
        </label>

        {providerModels?.message ? (
          <p className="text-xs text-text-muted">{providerModels.message}</p>
        ) : null}
        {modelOptionsError ? (
          <p role="alert" className="text-xs text-danger-foreground">
            {modelOptionsError}
          </p>
        ) : null}

        <fieldset>
          <legend className="text-xs font-semibold uppercase tracking-wide text-text-muted">
            Direction
          </legend>
          <div className="mt-2 flex flex-wrap gap-2">
            {STEERING_OPTIONS.map((option) => (
              <button
                key={option.value}
                type="button"
                aria-pressed={steering === option.value}
                onClick={() => setSteering(option.value)}
                className={`rounded-full border px-3 py-1.5 text-xs font-semibold transition-colors ${
                  steering === option.value
                    ? "border-border-accent bg-positive-surface text-positive-foreground-strong"
                    : "border-border bg-surface text-text-body"
                }`}
              >
                {option.label}
              </button>
            ))}
          </div>
        </fieldset>

        <div className="grid gap-3 sm:grid-cols-[12rem_1fr]">
          <label className="text-xs font-semibold text-text-muted">
            Meal type
            <select
              value={mealType ?? ""}
              onChange={(event) =>
                setMealType((event.target.value || null) as MealIdeaMealType | null)
              }
              className="mt-1.5 w-full rounded-xl border border-border bg-surface px-3 py-2.5 text-sm font-normal text-text-strong"
            >
              <option value="">Any meal</option>
              {MEAL_TYPES.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <label className="text-xs font-semibold text-text-muted">
            What are you in the mood for? <span className="font-normal">Optional</span>
            <input
              value={intent}
              maxLength={240}
              onChange={(event) => setIntent(event.target.value)}
              placeholder="Use eggplant, something spicy, make something with chicken…"
              className="mt-1.5 w-full rounded-xl border border-border bg-surface px-3 py-2.5 text-sm font-normal text-text-strong placeholder:text-text-muted"
            />
          </label>
        </div>

        <button
          type="submit"
          disabled={isGenerating || !selectedModel}
          className="rounded-xl bg-action-primary px-4 py-2.5 text-sm font-semibold text-action-primary-foreground hover:bg-action-primary-hover disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isGenerating
            ? `Asking ${providerLabel(provider)}…`
            : result
              ? "Generate another set"
              : "Generate meal ideas"}
        </button>
      </form>
      ) : (
        <div className="flex flex-wrap gap-x-4 gap-y-1 rounded-xl border border-border-subtle bg-surface px-3 py-2.5 text-xs text-text-muted">
          <span>{providerLabel(provider)} · {selectedModel || result.model}</span>
          <span>{steeringLabel(steering)}</span>
          <span>{mealType ? mealTypeLabel(mealType) : "Any meal"}</span>
          {intent.trim() ? <span className="truncate">“{intent.trim()}”</span> : null}
        </div>
      )}

      {history.length > 0 ? (
        <details className="rounded-xl border border-border-subtle bg-surface px-3 py-2.5">
          <summary className="cursor-pointer text-xs font-semibold text-text-body">
            Recent generations ({history.length})
          </summary>
          <div className="mt-2 grid gap-2 sm:grid-cols-2">
            {history.map((item) => (
              <button
                key={item.id}
                type="button"
                aria-pressed={selectedHistoryId === item.id}
                onClick={() => {
                  restoreGeneration(item);
                  setControlsExpanded(false);
                }}
                className={`rounded-lg border px-3 py-2 text-left text-xs transition ${
                  selectedHistoryId === item.id
                    ? "border-border-accent bg-positive-surface text-positive-foreground-strong"
                    : "border-border bg-surface text-text-body"
                }`}
              >
                <span className="block font-semibold">
                  {formatGenerationTime(item.created_at)} · {providerLabel(item.result.provider)}
                </span>
                <span className="mt-0.5 block truncate opacity-80">
                  {item.result.ideas.map((idea) => idea.name).join(" · ")}
                </span>
              </button>
            ))}
          </div>
        </details>
      ) : null}

      {historyError ? (
        <p role="status" className="text-xs text-text-muted">
          {historyError} New ideas can still be generated.
        </p>
      ) : null}

      {error ? (
        <div role="alert" className="rounded-xl bg-danger-surface px-3 py-2.5 text-sm text-danger-foreground">
          {error}
        </div>
      ) : null}

      {result ? (
        <div className="space-y-3" aria-live="polite">
          <AIRunTelemetrySummary
            telemetry={result.telemetry}
            className="rounded-xl border border-border-subtle bg-surface px-3 py-2.5"
          />
          <div className="grid gap-3 md:grid-cols-2">
            {result.ideas.map((idea, index) => (
              <MealIdeaCard
                key={`${selectedHistoryId ?? "new"}:${index}:${idea.name}:${idea.ingredients
                  .map((ingredient) => `${ingredient.canonical_food_id}:${ingredient.amount_grams}`)
                  .join("|")}`}
                idea={idea}
                userId={userId}
                provider={result.provider}
                model={result.model}
              />
            ))}
          </div>
          {result.rejected_concept_count > 0 ? (
            <p className="text-xs text-text-muted">
              {result.rejected_concept_count} concept
              {result.rejected_concept_count === 1 ? " was" : "s were"} omitted because
              the ingredients could not be grounded reliably.
            </p>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}

function MealIdeaCard({
  idea,
  userId,
  provider,
  model,
}: {
  idea: GroundedMealIdea;
  userId: number;
  provider: MealIdeaProvider;
  model: string;
}) {
  const [instructionResult, setInstructionResult] =
    useState<MealInstructionsResponse | null>(null);
  const [isGeneratingInstructions, setIsGeneratingInstructions] = useState(false);
  const [isConfirmingInstructionReplacement, setIsConfirmingInstructionReplacement] =
    useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [savedMealId, setSavedMealId] = useState<number | null>(null);
  const [savedInstructionKey, setSavedInstructionKey] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleGenerateInstructions() {
    setIsConfirmingInstructionReplacement(false);
    setIsGeneratingInstructions(true);
    setError(null);
    try {
      const response = await generateMealInstructions({
        userId,
        provider,
        model,
        idea,
      });
      setInstructionResult(response);
    } catch (generationError) {
      setError(
        generationError instanceof Error
          ? generationError.message
          : "Cooking instructions could not be generated.",
      );
    } finally {
      setIsGeneratingInstructions(false);
    }
  }

  function requestInstructionGeneration() {
    if (
      needsInstructionReplacementConfirmation(instructionResult?.instructions)
    ) {
      setIsConfirmingInstructionReplacement(true);
      return;
    }
    void handleGenerateInstructions();
  }

  async function handleSave() {
    setIsSaving(true);
    setError(null);
    setMessage(null);
    try {
      const payload: SavedMealMutation = {
        user_id: userId,
        display_name: idea.name,
        default_meal_type: idea.meal_type === "dessert" ? "other" : idea.meal_type,
        cooking_instructions: instructionResult?.instructions ?? [],
        instruction_telemetry: instructionResult?.telemetry ?? null,
        source_type: "ai",
        source_provider: provider,
        source_model: model,
        items: idea.ingredients.map((ingredient) => ({
          food_type: "canonical",
          canonical_food_id: ingredient.canonical_food_id,
          grams: ingredient.amount_grams,
        })),
      };
      const response = savedMealId
        ? await updateSavedMeal(savedMealId, payload)
        : await createSavedMeal(payload);
      setSavedMealId(response.saved_meal.id);
      setSavedInstructionKey(JSON.stringify(instructionResult?.instructions ?? []));
      window.dispatchEvent(new Event(SAVED_MEAL_CHANGED_EVENT));
      setMessage(
        savedMealId
          ? "Saved recipe updated with these instructions."
          : "Saved to Saved Recipes with these exact grounded quantities.",
      );
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Unable to save recipe.");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <article className="rounded-xl border border-border-subtle bg-surface p-3">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h4 className="text-sm font-semibold text-text-strong">{idea.name}</h4>
          <p className="mt-0.5 text-xs capitalize text-text-muted">{idea.meal_type}</p>
        </div>
        {idea.available_ingredient_count > 0 ? (
          <span className="shrink-0 rounded-full bg-positive-surface px-2 py-1 text-[0.68rem] font-semibold text-positive-foreground-strong">
            {idea.available_ingredient_count} available
          </span>
        ) : null}
      </div>

      <ul className="mt-3 space-y-1.5 text-sm text-text-body">
        {idea.ingredients.map((ingredient) => (
          <li key={ingredient.canonical_food_id} className="flex items-baseline justify-between gap-3">
            <span>
              {ingredient.display_name}
              {ingredient.is_available ? (
                <span className="ml-1 text-xs font-semibold text-positive-foreground-strong">
                  Available
                </span>
              ) : null}
            </span>
            <span className="shrink-0 text-xs text-text-muted">
              {ingredient.quantity_display.display_text}
            </span>
          </li>
        ))}
      </ul>

      <p className="mt-3 border-t border-border-subtle pt-2.5 text-xs font-semibold text-text-body">
        {Math.round(idea.calories)} cal · {Math.round(idea.protein_g)}P ·{" "}
        {Math.round(idea.carbs_g)}C · {Math.round(idea.fat_g)}F
      </p>
      {instructionResult ? (
        <div className="mt-3 space-y-2">
          <details className="rounded-lg bg-surface-muted/60 p-2.5">
            <summary className="cursor-pointer text-xs font-semibold text-text-strong">
              Cooking instructions
            </summary>
            <ol className="mt-2 list-decimal space-y-1.5 pl-5 text-sm text-text-body">
              {instructionResult.instructions.map((step, index) => (
                <li key={`${index}:${step}`}>{step}</li>
              ))}
            </ol>
          </details>
          <AIRunTelemetrySummary
            telemetry={instructionResult.telemetry}
            className="rounded-lg border border-border-subtle bg-surface-muted/40 px-2.5 py-2"
          />
        </div>
      ) : null}
      <div className="mt-3 flex flex-wrap gap-2">
        <button
          type="button"
          onClick={requestInstructionGeneration}
          disabled={isGeneratingInstructions}
          className="rounded-lg border border-border px-3 py-2 text-xs font-semibold text-text-body disabled:opacity-50"
        >
          {isGeneratingInstructions
            ? "Generating…"
            : instructionResult
              ? "Regenerate instructions"
              : "Cooking instructions"}
        </button>
        <button
          type="button"
          onClick={() => void handleSave()}
          disabled={
            isSaving ||
            (savedMealId !== null &&
              savedInstructionKey ===
                JSON.stringify(instructionResult?.instructions ?? []))
          }
          className="rounded-lg bg-action-primary px-3 py-2 text-xs font-semibold text-action-primary-foreground hover:bg-action-primary-hover disabled:opacity-50"
        >
          {isSaving
            ? "Saving…"
            : savedMealId === null
              ? "Save recipe"
              : savedInstructionKey ===
                  JSON.stringify(instructionResult?.instructions ?? [])
                ? "Saved"
                : "Update saved recipe"}
        </button>
      </div>
      {isConfirmingInstructionReplacement ? (
        <div
          role="alert"
          className="mt-3 rounded-xl border border-warning-foreground/30 bg-warning-surface p-3"
        >
          <p className="text-sm font-semibold text-warning-foreground">
            Replace cooking instructions?
          </p>
          <p className="mt-1 text-xs text-warning-foreground">
            {instructionReplacementConfirmationMessage(providerLabel(provider), model)}
          </p>
          <div className="mt-3 flex gap-2">
            <button
              type="button"
              onClick={() => setIsConfirmingInstructionReplacement(false)}
              className="rounded-lg border border-border px-3 py-2 text-sm font-semibold text-text-body"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={() => void handleGenerateInstructions()}
              disabled={isGeneratingInstructions}
              className="rounded-lg bg-action-primary px-3 py-2 text-sm font-semibold text-action-primary-foreground hover:bg-action-primary-hover disabled:opacity-50"
            >
              Regenerate
            </button>
          </div>
        </div>
      ) : null}
      {message ? <p role="status" className="mt-2 text-xs text-positive-foreground-strong">{message}</p> : null}
      {error ? <p role="alert" className="mt-2 text-xs text-danger-foreground">{error}</p> : null}
    </article>
  );
}

function providerLabel(provider: MealIdeaProvider) {
  return provider === "local" ? "Local" : "OpenAI";
}

function steeringLabel(steering: MealIdeaSteering) {
  return STEERING_OPTIONS.find((option) => option.value === steering)?.label ?? steering;
}

function mealTypeLabel(mealType: MealIdeaMealType) {
  return MEAL_TYPES.find((option) => option.value === mealType)?.label ?? mealType;
}

function formatGenerationTime(value: string) {
  const normalized = value.includes("T") ? value : `${value.replace(" ", "T")}Z`;
  const parsed = new Date(normalized);
  if (Number.isNaN(parsed.getTime())) return value;
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(parsed);
}

function optionStillAvailable(
  options: MealIdeaModelOptionsResponse,
  provider: MealIdeaProvider,
  selected: string,
) {
  return options.providers[provider].models.some((option) => option.id === selected);
}

function appendBoundedExposure(
  current: string[],
  additions: string[],
  limit: number,
) {
  const uniqueAdditions = Array.from(new Set(additions));
  const additionSet = new Set(uniqueAdditions);
  return [...current.filter((value) => !additionSet.has(value)), ...uniqueAdditions].slice(
    -limit,
  );
}

function generationNonce() {
  return typeof crypto !== "undefined" && "randomUUID" in crypto
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random()}`;
}
