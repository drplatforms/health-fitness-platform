"use client";

import {
  useDeferredValue,
  useEffect,
  useId,
  useMemo,
  useState,
} from "react";

import {
  fetchAvailableIngredientStarterGroups,
  fetchAvailableIngredients,
  searchCanonicalFoods,
  setIngredientAvailable,
} from "@/lib/canonicalFoodApi";
import type {
  AvailableIngredient,
  AvailableIngredientStarterGroup,
  AvailableIngredientStarterItem,
  CanonicalFoodSearchResult,
} from "@/types/canonicalFood";
import { FOOD_LIBRARY_CHANGED_EVENT } from "@/types/canonicalFood";

interface AvailableIngredientsPanelProps {
  userId: number;
}

function sortIngredients(ingredients: AvailableIngredient[]) {
  return [...ingredients].sort((left, right) =>
    left.display_name.localeCompare(right.display_name, undefined, {
      sensitivity: "base",
    }),
  );
}

function ingredientFromCatalogItem(
  food: CanonicalFoodSearchResult | AvailableIngredientStarterItem,
): AvailableIngredient {
  return {
    canonical_food_id: food.canonical_food_id,
    display_name: food.display_name,
    food_type: food.food_type,
    added_at: new Date().toISOString(),
  };
}

export function AvailableIngredientsPanel({
  userId,
}: AvailableIngredientsPanelProps) {
  const id = useId();
  const [ingredients, setIngredients] = useState<AvailableIngredient[]>([]);
  const [starterGroups, setStarterGroups] = useState<
    AvailableIngredientStarterGroup[]
  >([]);
  const [activeStarterGroupKey, setActiveStarterGroupKey] = useState("");
  const [pendingStarterIds, setPendingStarterIds] = useState<Set<number>>(
    () => new Set(),
  );
  const [query, setQuery] = useState("");
  const [selectedFilter, setSelectedFilter] = useState("");
  const [results, setResults] = useState<CanonicalFoodSearchResult[]>([]);
  const [loadedUserId, setLoadedUserId] = useState<number | null>(null);
  const [starterGroupsLoaded, setStarterGroupsLoaded] = useState(false);
  const [isQuickSetupOpen, setIsQuickSetupOpen] = useState(false);
  const [isSelectedIngredientsOpen, setIsSelectedIngredientsOpen] =
    useState(true);
  const [isSearching, setIsSearching] = useState(false);
  const [isAddingStarters, setIsAddingStarters] = useState(false);
  const [updatingFoodId, setUpdatingFoodId] = useState<number | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [starterMessage, setStarterMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const deferredQuery = useDeferredValue(query.trim());

  useEffect(() => {
    let isActive = true;
    fetchAvailableIngredients(userId)
      .then((response) => {
        if (isActive) {
          setIngredients(sortIngredients(response.results));
          setIsQuickSetupOpen(response.results.length === 0);
          setIsSelectedIngredientsOpen(response.results.length <= 10);
          setErrorMessage(null);
        }
      })
      .catch((error: unknown) => {
        if (isActive) {
          setIngredients([]);
          setErrorMessage(
            error instanceof Error
              ? error.message
              : "Unable to load your pantry.",
          );
        }
      })
      .finally(() => {
        if (isActive) {
          setLoadedUserId(userId);
        }
      });

    return () => {
      isActive = false;
    };
  }, [userId]);

  useEffect(() => {
    let active = true;
    const handleLibraryChanged = () => {
      void Promise.all([
        fetchAvailableIngredients(userId),
        fetchAvailableIngredientStarterGroups(userId),
      ]).then(([available, starters]) => {
        if (!active) return;
        setIngredients(sortIngredients(available.results));
        setStarterGroups(starters.groups);
        setActiveStarterGroupKey((current) =>
          starters.groups.some((group) => group.key === current)
            ? current
            : (starters.groups[0]?.key ?? ""),
        );
      }).catch(() => {
        // Keep the last usable Pantry state when a background refresh fails.
      });
    };
    window.addEventListener(FOOD_LIBRARY_CHANGED_EVENT, handleLibraryChanged);
    return () => {
      active = false;
      window.removeEventListener(FOOD_LIBRARY_CHANGED_EVENT, handleLibraryChanged);
    };
  }, [userId]);

  useEffect(() => {
    let isActive = true;
    fetchAvailableIngredientStarterGroups(userId)
      .then((response) => {
        if (isActive) {
          setStarterGroups(response.groups);
          setActiveStarterGroupKey(response.groups[0]?.key ?? "");
          setStarterMessage(null);
        }
      })
      .catch((error: unknown) => {
        if (isActive) {
          setStarterMessage(
            error instanceof Error
              ? error.message
              : "Unable to load quick-start ingredients.",
          );
        }
      })
      .finally(() => {
        if (isActive) {
          setStarterGroupsLoaded(true);
        }
      });

    return () => {
      isActive = false;
    };
  }, [userId]);

  useEffect(() => {
    if (deferredQuery.length < 2) {
      return;
    }

    let isActive = true;
    const timeoutId = window.setTimeout(async () => {
      setIsSearching(true);
      setMessage(null);
      try {
        const response = await searchCanonicalFoods(deferredQuery, 20, userId);
        if (!isActive) {
          return;
        }
        setResults(response.results);
        setMessage(
          response.results.length === 0 ? "No matching foods found." : null,
        );
      } catch (error) {
        if (!isActive) {
          return;
        }
        setResults([]);
        setMessage(
          error instanceof Error ? error.message : "Unable to search foods.",
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

  const availableIds = useMemo(
    () => new Set(ingredients.map((item) => item.canonical_food_id)),
    [ingredients],
  );
  const activeStarterGroup =
    starterGroups.find((group) => group.key === activeStarterGroupKey) ??
    starterGroups[0];
  const selectedStarterIds = useMemo(
    () =>
      [...pendingStarterIds].filter((foodId) => !availableIds.has(foodId)),
    [availableIds, pendingStarterIds],
  );
  const normalizedFilter = selectedFilter.trim().toLocaleLowerCase();
  const visibleIngredients = useMemo(
    () =>
      normalizedFilter
        ? ingredients.filter((item) =>
            item.display_name.toLocaleLowerCase().includes(normalizedFilter),
          )
        : ingredients,
    [ingredients, normalizedFilter],
  );

  async function toggleIngredient(
    food: CanonicalFoodSearchResult | AvailableIngredient,
    makeAvailable: boolean,
  ) {
    const canonicalFoodId = food.canonical_food_id;
    setUpdatingFoodId(canonicalFoodId);
    setErrorMessage(null);
    try {
      const response = await setIngredientAvailable({
        userId,
        canonicalFoodId,
        available: makeAvailable,
      });
      if (makeAvailable) {
        const ingredient =
          response.available_ingredient ??
          ingredientFromCatalogItem(food as CanonicalFoodSearchResult);
        setIngredients((current) =>
          sortIngredients([
            ...current.filter(
              (item) => item.canonical_food_id !== canonicalFoodId,
            ),
            ingredient,
          ]),
        );
      } else {
        setIngredients((current) =>
          current.filter((item) => item.canonical_food_id !== canonicalFoodId),
        );
      }
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "Unable to update your pantry.",
      );
    } finally {
      setUpdatingFoodId(null);
    }
  }

  function toggleStarterSelection(canonicalFoodId: number) {
    setPendingStarterIds((current) => {
      const next = new Set(current);
      if (next.has(canonicalFoodId)) {
        next.delete(canonicalFoodId);
      } else {
        next.add(canonicalFoodId);
      }
      return next;
    });
  }

  async function addSelectedStarterIngredients() {
    const selectedIdSet = new Set(selectedStarterIds);
    const selectedItems = starterGroups
      .flatMap((group) => group.items)
      .filter((item) => selectedIdSet.has(item.canonical_food_id));
    if (selectedItems.length === 0) {
      return;
    }

    setIsAddingStarters(true);
    setErrorMessage(null);
    const results = await Promise.allSettled(
      selectedItems.map(async (item) => {
        const response = await setIngredientAvailable({
          userId,
          canonicalFoodId: item.canonical_food_id,
          available: true,
        });
        return (
          response.available_ingredient ?? ingredientFromCatalogItem(item)
        );
      }),
    );

    const addedIngredients: AvailableIngredient[] = [];
    const successfulIds = new Set<number>();
    let failureCount = 0;
    results.forEach((result, index) => {
      if (result.status === "fulfilled") {
        addedIngredients.push(result.value);
        successfulIds.add(selectedItems[index].canonical_food_id);
      } else {
        failureCount += 1;
      }
    });

    if (addedIngredients.length > 0) {
      setIngredients((current) =>
        sortIngredients([
          ...current.filter(
            (item) => !successfulIds.has(item.canonical_food_id),
          ),
          ...addedIngredients,
        ]),
      );
      setPendingStarterIds((current) =>
        new Set([...current].filter((foodId) => !successfulIds.has(foodId))),
      );
    }
    if (failureCount > 0) {
      setErrorMessage(
        `${failureCount} ingredient${failureCount === 1 ? "" : "s"} could not be added. Your remaining selections are still checked.`,
      );
    }
    setIsAddingStarters(false);
  }

  return (
    <div className="space-y-5">
      <header>
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h2 className="text-lg font-bold text-text-strong">
            Pantry
          </h2>
          <span className="rounded-full bg-surface-subtle px-2.5 py-1 text-xs font-semibold text-text-secondary">
            {ingredients.length} selected
          </span>
        </div>
        <p className="mt-1 text-sm leading-5 text-text-body">
          Foods you generally keep on hand.
        </p>
      </header>

      <section
        aria-labelledby={`${id}-quick-setup-heading`}
        className="space-y-3 rounded-2xl border border-border bg-surface-subtle p-3"
      >
        <button
          type="button"
          aria-expanded={isQuickSetupOpen}
          aria-controls={`${id}-quick-setup-options`}
          onClick={() => setIsQuickSetupOpen((current) => !current)}
          className="flex w-full items-center justify-between gap-3 text-left"
        >
          <span>
            <span
              id={`${id}-quick-setup-heading`}
              className="block text-sm font-semibold text-text-primary"
            >
              Quick setup
            </span>
            <span className="block text-xs text-text-secondary">
              Choose several common foods, then add them together.
            </span>
          </span>
          <span className="shrink-0 text-xs font-semibold text-accent-text">
            {isQuickSetupOpen ? "Hide" : "Choose foods"}
          </span>
        </button>

        {isQuickSetupOpen ? (
          <div id={`${id}-quick-setup-options`} className="space-y-3">
            {selectedStarterIds.length > 0 ? (
              <p className="text-right text-xs font-semibold text-accent-text">
                {selectedStarterIds.length} ready to add
              </p>
            ) : null}
            {!starterGroupsLoaded ? (
              <p className="text-sm text-text-body" role="status">
                Loading quick setup...
              </p>
            ) : starterMessage ? (
              <p className="text-sm text-danger-foreground" role="status">
                {starterMessage} Use catalog search below instead.
              </p>
            ) : (
              <>
            <div
              className="flex gap-1.5 overflow-x-auto pb-1"
              role="group"
              aria-label="Starter ingredient groups"
            >
              {starterGroups.map((group) => (
                <button
                  key={group.key}
                  type="button"
                  aria-pressed={activeStarterGroup?.key === group.key}
                  onClick={() => setActiveStarterGroupKey(group.key)}
                  className={`shrink-0 rounded-full border px-3 py-1.5 text-xs font-semibold transition ${
                    activeStarterGroup?.key === group.key
                      ? "border-border-accent bg-surface-highlighted text-accent-text"
                      : "border-border bg-surface text-text-secondary hover:bg-surface-highlighted"
                  }`}
                >
                  {group.title}
                </button>
              ))}
            </div>

            {activeStarterGroup && activeStarterGroup.items.length > 0 ? (
              <div className="grid max-h-40 grid-cols-2 gap-1.5 overflow-y-auto sm:grid-cols-3 lg:grid-cols-4">
                {activeStarterGroup.items.map((item) => {
                  const isAvailable = availableIds.has(item.canonical_food_id);
                  const isSelected = pendingStarterIds.has(
                    item.canonical_food_id,
                  );
                  return (
                    <button
                      key={item.canonical_food_id}
                      type="button"
                      disabled={isAvailable || isAddingStarters}
                      aria-pressed={isAvailable || isSelected}
                      onClick={() =>
                        toggleStarterSelection(item.canonical_food_id)
                      }
                      className={`flex min-h-10 min-w-0 items-center gap-2 rounded-xl border px-2.5 py-2 text-left text-xs font-medium transition disabled:cursor-default ${
                        isAvailable
                          ? "border-border bg-positive-surface text-positive-foreground opacity-70"
                          : isSelected
                            ? "border-border-accent bg-surface-highlighted text-accent-text"
                            : "border-border bg-surface text-text-primary hover:bg-surface-highlighted"
                      }`}
                    >
                      <span
                        aria-hidden="true"
                        className="flex h-4 w-4 shrink-0 items-center justify-center rounded border border-current text-[0.65rem]"
                      >
                        {isAvailable || isSelected ? "✓" : ""}
                      </span>
                      <span className="min-w-0 truncate">
                        {item.display_name}
                      </span>
                    </button>
                  );
                })}
              </div>
            ) : (
              <p className="text-xs text-text-secondary">
                No matching catalog foods are available in this group yet.
              </p>
            )}

            <div className="flex justify-end">
              <button
                type="button"
                disabled={selectedStarterIds.length === 0 || isAddingStarters}
                onClick={() => void addSelectedStarterIngredients()}
                className="min-h-10 rounded-xl border border-border-accent bg-surface-highlighted px-4 py-2 text-sm font-semibold text-accent-text transition hover:bg-positive-surface disabled:cursor-not-allowed disabled:opacity-50"
              >
                {isAddingStarters
                  ? "Adding..."
                  : `Add selected${selectedStarterIds.length > 0 ? ` (${selectedStarterIds.length})` : ""}`}
              </button>
            </div>
              </>
            )}
          </div>
        ) : null}
      </section>

      <section aria-labelledby={`${id}-search-heading`} className="space-y-2">
        <h3 id={`${id}-search-heading`} className="text-sm font-semibold text-text-primary">
          Search the food catalog
        </h3>
        <input
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
              setMessage(
                trimmedQuery.length === 0
                  ? null
                  : "Type at least 2 characters to search foods.",
              );
            } else {
              setMessage(null);
            }
          }}
          placeholder="Search rice, tomatoes, yogurt..."
          aria-label="Search foods to add to your pantry"
          className="w-full rounded-2xl border border-border bg-surface px-4 py-2.5 text-sm text-text-primary outline-none transition focus:border-focus"
        />

        {isSearching ? (
          <p className="rounded-2xl bg-surface-subtle px-4 py-3 text-sm text-text-body" role="status">
            Searching foods...
          </p>
        ) : null}
        {!isSearching && message ? (
          <p className="rounded-2xl bg-surface-subtle px-4 py-3 text-sm text-text-body" role="status">
            {message}
          </p>
        ) : null}

        {results.length > 0 && deferredQuery.length >= 2 ? (
          <div className="max-h-72 space-y-1 overflow-y-auto rounded-2xl border border-border bg-surface p-1">
            {results.map((food) => {
              const isAvailable = availableIds.has(food.canonical_food_id);
              const isUpdating = updatingFoodId === food.canonical_food_id;
              return (
                <div
                  key={food.canonical_food_id}
                  className="flex items-center gap-3 rounded-xl px-3 py-2 hover:bg-surface-subtle"
                >
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-semibold text-text-strong">
                      {food.display_name}
                    </p>
                    <p className="truncate text-xs text-text-secondary">
                      {food.food_type}
                    </p>
                  </div>
                  <button
                    type="button"
                    disabled={isUpdating}
                    aria-label={`${isAvailable ? "Remove" : "Add"} ${food.display_name} ${isAvailable ? "from" : "to"} your pantry`}
                    onClick={() => void toggleIngredient(food, !isAvailable)}
                    className={`min-h-10 min-w-20 shrink-0 rounded-xl border px-3 py-2 text-sm font-semibold transition disabled:opacity-50 ${
                      isAvailable
                        ? "border-border bg-surface text-text-secondary hover:bg-surface-subtle"
                        : "border-border-accent bg-surface-highlighted text-accent-text hover:bg-positive-surface"
                    }`}
                  >
                    {isUpdating ? "Saving..." : isAvailable ? "Remove" : "Add"}
                  </button>
                </div>
              );
            })}
          </div>
        ) : null}
      </section>

      {errorMessage ? (
        <p className="rounded-2xl border border-border bg-danger-surface px-4 py-3 text-sm text-danger-foreground" role="alert">
          {errorMessage}
        </p>
      ) : null}

      <section aria-labelledby={`${id}-selected-heading`} className="space-y-3">
        <div className="flex items-center justify-between gap-3">
          <div className="flex min-w-0 items-center gap-2">
            <h3
              id={`${id}-selected-heading`}
              className="text-sm font-semibold text-text-primary"
            >
              Pantry foods
            </h3>
            <span className="rounded-full bg-surface-subtle px-2 py-0.5 text-xs font-semibold text-text-secondary">
              {ingredients.length}
            </span>
          </div>
          <button
            type="button"
            aria-expanded={isSelectedIngredientsOpen}
            aria-controls={`${id}-selected-content`}
            onClick={() =>
              setIsSelectedIngredientsOpen((current) => !current)
            }
            className="shrink-0 rounded-lg px-2.5 py-1.5 text-xs font-semibold text-accent-text transition hover:bg-surface-highlighted"
          >
            {isSelectedIngredientsOpen
              ? "Hide ingredients"
              : "Show ingredients"}
          </button>
        </div>

        {isSelectedIngredientsOpen ? (
          <div id={`${id}-selected-content`} className="space-y-3">
            {ingredients.length > 10 ? (
            <input
              type="search"
              value={selectedFilter}
              onChange={(event) => setSelectedFilter(event.target.value)}
              placeholder="Filter selected..."
              aria-label="Filter pantry foods"
              className="w-full rounded-xl border border-border bg-surface px-3 py-2 text-sm text-text-primary outline-none focus:border-focus sm:w-56"
            />
            ) : null}

            {loadedUserId !== userId ? (
              <p className="rounded-2xl bg-surface-subtle px-4 py-3 text-sm text-text-body" role="status">
                Loading pantry...
              </p>
            ) : ingredients.length === 0 ? (
              <p className="rounded-2xl border border-dashed border-border px-4 py-5 text-center text-sm text-text-secondary">
                Your pantry is empty. Search the catalog to add foods you
                generally keep on hand.
              </p>
            ) : visibleIngredients.length === 0 ? (
              <p className="rounded-2xl bg-surface-subtle px-4 py-3 text-sm text-text-body">
                No selected ingredients match this filter.
              </p>
            ) : (
              <ul className="grid max-h-[26rem] grid-cols-1 gap-2 overflow-y-auto pr-1 sm:grid-cols-2 lg:grid-cols-3">
                {visibleIngredients.map((ingredient) => {
                  const isUpdating =
                    updatingFoodId === ingredient.canonical_food_id;
                  return (
                    <li
                      key={ingredient.canonical_food_id}
                      className="flex min-w-0 items-center gap-2 rounded-xl border border-border bg-surface-subtle px-3 py-2"
                    >
                      <span className="min-w-0 flex-1 truncate text-sm font-medium text-text-primary">
                        {ingredient.display_name}
                      </span>
                      <button
                        type="button"
                        disabled={isUpdating}
                        aria-label={`Remove ${ingredient.display_name} from your pantry`}
                        title={`Remove ${ingredient.display_name}`}
                        onClick={() => void toggleIngredient(ingredient, false)}
                        className="flex min-h-9 min-w-9 shrink-0 items-center justify-center rounded-lg text-lg leading-none text-text-muted transition hover:bg-surface hover:text-danger-foreground disabled:opacity-50"
                      >
                        <span aria-hidden="true">×</span>
                      </button>
                    </li>
                  );
                })}
              </ul>
            )}
          </div>
        ) : null}
      </section>
    </div>
  );
}
