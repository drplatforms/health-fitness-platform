"use client";

import { useDeferredValue, useEffect, useMemo, useState, useTransition } from "react";
import { useRouter } from "next/navigation";

import { TodayCard } from "@/components/TodayCard";
import { logCanonicalFood, searchCanonicalFoods } from "@/lib/canonicalFoodApi";
import {
  CanonicalFoodNutrientSummary,
  CanonicalFoodSearchResult,
} from "@/types/canonicalFood";

interface FoodLoggingCardProps {
  userId: number;
  targetDate: string;
  className?: string;
}

const MEAL_OPTIONS = [
  { label: "Any time", value: "" },
  { label: "Breakfast", value: "breakfast" },
  { label: "Lunch", value: "lunch" },
  { label: "Dinner", value: "dinner" },
  { label: "Snack", value: "snack" },
] as const;

function formatCompactNumber(value: number, suffix = ""): string {
  const normalized =
    Math.abs(value % 1) < 0.001 ? String(Math.round(value)) : value.toFixed(1);
  return `${normalized}${suffix}`;
}

function formatMacroLine(summary?: CanonicalFoodNutrientSummary): string {
  if (!summary) {
    return "Nutrition details are limited for this food.";
  }

  const parts: string[] = [];

  if (summary.calories_per_100g !== undefined) {
    parts.push(`${formatCompactNumber(summary.calories_per_100g)} cal`);
  }
  if (summary.protein_g_per_100g !== undefined) {
    parts.push(`${formatCompactNumber(summary.protein_g_per_100g)}g protein`);
  }
  if (summary.carbohydrate_g_per_100g !== undefined) {
    parts.push(`${formatCompactNumber(summary.carbohydrate_g_per_100g)}g carbs`);
  }
  if (summary.fat_g_per_100g !== undefined) {
    parts.push(`${formatCompactNumber(summary.fat_g_per_100g)}g fat`);
  }

  return parts.length > 0
    ? `${parts.join(" · ")} per 100g`
    : "Nutrition details are limited for this food.";
}

function scaleNutrient(
  value: number | undefined,
  grams: number,
): number | null {
  if (value === undefined) {
    return null;
  }

  return (value * grams) / 100;
}

