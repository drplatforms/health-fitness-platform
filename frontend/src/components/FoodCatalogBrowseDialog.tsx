"use client";

import {
  useCallback,
  useDeferredValue,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { createPortal } from "react-dom";

import { browseCanonicalFoods } from "@/lib/canonicalFoodApi";
import {
  CanonicalFoodBrowseScope,
  CanonicalFoodNutrientSummary,
  CanonicalFoodSearchResult,
  PinnedFood,
} from "@/types/canonicalFood";

const ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("");
const BROWSE_PAGE_SIZE = 25;
const MAX_RENDERED_FOODS = 100;

type BrowseFilter = CanonicalFoodBrowseScope | "pinned";

export type FoodCatalogBrowseChoice =
  | { kind: "catalog"; food: CanonicalFoodSearchResult }
  | { kind: "pinned"; food: PinnedFood };

interface FoodCatalogBrowseDialogProps {
  open: boolean;
  userId: number;
  pinnedFoods: PinnedFood[];
  pinnedKeys: Set<string>;
  updatingPinnedKey: string | null;
  onClose: () => void;
  onSelect: (choice: FoodCatalogBrowseChoice) => void;
  onTogglePinned: (choice: FoodCatalogBrowseChoice) => void;
}

function choiceKey(choice: FoodCatalogBrowseChoice) {
  return choice.kind === "catalog"
    ? `canonical:${choice.food.canonical_food_id}`
    : `${choice.food.food_type}:${choice.food.food_id}`;
}

function choiceName(choice: FoodCatalogBrowseChoice) {
  return choice.food.display_name;
}

function choiceNutrients(choice: FoodCatalogBrowseChoice) {
  return choice.food.nutrient_summary;
}

function formatCompactNumber(value: number): string {
  return Math.abs(value % 1) < 0.001
    ? String(Math.round(value))
    : value.toFixed(1);
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

function sectionLetter(name: string) {
  const letter = name.trim().charAt(0).toUpperCase();
  return ALPHABET.includes(letter) ? letter : "#";
}

function PinIcon({ active }: { active: boolean }) {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 24 24"
      className="h-4 w-4"
      fill={active ? "currentColor" : "none"}
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M9 3h6l-1 6 3 3v2H7v-2l3-3-1-6Z" />
      <path d="M12 14v7" />
    </svg>
  );
}

export function FoodCatalogBrowseDialog({
  open,
  userId,
  pinnedFoods,
  pinnedKeys,
  updatingPinnedKey,
  onClose,
  onSelect,
  onTogglePinned,
}: FoodCatalogBrowseDialogProps) {
  const [filter, setFilter] = useState<BrowseFilter>("all");
  const [query, setQuery] = useState("");
  const [startLetter, setStartLetter] = useState("");
  const [catalogFoods, setCatalogFoods] = useState<CanonicalFoodSearchResult[]>([]);
  const [nextOffset, setNextOffset] = useState<number | null>(0);
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const deferredQuery = useDeferredValue(query.trim());
  const requestIdRef = useRef(0);
  const searchInputRef = useRef<HTMLInputElement>(null);
  const surfaceRef = useRef<HTMLElement>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const loadSentinelRef = useRef<HTMLDivElement>(null);

  const loadPage = useCallback(
    async (offset: number) => {
      if (filter === "pinned") {
        return;
      }
      const requestId = ++requestIdRef.current;
      setIsLoading(true);
      setMessage(null);
      try {
        const response = await browseCanonicalFoods({
          userId,
          scope: filter,
          offset,
          limit: BROWSE_PAGE_SIZE,
          query: deferredQuery,
          startLetter,
        });
        if (requestId !== requestIdRef.current) {
          return;
        }
        setCatalogFoods((current) =>
          offset === 0
            ? response.results
            : [...current, ...response.results].slice(0, MAX_RENDERED_FOODS),
        );
        setNextOffset(response.next_offset);
        if (offset === 0 && response.results.length === 0) {
          setMessage("No foods match this browse view.");
        }
      } catch (error) {
        if (requestId !== requestIdRef.current) {
          return;
        }
        if (offset === 0) {
          setCatalogFoods([]);
        }
        setMessage(
          error instanceof Error
            ? error.message
            : "Unable to browse foods right now.",
        );
      } finally {
        if (requestId === requestIdRef.current) {
          setIsLoading(false);
        }
      }
    },
    [deferredQuery, filter, startLetter, userId],
  );

  useEffect(() => {
    if (!open || filter === "pinned") {
      return;
    }
    const timeoutId = window.setTimeout(() => void loadPage(0), 180);
    return () => window.clearTimeout(timeoutId);
  }, [filter, loadPage, open]);

  useEffect(() => {
    if (!open) {
      return;
    }
    const previousOverflow = document.body.style.overflow;
    const previouslyFocused = document.activeElement as HTMLElement | null;
    document.body.style.overflow = "hidden";
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose();
        return;
      }
      if (event.key === "Tab") {
        const focusable = surfaceRef.current?.querySelectorAll<HTMLElement>(
          'button:not([disabled]), input:not([disabled]), [href], [tabindex]:not([tabindex="-1"])',
        );
        if (!focusable?.length) {
          return;
        }
        const first = focusable[0];
        const last = focusable[focusable.length - 1];
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault();
          last.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first.focus();
        }
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    window.requestAnimationFrame(() => searchInputRef.current?.focus());
    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", handleKeyDown);
      previouslyFocused?.focus();
    };
  }, [onClose, open]);

  useEffect(() => {
    if (
      !open ||
      filter === "pinned" ||
      nextOffset === null ||
      isLoading ||
      catalogFoods.length >= MAX_RENDERED_FOODS
    ) {
      return;
    }
    const root = scrollRef.current;
    const sentinel = loadSentinelRef.current;
    if (!root || !sentinel) {
      return;
    }
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          void loadPage(nextOffset);
        }
      },
      { root, rootMargin: "240px 0px" },
    );
    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [catalogFoods.length, filter, isLoading, loadPage, nextOffset, open]);

  const visibleChoices = useMemo<FoodCatalogBrowseChoice[]>(() => {
    if (filter !== "pinned") {
      return catalogFoods.map((food) => ({ kind: "catalog", food }));
    }
    const normalizedQuery = deferredQuery.toLocaleLowerCase();
    return pinnedFoods
      .filter((food) => {
        const name = food.display_name.trim();
        return (
          (!normalizedQuery || name.toLocaleLowerCase().includes(normalizedQuery)) &&
          (!startLetter || name.localeCompare(startLetter, undefined, { sensitivity: "base" }) >= 0)
        );
      })
      .sort((left, right) =>
        left.display_name.localeCompare(right.display_name, undefined, {
          sensitivity: "base",
        }),
      )
      .map((food) => ({ kind: "pinned", food }));
  }, [catalogFoods, deferredQuery, filter, pinnedFoods, startLetter]);

  const sections = useMemo(() => {
    const grouped = new Map<string, FoodCatalogBrowseChoice[]>();
    for (const choice of visibleChoices) {
      const letter = sectionLetter(choiceName(choice));
      grouped.set(letter, [...(grouped.get(letter) ?? []), choice]);
    }
    return [...grouped.entries()];
  }, [visibleChoices]);

  if (!open) {
    return null;
  }

  return createPortal(
    <div className="fixed inset-0 z-[80]" role="dialog" aria-modal="true" aria-labelledby="food-browse-title">
      <button
        type="button"
        aria-label="Close food browse"
        onClick={onClose}
        className="absolute inset-0 hidden bg-black/40 backdrop-blur-[1px] md:block"
      />
      <section ref={surfaceRef} className="absolute inset-0 flex min-w-0 flex-col bg-surface shadow-2xl md:left-auto md:w-[min(52rem,86vw)] md:border-l md:border-border">
        <header className="z-20 shrink-0 border-b border-border bg-surface px-3 pb-3 pt-[max(0.75rem,env(safe-area-inset-top))] sm:px-5 md:pt-4">
          <div className="flex items-center justify-between gap-3">
            <div className="min-w-0">
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-text-muted">Food catalog</p>
              <h2 id="food-browse-title" className="text-xl font-semibold text-text-strong">Browse foods</h2>
            </div>
            <button
              type="button"
              onClick={onClose}
              className="min-h-11 shrink-0 rounded-xl border border-border-accent bg-surface px-4 py-2 text-sm font-semibold text-accent-text transition hover:bg-surface-highlighted"
            >
              Close
            </button>
          </div>

          <label className="mt-3 block">
            <span className="sr-only">Search the food catalog</span>
            <input
              ref={searchInputRef}
              type="search"
              value={query}
              onChange={(event) => {
                requestIdRef.current += 1;
                setQuery(event.target.value);
                setStartLetter("");
                setCatalogFoods([]);
                setNextOffset(0);
                setMessage(null);
                scrollRef.current?.scrollTo({ top: 0 });
              }}
              placeholder="Search within the catalog..."
              className="min-h-11 w-full rounded-2xl border border-border bg-surface px-4 py-2.5 text-sm text-text-primary outline-none transition focus:border-focus"
            />
          </label>

          <div className="mt-2 flex gap-2 overflow-x-auto pb-1" aria-label="Browse filters">
            {(
              [
                ["all", "All"],
                ["catalog", "Catalog"],
                ["added", "Scanned / added"],
                ["pinned", "Pinned"],
              ] as const
            ).map(([value, label]) => (
              <button
                key={value}
                type="button"
                aria-pressed={filter === value}
                onClick={() => {
                  if (filter === value) return;
                  requestIdRef.current += 1;
                  setFilter(value);
                  setCatalogFoods([]);
                  setNextOffset(0);
                  setMessage(null);
                  setIsLoading(false);
                  scrollRef.current?.scrollTo({ top: 0 });
                }}
                className={`min-h-9 shrink-0 rounded-full border px-3 py-1.5 text-xs font-semibold transition ${
                  filter === value
                    ? "border-border-accent bg-surface-highlighted text-accent-text"
                    : "border-border bg-surface text-text-secondary"
                }`}
              >
                {label}
              </button>
            ))}
          </div>

          <nav className="mt-1 flex gap-1 overflow-x-auto pb-1" aria-label="Browse foods by letter">
            {ALPHABET.map((letter) => (
              <button
                key={letter}
                type="button"
                aria-label={`Jump to foods starting at ${letter}`}
                aria-pressed={startLetter === letter}
                onClick={() => {
                  if (startLetter === letter) {
                    scrollRef.current?.scrollTo({ top: 0, behavior: "smooth" });
                    return;
                  }
                  requestIdRef.current += 1;
                  setQuery("");
                  setStartLetter(letter);
                  setCatalogFoods([]);
                  setNextOffset(0);
                  setMessage(null);
                  setIsLoading(false);
                  scrollRef.current?.scrollTo({ top: 0 });
                }}
                className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-xs font-bold transition ${
                  startLetter === letter
                    ? "bg-action-primary text-action-primary-foreground"
                    : "bg-surface-subtle text-text-secondary hover:text-text-strong"
                }`}
              >
                {letter}
              </button>
            ))}
          </nav>
        </header>

        <div ref={scrollRef} className="min-h-0 flex-1 overflow-y-auto overscroll-contain px-3 pb-[max(1.5rem,env(safe-area-inset-bottom))] sm:px-5">
          {sections.map(([letter, choices]) => (
            <section key={letter} aria-labelledby={`food-section-${letter}`}>
              <h3
                id={`food-section-${letter}`}
                className="sticky top-0 z-10 -mx-3 border-y border-border bg-surface-muted/95 px-4 py-1.5 text-xs font-bold uppercase tracking-[0.18em] text-text-secondary backdrop-blur sm:-mx-5 sm:px-6"
              >
                {letter}
              </h3>
              <div className="divide-y divide-border-subtle">
                {choices.map((choice) => {
                  const key = choiceKey(choice);
                  const name = choiceName(choice);
                  const isPinned = pinnedKeys.has(key);
                  return (
                    <div key={key} className="flex min-h-[4.25rem] items-stretch">
                      <button
                        type="button"
                        onClick={() => onSelect(choice)}
                        className="min-w-0 flex-1 py-3 pr-3 text-left transition hover:bg-surface-subtle"
                      >
                        <span className="block text-sm font-semibold text-text-strong">{name}</span>
                        <span className="mt-0.5 block text-xs leading-4 text-text-secondary">
                          {formatMacroLine(choiceNutrients(choice))}
                        </span>
                      </button>
                      <button
                        type="button"
                        aria-label={`${isPinned ? "Unpin" : "Pin"} ${name}`}
                        title={`${isPinned ? "Unpin" : "Pin"} ${name}`}
                        disabled={updatingPinnedKey === key}
                        onClick={() => onTogglePinned(choice)}
                        className={`flex w-12 shrink-0 items-center justify-center transition disabled:opacity-50 ${
                          isPinned ? "text-accent-text" : "text-text-muted hover:text-accent-text"
                        }`}
                      >
                        <PinIcon active={isPinned} />
                      </button>
                    </div>
                  );
                })}
              </div>
            </section>
          ))}

          {isLoading ? (
            <p className="px-2 py-5 text-center text-sm text-text-secondary">Loading foods...</p>
          ) : null}
          {!isLoading && filter === "pinned" && visibleChoices.length === 0 ? (
            <p className="mx-auto max-w-md px-4 py-10 text-center text-sm leading-6 text-text-secondary">
              {pinnedFoods.length === 0
                ? "Pin foods from search or browse to keep them here."
                : "No pinned foods match these browse controls."}
            </p>
          ) : null}
          {message ? (
            <p className="mx-auto max-w-md px-4 py-10 text-center text-sm leading-6 text-text-secondary">{message}</p>
          ) : null}
          {!isLoading && catalogFoods.length >= MAX_RENDERED_FOODS && nextOffset !== null ? (
            <p className="mx-auto max-w-md px-4 py-6 text-center text-xs leading-5 text-text-muted">
              Use search or A–Z to narrow the catalog further.
            </p>
          ) : null}
          <div ref={loadSentinelRef} className="h-1" aria-hidden="true" />
        </div>
      </section>
    </div>,
    document.body,
  );
}
