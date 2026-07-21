"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { TodayCard } from "@/components/TodayCard";
import { fetchDailyDriverToday } from "@/lib/dailyDriverApi";
import { CANONICAL_FOOD_LOGGED_EVENT } from "@/types/canonicalFood";
import { DailyDriverNutritionSummary } from "@/types/dailyDriver";
import { PERSONAL_FOOD_LOGGED_EVENT } from "@/types/personalFood";

function formatNumber(value: number | null, suffix = ""): string {
  if (value === null) {
    return "--";
  }

  return `${value.toLocaleString()}${suffix}`;
}

function formatTargetRange(
  min: number | null,
  max: number | null,
  suffix = "",
): string {
  if (min === null && max === null) {
    return "Target unavailable";
  }
  if (min === null || min === max) {
    return `Target ${formatNumber(max, suffix)}`;
  }
  if (max === null) {
    return `Target ${formatNumber(min, suffix)}`;
  }
  return `Target ${min.toLocaleString()}–${max.toLocaleString()}${suffix}`;
}

export function NutritionMacroCard({
  nutrition,
  userId,
  targetDate,
  className,
}: {
  nutrition: DailyDriverNutritionSummary;
  userId: number;
  targetDate: string;
  className?: string;
}) {
  const nutritionIdentity = `${userId}:${targetDate}`;
  const [nutritionState, setNutritionState] = useState({
    identity: nutritionIdentity,
    sourceNutrition: nutrition,
    nutrition,
  });
  const refreshRequestIdRef = useRef(0);
  const currentNutrition =
    nutritionState.identity === nutritionIdentity &&
    nutritionState.sourceNutrition === nutrition
      ? nutritionState.nutrition
      : nutrition;

  const refreshNutrition = useCallback(async () => {
    const requestId = refreshRequestIdRef.current + 1;
    refreshRequestIdRef.current = requestId;
    const result = await fetchDailyDriverToday({ userId, date: targetDate });

    if (requestId !== refreshRequestIdRef.current || !result.data) {
      return;
    }
    setNutritionState({
      identity: nutritionIdentity,
      sourceNutrition: nutrition,
      nutrition: result.data.nutrition,
    });
  }, [nutrition, nutritionIdentity, targetDate, userId]);

  useEffect(() => {
    const handleFoodLogged = () => void refreshNutrition();

    window.addEventListener(CANONICAL_FOOD_LOGGED_EVENT, handleFoodLogged);
    window.addEventListener(PERSONAL_FOOD_LOGGED_EVENT, handleFoodLogged);

    return () => {
      window.removeEventListener(CANONICAL_FOOD_LOGGED_EVENT, handleFoodLogged);
      window.removeEventListener(PERSONAL_FOOD_LOGGED_EVENT, handleFoodLogged);
    };
  }, [refreshNutrition]);

  const incompleteTotals = [
    !currentNutrition.calories_logged_complete ? "Calories" : null,
    !currentNutrition.protein_logged_complete ? "Protein" : null,
    !currentNutrition.carbs_logged_complete ? "Carbs" : null,
    !currentNutrition.fat_logged_complete ? "Fat" : null,
  ].filter((label): label is string => label !== null);

  return (
    <TodayCard title="Nutrition" className={className}>
      <div className="space-y-3">
        <div className="grid grid-cols-2 gap-2 text-sm sm:gap-3">
          <div className="rounded-xl bg-surface-subtle px-3 py-2.5 sm:rounded-2xl sm:px-4 sm:py-3">
            <p className="text-xs uppercase tracking-[0.16em] text-text-muted">
              Calories
            </p>
            <p className="mt-1.5 font-semibold text-text-primary sm:mt-2">
              {formatNumber(currentNutrition.calories_logged, " kcal")}
            </p>
            <p className="mt-0.5 text-xs text-text-muted">
              {formatTargetRange(
                currentNutrition.calorie_target_min,
                currentNutrition.calorie_target_max,
                " kcal",
              )}
            </p>
          </div>
          <div className="rounded-xl bg-surface-subtle px-3 py-2.5 sm:rounded-2xl sm:px-4 sm:py-3">
            <p className="text-xs uppercase tracking-[0.16em] text-text-muted">
              Protein
            </p>
            <p className="mt-1.5 font-semibold text-text-primary sm:mt-2">
              {formatNumber(currentNutrition.protein_logged_g, "g")}
            </p>
            <p className="mt-0.5 text-xs text-text-muted">
              {formatTargetRange(
                currentNutrition.protein_target_min_g,
                currentNutrition.protein_target_max_g,
                "g",
              )}
            </p>
          </div>
          <div className="rounded-xl bg-surface-subtle px-3 py-2.5 sm:rounded-2xl sm:px-4 sm:py-3">
            <p className="text-xs uppercase tracking-[0.16em] text-text-muted">
              Carbs
            </p>
            <p className="mt-1.5 font-semibold text-text-primary sm:mt-2">
              {formatNumber(currentNutrition.carbs_logged_g, "g")}
            </p>
            <p className="mt-0.5 text-xs text-text-muted">
              {formatTargetRange(
                currentNutrition.carbohydrate_target_min_g,
                currentNutrition.carbohydrate_target_max_g,
                "g",
              )}
            </p>
          </div>
          <div className="rounded-xl bg-surface-subtle px-3 py-2.5 sm:rounded-2xl sm:px-4 sm:py-3">
            <p className="text-xs uppercase tracking-[0.16em] text-text-muted">
              Fat
            </p>
            <p className="mt-1.5 font-semibold text-text-primary sm:mt-2">
              {formatNumber(currentNutrition.fat_logged_g, "g")}
            </p>
            <p className="mt-0.5 text-xs text-text-muted">
              {formatTargetRange(
                currentNutrition.fat_target_min_g,
                currentNutrition.fat_target_max_g,
                "g",
              )}
            </p>
          </div>
        </div>
        {incompleteTotals.length > 0 ? (
          <p className="text-xs leading-5 text-text-muted">
            Incomplete totals: {incompleteTotals.join(", ")}.
          </p>
        ) : null}
      </div>
    </TodayCard>
  );
}
