"use client";

import {
  useCallback,
  useDeferredValue,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import Link from "next/link";

import { TodayCard } from "@/components/TodayCard";
import {
  fetchCanonicalFoodServingUnits,
  fetchRecentCanonicalFoods,
  logCanonicalFood,
  searchCanonicalFoods,
} from "@/lib/canonicalFoodApi";
import { logPersonalFood, searchPersonalFoods } from "@/lib/personalFoodApi";
import {
  CANONICAL_FOOD_LOGGED_EVENT,
  CanonicalFoodNutrientSummary,
  CanonicalFoodSearchResult,
  CanonicalFoodServingUnit,
  RecentCanonicalFood,
} from "@/types/canonicalFood";
import {
  PERSONAL_FOOD_LOGGED_EVENT,
  PersonalFood,
  personalFoodNutrientSummary,
} from "@/types/personalFood";

interface FoodLoggingCardProps {
  userId: number;
  targetDate: string;
  className?: string;
  variant?: "card" | "embedded";
}

const MEAL_OPTIONS = [
  { label: "Any time", value: "" },
  { label: "Breakfast", value: "breakfast" },
  { label: "Lunch", value: "lunch" },
  { label: "Dinner", value: "dinner" },
  { label: "Snack", value: "snack" },
] as const;

interface PendingRecentContext {
  canonicalFoodId: number;
  grams: number;
  mealType: string | null;
  servingUnitId?: number;
  quantity?: number;
}

interface LoggingFoodResult {
  key: string;
  foodType: "canonical" | "personal";
  displayName: string;
  nutrientSummary?: CanonicalFoodNutrientSummary;
  defaultGrams: number | null;
  canonicalFoodId?: number;
  personalFoodId?: number;
  servingName?: string | null;
  servingGrams?: number | null;
}

function formatCompactNumber(value: number, suffix = ""): string {
  const normalized =
    Math.abs(value % 1) < 0.001 ? String(Math.round(value)) : value.toFixed(1);
  return `${normalized}${suffix}`;
}

function formatRecentAmount(food: RecentCanonicalFood): string {
  if (food.last_serving_unit_label) {
    return food.last_serving_unit_label;
  }

  return `${formatCompactNumber(food.last_grams)}g`;
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

function canonicalFoodToLoggingResult(
  food: CanonicalFoodSearchResult,
): LoggingFoodResult {
  return {
    key: `canonical:${food.canonical_food_id}`,
    foodType: "canonical",
    displayName: food.display_name,
    nutrientSummary: food.nutrient_summary,
    defaultGrams: food.default_grams,
    canonicalFoodId: food.canonical_food_id,
  };
}

function personalFoodToLoggingResult(food: PersonalFood): LoggingFoodResult {
  return {
    key: `personal:${food.id}`,
    foodType: "personal",
    displayName: food.display_name,
    nutrientSummary: personalFoodNutrientSummary(food),
    defaultGrams: food.current_revision.serving_grams,
    personalFoodId: food.id,
    servingName: food.current_revision.serving_name,
    servingGrams: food.current_revision.serving_grams,
  };
}

function recentFoodToLoggingResult(food: RecentCanonicalFood): LoggingFoodResult {
  return {
    key: `canonical:${food.canonical_food_id}`,
    foodType: "canonical",
    displayName: food.display_name,
    defaultGrams: food.last_grams,
    canonicalFoodId: food.canonical_food_id,
  };
}

export function FoodLoggingCard({
  userId,
  targetDate,
  className,
  variant = "card",
}: FoodLoggingCardProps) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<LoggingFoodResult[]>([]);
  const [recentFoods, setRecentFoods] = useState<RecentCanonicalFood[]>([]);
  const [selectedFood, setSelectedFood] = useState<LoggingFoodResult | null>(null);
  const pendingRecentContextRef = useRef<PendingRecentContext | null>(null);
  const [selectedSearchQuery, setSelectedSearchQuery] = useState("");
  const [amount, setAmount] = useState("50");
  const [servingUnits, setServingUnits] = useState<CanonicalFoodServingUnit[]>([]);
  const [selectedUnitKey, setSelectedUnitKey] = useState("grams");
  const [mealType, setMealType] = useState("snack");
  const [isSearching, setIsSearching] = useState(false);
  const [isLoadingRecentFoods, setIsLoadingRecentFoods] = useState(true);
  const [isLoadingServingUnits, setIsLoadingServingUnits] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [searchMessage, setSearchMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const deferredQuery = useDeferredValue(query.trim());

  const refreshRecentFoods = useCallback(async () => {
    setIsLoadingRecentFoods(true);

    try {
      const response = await fetchRecentCanonicalFoods({ userId, limit: 10 });
      setRecentFoods(response.results);
    } catch {
      setRecentFoods([]);
    } finally {
      setIsLoadingRecentFoods(false);
    }
  }, [userId]);

  useEffect(() => {
    let isActive = true;

    void fetchRecentCanonicalFoods({ userId, limit: 10 })
      .then((response) => {
        if (isActive) {
          setRecentFoods(response.results);
        }
      })
      .catch(() => {
        if (isActive) {
          setRecentFoods([]);
        }
      })
      .finally(() => {
        if (isActive) {
          setIsLoadingRecentFoods(false);
        }
      });

    return () => {
      isActive = false;
    };
  }, [userId]);

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
        const [canonicalResult, personalResult] = await Promise.allSettled([
          searchCanonicalFoods(deferredQuery, 8),
          searchPersonalFoods(userId, deferredQuery, 8),
        ]);

        if (!isActive) {
          return;
        }

        if (
          canonicalResult.status === "rejected" &&
          personalResult.status === "rejected"
        ) {
          setResults([]);
          setSearchMessage("Unable to search foods right now.");
          return;
        }

        const normalizedQuery = deferredQuery.toLocaleLowerCase();
        const personalResults =
          personalResult.status === "fulfilled"
            ? personalResult.value.results.map(personalFoodToLoggingResult)
            : [];
        const exactPersonal = personalResults.filter(
          (food) => food.displayName.toLocaleLowerCase() === normalizedQuery,
        );
        const remainingPersonal = personalResults.filter(
          (food) => food.displayName.toLocaleLowerCase() !== normalizedQuery,
        );
        const mergedResults = [
          ...exactPersonal,
          ...(canonicalResult.status === "fulfilled"
            ? canonicalResult.value.results.map(canonicalFoodToLoggingResult)
            : []),
          ...remainingPersonal,
        ];
        setResults(mergedResults);
        setSearchMessage(
          mergedResults.length > 0 ? null : "No matching foods found.",
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
  }, [deferredQuery, userId]);

  useEffect(() => {
    if (!selectedFood) {
      return;
    }

    if (selectedFood.foodType === "personal") {
      pendingRecentContextRef.current = null;
      return;
    }

    let isActive = true;

    void fetchCanonicalFoodServingUnits(selectedFood.canonicalFoodId as number)
      .then((response) => {
        if (!isActive) {
          return;
        }

        const units = response.serving_units;
        setServingUnits(units);
        const recentContext =
          pendingRecentContextRef.current?.canonicalFoodId ===
          selectedFood.canonicalFoodId
            ? pendingRecentContextRef.current
            : null;

        if (recentContext) {
          const recentServingUnit = units.find(
            (unit) => unit.serving_unit_id === recentContext.servingUnitId,
          );

          if (recentServingUnit && recentContext.quantity !== undefined) {
            setSelectedUnitKey(String(recentServingUnit.serving_unit_id));
            setAmount(String(recentContext.quantity));
          } else {
            setSelectedUnitKey("grams");
            setAmount(String(recentContext.grams));
          }

          setMealType(recentContext.mealType ?? "");
          pendingRecentContextRef.current = null;
          return;
        }

        const defaultUnit = units.find((unit) => unit.is_default) ?? units[0];

        if (defaultUnit) {
          setSelectedUnitKey(String(defaultUnit.serving_unit_id));
          setAmount("1");
        } else {
          setSelectedUnitKey("grams");
          setAmount(String(selectedFood.defaultGrams ?? 50));
        }
      })
      .catch(() => {
        if (!isActive) {
          return;
        }

        const recentContext =
          pendingRecentContextRef.current?.canonicalFoodId ===
          selectedFood.canonicalFoodId
            ? pendingRecentContextRef.current
            : null;
        setServingUnits([]);
        setSelectedUnitKey("grams");
        setAmount(String(recentContext?.grams ?? selectedFood.defaultGrams ?? 50));
        pendingRecentContextRef.current = null;
      })
      .finally(() => {
        if (isActive) {
          setIsLoadingServingUnits(false);
        }
      });

    return () => {
      isActive = false;
    };
  }, [selectedFood]);

  function handleSelectRecentFood(food: RecentCanonicalFood) {
    const selectedRecentFood = recentFoodToLoggingResult(food);

    setServingUnits([]);
    setSelectedUnitKey("grams");
    setAmount(String(food.last_grams));
    setMealType(food.last_meal_type ?? "");
    pendingRecentContextRef.current = {
      canonicalFoodId: food.canonical_food_id,
      grams: food.last_grams,
      mealType: food.last_meal_type,
      servingUnitId: food.last_serving_unit_id,
      quantity: food.last_quantity,
    };
    setIsLoadingServingUnits(true);
    setSelectedFood(selectedRecentFood);
    setSelectedSearchQuery(food.display_name);
    setQuery(food.display_name);
    setResults([]);
    setSearchMessage(null);
    setErrorMessage(null);
  }

  const amountValue = Number.parseFloat(amount);
  const amountIsValid = Number.isFinite(amountValue) && amountValue > 0;
  const selectedServingUnit = useMemo(
    () =>
      selectedUnitKey === "grams" || selectedUnitKey === "personal-serving"
        ? null
        : (servingUnits.find(
            (unit) => String(unit.serving_unit_id) === selectedUnitKey,
          ) ?? null),
    [selectedUnitKey, servingUnits],
  );
  const usesPersonalServing =
    selectedUnitKey === "personal-serving" &&
    selectedFood?.foodType === "personal" &&
    selectedFood.servingGrams !== null &&
    selectedFood.servingGrams !== undefined;
  const resolvedGrams =
    selectedServingUnit !== null
      ? amountValue * selectedServingUnit.grams_per_unit
      : usesPersonalServing
        ? amountValue * (selectedFood.servingGrams as number)
        : amountValue;
  const resolvedGramsIsValid =
    amountIsValid && Number.isFinite(resolvedGrams) && resolvedGrams <= 5_000;
  const searchChangedAfterSelection =
    selectedFood !== null && query.trim() !== selectedSearchQuery;
  const shouldShowResults =
    results.length > 0 && (!selectedFood || searchChangedAfterSelection);

  const preview = useMemo(() => {
    if (!selectedFood || !resolvedGramsIsValid) {
      return null;
    }

    const summary = selectedFood.nutrientSummary;
    const calories = scaleNutrient(summary?.calories_per_100g, resolvedGrams);
    const protein = scaleNutrient(summary?.protein_g_per_100g, resolvedGrams);
    const carbs = scaleNutrient(summary?.carbohydrate_g_per_100g, resolvedGrams);
    const fat = scaleNutrient(summary?.fat_g_per_100g, resolvedGrams);

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
  }, [resolvedGrams, resolvedGramsIsValid, selectedFood]);

  async function handleLogFood() {
    if (!selectedFood) {
      setErrorMessage("Choose a food before logging it.");
      return;
    }

    if (!resolvedGramsIsValid) {
      setErrorMessage("Enter an amount greater than 0 before logging.");
      return;
    }

    setIsSaving(true);
    setErrorMessage(null);

    try {
      if (selectedFood.foodType === "personal") {
        await logPersonalFood({
          user_id: userId,
          entry_date: targetDate,
          personal_food_id: selectedFood.personalFoodId as number,
          meal_type: mealType || undefined,
          ...(usesPersonalServing
            ? { serving_quantity: amountValue }
            : { grams: resolvedGrams }),
        });
        window.dispatchEvent(new CustomEvent(PERSONAL_FOOD_LOGGED_EVENT));
      } else {
        await logCanonicalFood({
          user_id: userId,
          entry_date: targetDate,
          canonical_food_id: selectedFood.canonicalFoodId as number,
          meal_type: mealType || undefined,
          ...(selectedServingUnit
            ? {
                serving_unit_id: selectedServingUnit.serving_unit_id,
                quantity: amountValue,
              }
            : { grams: resolvedGrams }),
        });
        void refreshRecentFoods();
        window.dispatchEvent(new CustomEvent(CANONICAL_FOOD_LOGGED_EVENT));
      }
      pendingRecentContextRef.current = null;
      setSelectedFood(null);
      setSelectedSearchQuery("");
      setQuery("");
      setResults([]);
      setServingUnits([]);
      setSelectedUnitKey("grams");
      setAmount("50");
      setIsLoadingServingUnits(false);
      setSearchMessage(null);
      setErrorMessage(null);
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

  const content = (
    <div className="space-y-3">
      {variant === "card" ? (
        <div className="flex justify-end">
          <Link
            href={`/personal-foods?${new URLSearchParams({
              user_id: String(userId),
              date: targetDate,
            }).toString()}`}
            className="text-sm font-semibold !text-accent-text transition hover:!text-accent-text-hover"
          >
            My Foods
          </Link>
        </div>
      ) : null}
        {recentFoods.length > 0 ? (
          <div className="space-y-2">
            <p className="text-sm font-semibold text-text-primary">Recent foods</p>
            <div className="flex snap-x snap-proximity flex-nowrap gap-2 overflow-x-auto pb-1">
              {recentFoods.map((food) => (
                <button
                  key={food.canonical_food_id}
                  type="button"
                  onClick={() => handleSelectRecentFood(food)}
                  className="shrink-0 snap-start rounded-xl border border-border bg-surface px-3 py-2 text-left text-xs text-text-body transition hover:border-border-accent hover:bg-surface-highlighted"
                >
                  <span className="font-semibold text-text-strong">
                    {food.display_name}
                  </span>
                  <span className="text-text-muted">
                    {" "}· {formatRecentAmount(food)}
                  </span>
                </button>
              ))}
            </div>
          </div>
        ) : null}

        {isLoadingRecentFoods && recentFoods.length === 0 ? (
          <p className="rounded-2xl bg-surface-subtle px-4 py-3 text-sm text-text-body">
            Loading recent foods...
          </p>
        ) : null}

        <div className="space-y-2">
          <label className="text-sm font-semibold text-text-primary" htmlFor="food-search">
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
            className="w-full rounded-2xl border border-border bg-surface px-4 py-2.5 text-sm text-text-primary outline-none transition focus:border-focus"
          />
        </div>

        {isSearching ? (
          <p className="rounded-2xl bg-surface-subtle px-4 py-3 text-sm text-text-body">
            Searching foods...
          </p>
        ) : null}

        {!isSearching && searchMessage ? (
          <p className="rounded-2xl bg-surface-subtle px-4 py-3 text-sm text-text-body">
            {searchMessage}
          </p>
        ) : null}

        {shouldShowResults ? (
          <div className="max-h-64 space-y-1 overflow-y-auto rounded-2xl border border-border bg-surface p-1">
            {results.map((food) => {
              const isSelected = selectedFood?.key === food.key;

              return (
                <button
                  key={food.key}
                  type="button"
                  onClick={() => {
                    const isSameSelection = selectedFood?.key === food.key;
                    if (!isSameSelection) {
                      pendingRecentContextRef.current = null;
                      setServingUnits([]);
                      if (food.foodType === "personal") {
                        setSelectedUnitKey(
                          food.servingGrams ? "personal-serving" : "grams",
                        );
                        setAmount(
                          food.servingGrams
                            ? "1"
                            : String(food.defaultGrams ?? 50),
                        );
                        setIsLoadingServingUnits(false);
                      } else {
                        setSelectedUnitKey("grams");
                        setAmount("50");
                        setIsLoadingServingUnits(true);
                      }
                    }
                    setSelectedFood(food);
                    setSelectedSearchQuery(query.trim());
                    setErrorMessage(null);
                  }}
                  className={`w-full rounded-xl px-3 py-2 text-left transition ${
                    isSelected
                      ? "bg-surface-highlighted"
                      : "hover:bg-surface-subtle"
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-semibold text-text-strong">
                      {food.displayName}
                    </p>
                    {food.foodType === "personal" ? (
                      <span className="rounded-full bg-positive-surface px-2 py-0.5 text-[0.68rem] font-semibold text-positive-foreground">
                        My food
                      </span>
                    ) : null}
                  </div>
                  <p className="mt-0.5 text-xs leading-4 text-text-secondary">
                    {formatMacroLine(food.nutrientSummary)}
                  </p>
                </button>
              );
            })}
          </div>
        ) : null}

        {selectedFood ? (
          <div className="space-y-2.5 rounded-[20px] bg-surface-subtle px-3 py-3 sm:px-4">
            <div className="grid gap-1">
              <p className="text-sm font-semibold text-text-strong">
                {selectedFood.displayName}
              </p>
              <p className="text-xs leading-4 text-text-secondary">
                {preview ?? "Enter an amount to preview this food."}
              </p>
            </div>

            <div className="grid grid-cols-[minmax(4.5rem,0.75fr)_minmax(0,1.2fr)_minmax(0,1fr)] gap-2">
              <label className="min-w-0 space-y-1">
                <span className="text-xs font-semibold text-text-primary">Amount</span>
                <input
                  type="number"
                  min="0"
                  step={selectedUnitKey === "grams" ? "1" : "0.25"}
                  value={amount}
                  onChange={(event) => {
                    setAmount(event.target.value);
                    setErrorMessage(null);
                  }}
                  className="min-h-11 w-full min-w-0 rounded-xl border border-border bg-surface px-3 py-2 text-sm text-text-primary outline-none transition focus:border-focus"
                />
              </label>

              <label className="min-w-0 space-y-1">
                <span className="text-xs font-semibold text-text-primary">Unit</span>
                <select
                  value={selectedUnitKey}
                  disabled={isLoadingServingUnits}
                  onChange={(event) => {
                    const nextUnitKey = event.target.value;
                    setSelectedUnitKey(nextUnitKey);
                    setAmount(nextUnitKey === "grams" ? "50" : "1");
                    setErrorMessage(null);
                  }}
                  className="min-h-11 w-full min-w-0 rounded-xl border border-border bg-surface px-2 py-2 text-sm text-text-primary outline-none transition focus:border-focus disabled:opacity-70"
                >
                  <option value="grams">grams</option>
                  {selectedFood.foodType === "personal" && selectedFood.servingGrams ? (
                    <option value="personal-serving">
                      {selectedFood.servingName || "serving"}
                    </option>
                  ) : null}
                  {servingUnits.map((unit) => (
                    <option key={unit.serving_unit_id} value={String(unit.serving_unit_id)}>
                      {unit.display_label}
                    </option>
                  ))}
                </select>
              </label>

              <label className="min-w-0 space-y-1">
                <span className="text-xs font-semibold text-text-primary">Meal</span>
                <select
                  value={mealType}
                  onChange={(event) => {
                    setMealType(event.target.value);
                    setErrorMessage(null);
                  }}
                  className="min-h-11 w-full min-w-0 rounded-xl border border-border bg-surface px-2 py-2 text-sm text-text-primary outline-none transition focus:border-focus"
                >
                  {MEAL_OPTIONS.map((option) => (
                    <option key={option.value || "any"} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            <p className="text-xs leading-4 text-text-secondary">
              {isLoadingServingUnits
                ? "Loading serving units..."
                : resolvedGramsIsValid
                  ? `≈ ${formatCompactNumber(resolvedGrams)}g`
                  : resolvedGrams > 5_000
                    ? "Resolved amount must be 5,000g or less."
                    : "Enter an amount to resolve grams."}
            </p>
            {errorMessage ? (
              <p className="rounded-2xl bg-danger-surface px-4 py-2.5 text-sm text-danger-foreground">
                {errorMessage}
              </p>
            ) : null}

            <button
              type="button"
              onClick={() => void handleLogFood()}
              disabled={isSaving}
              className="inline-flex w-full items-center justify-center rounded-2xl bg-action-primary px-4 py-2.5 text-sm font-semibold text-action-primary-foreground transition hover:bg-action-primary-hover disabled:cursor-not-allowed disabled:opacity-60 sm:w-auto"
            >
              {isSaving ? "Logging food..." : "Log food"}
            </button>
          </div>
        ) : null}
    </div>
  );

  if (variant === "embedded") {
    return <div className={className}>{content}</div>;
  }

  return (
    <TodayCard title="Log Food" className={className}>
      {content}
    </TodayCard>
  );
}
