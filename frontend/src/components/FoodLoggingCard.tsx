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

function formatMealLabel(value: string | null | undefined): string {
  if (!value) {
    return "Any time";
  }

  const normalized = value.replace("_", " ");
  return normalized.charAt(0).toUpperCase() + normalized.slice(1);
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
  const [actionMessage, setActionMessage] = useState<string | null>(null);
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
    setActionMessage(null);
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
    setActionMessage(null);

    try {
      if (selectedFood.foodType === "personal") {
        const response = await logPersonalFood({
          user_id: userId,
          entry_date: targetDate,
          personal_food_id: selectedFood.personalFoodId as number,
          meal_type: mealType || undefined,
          ...(usesPersonalServing
            ? { serving_quantity: amountValue }
            : { grams: resolvedGrams }),
        });
        setActionMessage(
          `Logged ${formatCompactNumber(response.grams)}g ${response.display_name}.`,
        );
        window.dispatchEvent(new CustomEvent(PERSONAL_FOOD_LOGGED_EVENT));
      } else {
        const response = await logCanonicalFood({
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
        setActionMessage(
          `Logged ${formatCompactNumber(response.grams)}g ${response.display_name}.`,
        );
        void refreshRecentFoods();
        window.dispatchEvent(new CustomEvent(CANONICAL_FOOD_LOGGED_EVENT));
      }
      setAmount(selectedUnitKey === "grams" ? "50" : "1");
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
            className="text-sm font-semibold text-emerald-800 transition hover:text-emerald-950"
          >
            My Foods
          </Link>
        </div>
      ) : null}
        {recentFoods.length > 0 ? (
          <div className="space-y-2">
            <p className="text-sm font-semibold text-slate-900">Recent foods</p>
            <div className="flex flex-wrap gap-2">
              {recentFoods.map((food) => (
                <button
                  key={food.canonical_food_id}
                  type="button"
                  onClick={() => handleSelectRecentFood(food)}
                  className="max-w-full rounded-2xl border border-slate-200 bg-white px-3 py-2 text-left text-xs leading-5 text-slate-700 transition hover:border-emerald-300 hover:bg-emerald-50"
                >
                  <span className="font-semibold text-slate-950">
                    {food.display_name}
                  </span>
                  <span className="text-slate-500">
                    {" "}
                    · {formatRecentAmount(food)} ·{" "}
                    {formatMealLabel(food.last_meal_type)}
                  </span>
                </button>
              ))}
            </div>
          </div>
        ) : null}

        {isLoadingRecentFoods && recentFoods.length === 0 ? (
          <p className="rounded-2xl bg-slate-50 px-4 py-3 text-sm text-slate-700">
            Loading recent foods...
          </p>
        ) : null}

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
            className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-900 outline-none transition focus:border-emerald-500"
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

        {shouldShowResults ? (
          <div className="space-y-2">
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
                    setActionMessage(null);
                    setErrorMessage(null);
                  }}
                  className={`w-full rounded-[20px] border px-4 py-2.5 text-left transition ${
                    isSelected
                      ? "border-emerald-700 bg-emerald-50"
                      : "border-slate-200 bg-slate-50 hover:border-emerald-300 hover:bg-white"
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-semibold text-slate-950">
                      {food.displayName}
                    </p>
                    {food.foodType === "personal" ? (
                      <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-[0.68rem] font-semibold text-emerald-800">
                        My food
                      </span>
                    ) : null}
                  </div>
                  <p className="mt-1 text-sm leading-6 text-slate-700">
                    {formatMacroLine(food.nutrientSummary)}
                  </p>
                </button>
              );
            })}
          </div>
        ) : null}

        {selectedFood ? (
          <div className="space-y-3 rounded-[22px] bg-slate-50 px-4 py-3">
            <div className="grid gap-1">
              <p className="text-sm font-semibold text-slate-950">
                Selected: {selectedFood.displayName}
              </p>
              <p className="text-xs leading-5 text-slate-600">
                {formatMacroLine(selectedFood.nutrientSummary)}
              </p>
            </div>

            <div className="grid gap-3 sm:grid-cols-[minmax(0,1fr)_180px]">
              <label className="space-y-2">
                <span className="text-sm font-semibold text-slate-900">Amount</span>
                <div className="grid gap-2 sm:grid-cols-[minmax(0,1fr)_180px]">
                  <input
                    type="number"
                    min="0"
                    step={selectedUnitKey === "grams" ? "1" : "0.25"}
                    value={amount}
                    onChange={(event) => {
                      setAmount(event.target.value);
                      setActionMessage(null);
                      setErrorMessage(null);
                    }}
                    className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-900 outline-none transition focus:border-emerald-500"
                  />
                  <select
                    value={selectedUnitKey}
                    disabled={isLoadingServingUnits}
                    onChange={(event) => {
                      const nextUnitKey = event.target.value;
                      setSelectedUnitKey(nextUnitKey);
                      setAmount(nextUnitKey === "grams" ? "50" : "1");
                      setActionMessage(null);
                      setErrorMessage(null);
                    }}
                    className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-900 outline-none transition focus:border-emerald-500 disabled:opacity-70"
                  >
                    <option value="grams">grams</option>
                    {selectedFood.foodType === "personal" &&
                    selectedFood.servingGrams ? (
                      <option value="personal-serving">
                        {selectedFood.servingName || "serving"}
                      </option>
                    ) : null}
                    {servingUnits.map((unit) => (
                      <option
                        key={unit.serving_unit_id}
                        value={String(unit.serving_unit_id)}
                      >
                        {unit.display_label}
                      </option>
                    ))}
                  </select>
                </div>
                <span className="block text-xs leading-5 text-slate-600">
                  {isLoadingServingUnits
                    ? "Loading serving units..."
                    : resolvedGramsIsValid
                      ? `≈ ${formatCompactNumber(resolvedGrams)}g`
                      : resolvedGrams > 5_000
                        ? "Resolved amount must be 5,000g or less."
                        : "Enter an amount to resolve grams."}
                </span>
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
                  className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-900 outline-none transition focus:border-emerald-500"
                >
                  {MEAL_OPTIONS.map((option) => (
                    <option key={option.value || "any"} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            <div className="rounded-2xl bg-white px-4 py-2.5">
              <p className="text-sm font-semibold text-slate-900">
                Preview: {preview ?? "Enter an amount to preview this food."}
              </p>
            </div>

            {actionMessage ? (
              <p className="rounded-2xl bg-emerald-50 px-4 py-2.5 text-sm text-emerald-900">
                {actionMessage}
              </p>
            ) : null}
            {errorMessage ? (
              <p className="rounded-2xl bg-rose-50 px-4 py-2.5 text-sm text-rose-900">
                {errorMessage}
              </p>
            ) : null}

            <button
              type="button"
              onClick={() => void handleLogFood()}
              disabled={isSaving}
              className="inline-flex w-full items-center justify-center rounded-2xl bg-emerald-900 px-4 py-2.5 text-sm font-semibold text-emerald-50 transition hover:bg-emerald-800 disabled:cursor-not-allowed disabled:opacity-60 sm:w-auto"
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
