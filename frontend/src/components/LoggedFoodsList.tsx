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

function formatMealType(value: string | null): string {
  if (!value) {
    return "Any time";
  }

  return value.charAt(0).toUpperCase() + value.slice(1).replaceAll("_", " ");
}

function formatMacro(value: number | null, label: string): string {
  if (value === null) {
    return `${label} unknown`;
  }

  return `${formatCompactNumber(value)}${label}`;
}

function formatMacroLine(entry: CanonicalFoodLoggedEntry): string {
  return [
    entry.calories === null
      ? "cal unknown"
      : `${formatCompactNumber(entry.calories)} cal`,
    formatMacro(entry.protein_g, "P"),
    formatMacro(entry.carbs_g, "C"),
    formatMacro(entry.fat_g, "F"),
  ].join(" · ");
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
          <div className="divide-y divide-slate-100 rounded-2xl bg-slate-50 px-4 py-1">
            {entries.map((entry) => (
              <div
                key={entry.entry_id}
                className="grid gap-1 py-3 text-sm sm:grid-cols-[minmax(0,0.75fr)_minmax(0,1fr)_auto] sm:items-center"
              >
                <span className="font-semibold text-slate-700">
                  {formatMealType(entry.meal_type)}
                </span>
                <span className="font-semibold text-slate-950">
                  {entry.food_name}
                </span>
                <span className="text-slate-600 sm:text-right">
                  {formatCompactNumber(entry.grams, "g")}
                </span>
                <span className="text-xs font-medium text-slate-600 sm:col-span-3">
                  {formatMacroLine(entry)}
                </span>
              </div>
            ))}
          </div>
        ) : null}
      </div>
    </TodayCard>
  );
}
