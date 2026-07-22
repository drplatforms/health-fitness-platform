"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import {
  FoodCatalogBrowseChoice,
  FoodCatalogBrowseDialog,
} from "@/components/FoodCatalogBrowseDialog";
import { PersonalFoodsList } from "@/components/PersonalFoodsList";
import { fetchPinnedFoods, setFoodPinned } from "@/lib/canonicalFoodApi";
import {
  FOOD_LIBRARY_CHANGED_EVENT,
  PinnedFood,
  PinnedFoodType,
} from "@/types/canonicalFood";

interface FoodLibraryPanelProps {
  userId: number;
  targetDate?: string;
}

export function FoodLibraryPanel({
  userId,
  targetDate,
}: FoodLibraryPanelProps) {
  const [isBrowseOpen, setIsBrowseOpen] = useState(false);
  const [pinnedFoods, setPinnedFoods] = useState<PinnedFood[]>([]);
  const [updatingPinnedKey, setUpdatingPinnedKey] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const loadPinnedFoods = useCallback(async () => {
    const response = await fetchPinnedFoods(userId);
    setPinnedFoods(response.results);
  }, [userId]);

  useEffect(() => {
    let active = true;
    void fetchPinnedFoods(userId)
      .then((response) => {
        if (active) {
          setPinnedFoods(response.results);
        }
      })
      .catch(() => {
        if (active) {
          setPinnedFoods([]);
        }
      });
    return () => {
      active = false;
    };
  }, [userId]);

  useEffect(() => {
    const handleLibraryChanged = () => {
      void loadPinnedFoods().catch(() => {
        // Keep the last usable pinned list when a background refresh fails.
      });
    };
    window.addEventListener(FOOD_LIBRARY_CHANGED_EVENT, handleLibraryChanged);
    return () =>
      window.removeEventListener(FOOD_LIBRARY_CHANGED_EVENT, handleLibraryChanged);
  }, [loadPinnedFoods]);

  const pinnedKeys = useMemo(
    () => new Set(pinnedFoods.map((food) => `${food.food_type}:${food.food_id}`)),
    [pinnedFoods],
  );

  async function togglePinned(choice: FoodCatalogBrowseChoice) {
    const foodType: PinnedFoodType =
      choice.kind === "catalog" ? "canonical" : choice.food.food_type;
    const foodId =
      choice.kind === "catalog"
        ? choice.food.canonical_food_id
        : choice.food.food_id;
    const key = `${foodType}:${foodId}`;
    const isPinned = pinnedKeys.has(key);

    setUpdatingPinnedKey(key);
    setMessage(null);
    try {
      await setFoodPinned({
        userId,
        foodType,
        foodId,
        pinned: !isPinned,
      });
      await loadPinnedFoods();
      window.dispatchEvent(new Event(FOOD_LIBRARY_CHANGED_EVENT));
    } catch (error) {
      setMessage(
        error instanceof Error ? error.message : "Unable to update this pinned food.",
      );
    } finally {
      setUpdatingPinnedKey(null);
    }
  }

  return (
    <div className="space-y-5">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-lg font-bold text-text-strong">Food Library</h2>
          <p className="mt-1 text-sm leading-5 text-text-body">
            Browse your catalog, preferences, pinned foods, and foods you added.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setIsBrowseOpen(true)}
          className="min-h-10 rounded-xl border border-border-accent bg-surface px-3 py-2 text-sm font-semibold text-accent-text transition hover:bg-surface-highlighted"
        >
          Browse catalog
        </button>
      </header>

      {message ? (
        <p role="alert" className="rounded-xl bg-danger-surface px-3 py-2 text-sm text-danger-foreground">
          {message}
        </p>
      ) : null}

      <section className="space-y-2" aria-labelledby="personal-foods-heading">
        <div>
          <h3 id="personal-foods-heading" className="text-sm font-semibold text-text-primary">
            Foods you added
          </h3>
          <p className="text-xs text-text-muted">
            Create, edit, archive, or restore your own food entries.
          </p>
        </div>
        <PersonalFoodsList
          userId={userId}
          targetDate={targetDate}
          variant="embedded"
        />
      </section>

      <FoodCatalogBrowseDialog
        open={isBrowseOpen}
        userId={userId}
        mode="manage"
        pinnedFoods={pinnedFoods}
        pinnedKeys={pinnedKeys}
        updatingPinnedKey={updatingPinnedKey}
        onClose={() => setIsBrowseOpen(false)}
        onTogglePinned={(choice) => void togglePinned(choice)}
        onDisplayNameChanged={() => {
          void loadPinnedFoods().catch(() => {
            // The dialog already applied the rename locally.
          });
          window.dispatchEvent(new Event(FOOD_LIBRARY_CHANGED_EVENT));
        }}
      />
    </div>
  );
}
