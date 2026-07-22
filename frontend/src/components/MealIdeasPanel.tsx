"use client";

import { FormEvent, useEffect, useRef, useState } from "react";

import {
  fetchMealIdeaModelOptions,
  generateMealIdeas,
} from "@/lib/mealIdeasApi";
import {
  GroundedMealIdea,
  MealIdeaMealType,
  MealIdeaModelOptionsResponse,
  MealIdeaProvider,
  MealIdeaSteering,
  MealIdeasResponse,
} from "@/types/mealIdea";

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
      setResult(response);
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
      <div>
        <div className="flex flex-wrap items-center justify-between gap-2">
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

      {error ? (
        <div role="alert" className="rounded-xl bg-danger-surface px-3 py-2.5 text-sm text-danger-foreground">
          {error}
        </div>
      ) : null}

      {result ? (
        <div className="space-y-3" aria-live="polite">
          <div className="grid gap-3 md:grid-cols-2">
            {result.ideas.map((idea) => (
              <MealIdeaCard key={`${idea.name}:${idea.meal_type}`} idea={idea} />
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

function MealIdeaCard({ idea }: { idea: GroundedMealIdea }) {
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
              {formatAmount(ingredient.amount_grams)} g
            </span>
          </li>
        ))}
      </ul>

      <p className="mt-3 border-t border-border-subtle pt-2.5 text-xs font-semibold text-text-body">
        {Math.round(idea.calories)} cal · {Math.round(idea.protein_g)}P ·{" "}
        {Math.round(idea.carbs_g)}C · {Math.round(idea.fat_g)}F
      </p>
    </article>
  );
}

function providerLabel(provider: MealIdeaProvider) {
  return provider === "local" ? "Local" : "OpenAI";
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

function formatAmount(value: number) {
  return Number.isInteger(value) ? String(value) : value.toFixed(1);
}
