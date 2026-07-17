"use client";

import { useRef, useState } from "react";

import { TodayCard } from "@/components/TodayCard";
import { logCanonicalFood } from "@/lib/canonicalFoodApi";
import { NutritionFoodSuggestion } from "@/types/nutritionFoodSuggestion";
import { CANONICAL_FOOD_LOGGED_EVENT } from "@/types/canonicalFood";

const MACRO_LABELS: Record<NutritionFoodSuggestion["macro_gap_addressed"], string> = {
  protein_g: "Protein",
  carbohydrate_g: "Carbs",
  calories: "Calories",
  fat_g: "Fat",
};

function formatGrams(grams: number): string {
  return Number.isInteger(grams) ? String(grams) : grams.toFixed(1);
}

export function NutritionGapActionsCard({
  userId,
  targetDate,
  suggestions,
}: {
  userId: number;
  targetDate: string;
  suggestions: NutritionFoodSuggestion[];
}) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [loggingFoodId, setLoggingFoodId] = useState<number | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [messageTone, setMessageTone] = useState<"success" | "error" | null>(
    null,
  );
  const isLoggingRef = useRef(false);

  if (suggestions.length === 0) {
    return null;
  }

  async function handleLogSuggestion(suggestion: NutritionFoodSuggestion) {
    if (isLoggingRef.current) {
      return;
    }

    isLoggingRef.current = true;
    setLoggingFoodId(suggestion.canonical_food_id);
    setMessage(null);
    setMessageTone(null);

    try {
      await logCanonicalFood({
        user_id: userId,
        entry_date: targetDate,
        canonical_food_id: suggestion.canonical_food_id,
        grams: suggestion.suggested_grams,
      });
      setMessage(`${suggestion.display_name} logged.`);
      setMessageTone("success");
      window.dispatchEvent(new CustomEvent(CANONICAL_FOOD_LOGGED_EVENT));
    } catch (error) {
      setMessage(
        error instanceof Error
          ? error.message
          : "Unable to log this food right now.",
      );
      setMessageTone("error");
    } finally {
      isLoggingRef.current = false;
      setLoggingFoodId(null);
    }
  }

  const visibleSuggestions = isExpanded ? suggestions : suggestions.slice(0, 1);
  const additionalSuggestionCount = suggestions.length - 1;

  return (
    <TodayCard title="Close the gap">
      <div className="space-y-2">
        {visibleSuggestions.map((suggestion) => {
          const isLogging = loggingFoodId === suggestion.canonical_food_id;

          return (
            <div
              key={suggestion.canonical_food_id}
              className="flex items-center justify-between gap-3 rounded-xl bg-surface-subtle px-3 py-2"
            >
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
                  <p className="text-sm font-semibold text-text-strong">
                    {suggestion.display_name}
                  </p>
                  <span className="rounded-full bg-surface px-2 py-0.5 text-[0.68rem] font-semibold text-text-secondary">
                    {MACRO_LABELS[suggestion.macro_gap_addressed]}
                  </span>
                </div>
              </div>
              <button
                type="button"
                onClick={() => void handleLogSuggestion(suggestion)}
                disabled={loggingFoodId !== null}
                className="inline-flex min-h-10 shrink-0 items-center justify-center rounded-lg bg-action-primary px-3 py-1.5 text-sm font-semibold text-action-primary-foreground transition hover:bg-action-primary-hover disabled:cursor-not-allowed disabled:opacity-60"
              >
                {isLogging ? "Logging..." : `Log ${formatGrams(suggestion.suggested_grams)}g`}
              </button>
            </div>
          );
        })}
        {additionalSuggestionCount > 0 ? (
          <button
            type="button"
            aria-expanded={isExpanded}
            onClick={() => setIsExpanded((expanded) => !expanded)}
            className="inline-flex min-h-10 items-center rounded-lg px-2 text-sm font-semibold text-accent-text transition hover:bg-surface-subtle"
          >
            {isExpanded
              ? "Show less"
              : `More options (${additionalSuggestionCount})`}
          </button>
        ) : null}
        {message && messageTone ? (
          <p
            aria-live="polite"
            className={`rounded-xl px-3 py-2 text-sm ${
              messageTone === "success"
                ? "bg-positive-surface text-positive-foreground"
                : "bg-danger-surface text-danger-foreground"
            }`}
          >
            {message}
          </p>
        ) : null}
      </div>
    </TodayCard>
  );
}