export function FoodLoggingCard({
  userId,
  targetDate,
  className,
}: FoodLoggingCardProps) {
  const router = useRouter();
  const [isRefreshing, startRefresh] = useTransition();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<CanonicalFoodSearchResult[]>([]);
  const [selectedFood, setSelectedFood] = useState<CanonicalFoodSearchResult | null>(
    null,
  );
  const [grams, setGrams] = useState("50");
  const [mealType, setMealType] = useState("snack");
  const [isSearching, setIsSearching] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [searchMessage, setSearchMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const deferredQuery = useDeferredValue(query.trim());

  useEffect(() => {
    if (!deferredQuery) {
      return;
    }

    if (deferredQuery.length < 2) {
      return;
    }

    let isActive = true;
    const timeoutId = window.setTimeout(async () => {
      setIsSearching(true);
      setSearchMessage(null);

      try {
        const response = await searchCanonicalFoods(deferredQuery, 8);

        if (!isActive) {
          return;
        }

        setResults(response.results);
        setSearchMessage(
          response.results.length > 0 ? null : "No matching foods found.",
        );
      } catch (error) {
        if (!isActive) {
          return;
        }

        setResults([]);
        setSearchMessage(
          error instanceof Error
            ? error.message
            : "Unable to search foods right now.",
        );
      } finally {
        if (isActive) {
          setIsSearching(false);
        }
      }
    }, 250);

    return () => {
      isActive = false;
      window.clearTimeout(timeoutId);
    };
  }, [deferredQuery]);

  const gramsValue = Number.parseFloat(grams);
  const gramsIsValid = Number.isFinite(gramsValue) && gramsValue > 0;

  const preview = useMemo(() => {
    if (!selectedFood || !gramsIsValid) {
      return null;
    }

    const summary = selectedFood.nutrient_summary;
    const calories = scaleNutrient(summary?.calories_per_100g, gramsValue);
    const protein = scaleNutrient(summary?.protein_g_per_100g, gramsValue);
    const carbs = scaleNutrient(summary?.carbohydrate_g_per_100g, gramsValue);
    const fat = scaleNutrient(summary?.fat_g_per_100g, gramsValue);

    const parts: string[] = [];
    if (calories !== null) {
      parts.push(`${formatCompactNumber(calories)} cal`);
    }
    if (protein !== null) {
      parts.push(`${formatCompactNumber(protein)}g protein`);
    }
    if (carbs !== null) {
      parts.push(`${formatCompactNumber(carbs)}g carbs`);
    }
    if (fat !== null) {
      parts.push(`${formatCompactNumber(fat)}g fat`);
    }

    return parts.length > 0 ? parts.join(" · ") : "Nutrition preview unavailable.";
  }, [gramsIsValid, gramsValue, selectedFood]);

  async function handleLogFood() {
    if (!selectedFood) {
      setErrorMessage("Choose a food before logging it.");
      return;
    }

    if (!gramsIsValid) {
      setErrorMessage("Enter grams greater than 0 before logging.");
      return;
    }

    setIsSaving(true);
    setErrorMessage(null);
    setActionMessage(null);

    try {
      const response = await logCanonicalFood({
        user_id: userId,
        entry_date: targetDate,
        canonical_food_id: selectedFood.canonical_food_id,
        grams: gramsValue,
        meal_type: mealType || undefined,
      });

      setActionMessage(
        `Logged ${formatCompactNumber(response.grams)}g ${response.display_name}.`,
      );
      setGrams("50");
      startRefresh(() => {
        router.refresh();
      });
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "Unable to log this food right now.",
      );
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <TodayCard title="Log Food" className={className}>
      <div className="space-y-4">
        <div className="space-y-2">
          <label className="text-sm font-semibold text-slate-900" htmlFor="food-search">
            Search foods
          </label>
          <input
            id="food-search"
            type="search"
            value={query}
            onChange={(event) => {
              const nextQuery = event.target.value;
              const trimmedQuery = nextQuery.trim();

              setQuery(nextQuery);
              setIsSearching(false);
              setErrorMessage(null);
              setActionMessage(null);

              if (trimmedQuery.length < 2) {
                setResults([]);
                setSearchMessage(
                  trimmedQuery.length === 0
                    ? null
                    : "Type at least 2 characters to search foods.",
                );
                return;
              }

              setSearchMessage(null);
            }}
            placeholder="Search food..."
            className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-emerald-500"
          />
        </div>

        {isSearching ? (
          <p className="rounded-2xl bg-slate-50 px-4 py-3 text-sm text-slate-700">
            Searching foods...
          </p>
        ) : null}

        {!isSearching && searchMessage ? (
          <p className="rounded-2xl bg-slate-50 px-4 py-3 text-sm text-slate-700">
            {searchMessage}
          </p>
        ) : null}

        {results.length > 0 ? (
          <div className="space-y-2">
            {results.map((food) => {
              const isSelected =
                selectedFood?.canonical_food_id === food.canonical_food_id;

              return (
                <button
                  key={food.canonical_food_id}
                  type="button"
                  onClick={() => {
                    setSelectedFood(food);
                    setActionMessage(null);
                    setErrorMessage(null);
                  }}
                  className={`w-full rounded-[22px] border px-4 py-3 text-left transition ${
                    isSelected
                      ? "border-emerald-700 bg-emerald-50"
                      : "border-slate-200 bg-slate-50 hover:border-emerald-300 hover:bg-white"
                  }`}
                >
                  <p className="text-sm font-semibold text-slate-950">
                    {food.display_name}
                  </p>
                  <p className="mt-1 text-sm leading-6 text-slate-700">
                    {formatMacroLine(food.nutrient_summary)}
                  </p>
                </button>
              );
            })}
          </div>
        ) : null}

        {selectedFood ? (
          <div className="space-y-4 rounded-[24px] bg-slate-50 px-4 py-4">
            <div className="space-y-1">
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
                Selected Food
              </p>
              <p className="text-base font-semibold text-slate-950">
                {selectedFood.display_name}
              </p>
              <p className="text-sm leading-6 text-slate-700">
                {formatMacroLine(selectedFood.nutrient_summary)}
              </p>
            </div>

            <div className="grid gap-3 sm:grid-cols-[minmax(0,1fr)_180px]">
              <label className="space-y-2">
                <span className="text-sm font-semibold text-slate-900">Amount</span>
                <div className="flex items-center gap-2">
                  <input
                    type="number"
                    min="1"
                    step="1"
                    value={grams}
                    onChange={(event) => {
                      setGrams(event.target.value);
                      setActionMessage(null);
                      setErrorMessage(null);
                    }}
                    className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-emerald-500"
                  />
                  <span className="text-sm font-semibold text-slate-600">g</span>
                </div>
              </label>

              <label className="space-y-2">
                <span className="text-sm font-semibold text-slate-900">Meal</span>
                <select
                  value={mealType}
                  onChange={(event) => {
                    setMealType(event.target.value);
                    setActionMessage(null);
                    setErrorMessage(null);
                  }}
                  className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-emerald-500"
                >
                  {MEAL_OPTIONS.map((option) => (
                    <option key={option.value || "any"} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            <div className="rounded-2xl bg-white px-4 py-3">
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
                For {gramsIsValid ? formatCompactNumber(gramsValue) : "--"}g
              </p>
              <p className="mt-2 text-sm font-semibold text-slate-900">
                {preview ?? "Enter grams to preview this food."}
              </p>
            </div>

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
              onClick={() => void handleLogFood()}
              disabled={isSaving || isRefreshing}
              className="inline-flex w-full items-center justify-center rounded-2xl bg-emerald-900 px-4 py-3 text-sm font-semibold text-emerald-50 transition hover:bg-emerald-800 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isSaving ? "Logging food..." : isRefreshing ? "Updating nutrition..." : "Log food"}
            </button>
          </div>
        ) : null}
      </div>
    </TodayCard>
  );
}
