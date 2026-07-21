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

type TargetState = "below" | "within" | "above" | "unavailable";

function clampPercentage(value: number): number {
  return Math.min(100, Math.max(0, value));
}

function NutritionTargetRangeBar({
  label,
  value,
  targetMin,
  targetMax,
  complete,
  suffix,
}: {
  label: string;
  value: number | null;
  targetMin: number | null;
  targetMax: number | null;
  complete: boolean;
  suffix: string;
}) {
  const lowerTarget = targetMin ?? targetMax;
  const upperTarget = targetMax ?? targetMin;
  const hasTarget = lowerTarget !== null && upperTarget !== null;
  let state: TargetState = "unavailable";

  if (value !== null && lowerTarget !== null && upperTarget !== null) {
    state = value < lowerTarget ? "below" : value > upperTarget ? "above" : "within";
  }
  const scaleMax = Math.max((upperTarget ?? value ?? 1) * 1.2, 1);
  const valuePosition = clampPercentage(((value ?? 0) / scaleMax) * 100);
  const targetStart = clampPercentage(((lowerTarget ?? 0) / scaleMax) * 100);
  const targetEnd = clampPercentage(((upperTarget ?? 0) / scaleMax) * 100);
  const stateColor = {
    below: "bg-caution-action",
    within: "bg-control-positive-accent",
    above: "bg-danger-action",
    unavailable: "bg-border",
  }[state];
  const stateLabel = {
    below: "below target",
    within: "within target",
    above: "above target",
    unavailable: "target comparison unavailable",
  }[state];
  const completenessLabel = complete ? "" : "; known subtotal, incomplete";

  return (
    <div
      className="relative mt-2 h-2.5 w-full overflow-hidden rounded-full bg-surface-muted ring-1 ring-inset ring-border-subtle"
      role="img"
      aria-label={`${label}: ${formatNumber(value, suffix)}; ${formatTargetRange(targetMin, targetMax, suffix)}; ${stateLabel}${completenessLabel}`}
    >
      {hasTarget ? (
        <span
          className="absolute inset-y-0 bg-positive-surface ring-1 ring-inset ring-control-positive-accent"
          style={{
            left: `${targetStart}%`,
            width: `${targetEnd - targetStart}%`,
          }}
        />
      ) : null}
      {value !== null ? (
        <>
          <span
            className={`absolute left-0 top-[3px] h-1 ${stateColor} ${complete ? "" : "border-r border-dashed border-text-primary opacity-50"}`}
            style={{ width: `${valuePosition}%` }}
          />
          <span
            className={`absolute top-1/2 h-2 w-2 -translate-x-1/2 -translate-y-1/2 rounded-full ${stateColor} ring-2 ring-surface-subtle ${complete ? "" : "opacity-50"}`}
            style={{ left: `${Math.min(98, Math.max(2, valuePosition))}%` }}
          />
        </>
      ) : null}
    </div>
  );
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
            <NutritionTargetRangeBar
              label="Calories"
              value={currentNutrition.calories_logged}
              targetMin={currentNutrition.calorie_target_min}
              targetMax={currentNutrition.calorie_target_max}
              complete={currentNutrition.calories_logged_complete}
              suffix=" kcal"
            />
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
            <NutritionTargetRangeBar
              label="Protein"
              value={currentNutrition.protein_logged_g}
              targetMin={currentNutrition.protein_target_min_g}
              targetMax={currentNutrition.protein_target_max_g}
              complete={currentNutrition.protein_logged_complete}
              suffix="g"
            />
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
            <NutritionTargetRangeBar
              label="Carbs"
              value={currentNutrition.carbs_logged_g}
              targetMin={currentNutrition.carbohydrate_target_min_g}
              targetMax={currentNutrition.carbohydrate_target_max_g}
              complete={currentNutrition.carbs_logged_complete}
              suffix="g"
            />
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
            <NutritionTargetRangeBar
              label="Fat"
              value={currentNutrition.fat_logged_g}
              targetMin={currentNutrition.fat_target_min_g}
              targetMax={currentNutrition.fat_target_max_g}
              complete={currentNutrition.fat_logged_complete}
              suffix="g"
            />
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
