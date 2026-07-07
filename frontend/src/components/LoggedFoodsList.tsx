"use client";

import { useEffect, useState } from "react";

import { TodayCard } from "@/components/TodayCard";
import { fetchCanonicalFoodLogs } from "@/lib/canonicalFoodApi";
import {
  CANONICAL_FOOD_LOGGED_EVENT,
  CanonicalFoodLoggedEntry,
} from "@/types/canonicalFood";

interface LoggedFoodsListProps {
  initialEntries: CanonicalFoodLoggedEntry[];
  initialError?: string | null;
  userId: number;
  targetDate: string;
  className?: string;
}

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
  const [entries, setEntries] = useState(initialEntries);
  const [error, setError] = useState(initialError ?? null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const mealGroups = groupEntriesByMeal(entries);

  useEffect(() => {
    let isActive = true;

    async function refreshLoggedFoods() {
      setIsRefreshing(true);
      try {
        const response = await fetchCanonicalFoodLogs({
          userId,
          date: targetDate,
        });
        if (!isActive) {
          return;
        }
        setEntries(response.entries);
        setError(null);
      } catch (refreshError) {
        if (!isActive) {
          return;
        }
        setError(
          refreshError instanceof Error
            ? refreshError.message
            : "Logged foods are unavailable right now.",
        );
      } finally {
        if (isActive) {
          setIsRefreshing(false);
        }
      }
    }

    window.addEventListener(CANONICAL_FOOD_LOGGED_EVENT, refreshLoggedFoods);

    return () => {
      isActive = false;
      window.removeEventListener(CANONICAL_FOOD_LOGGED_EVENT, refreshLoggedFoods);
    };
  }, [targetDate, userId]);

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
                      className="grid gap-1 px-3 py-2.5 text-sm sm:grid-cols-[minmax(0,1fr)_auto] sm:items-baseline"
                    >
                      <span className="font-semibold text-slate-950">
                        {entry.food_name}
                      </span>
                      <span className="text-slate-600 sm:text-right">
                        {formatCompactNumber(entry.grams, "g")}
                      </span>
                      <span className="text-xs font-medium text-slate-600 sm:col-span-2">
                        {formatMacroLine(entry)}
                      </span>
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
