"use client";

import { FormEvent, useMemo, useState } from "react";

import {
  fetchCanonicalFoodServingUnits,
  searchCanonicalFoods,
} from "@/lib/canonicalFoodApi";
import { searchPersonalFoods } from "@/lib/personalFoodApi";
import { createSavedMeal, updateSavedMeal } from "@/lib/savedMealApi";
import {
  CanonicalFoodSearchResult,
  CanonicalFoodServingUnit,
} from "@/types/canonicalFood";
import { PersonalFood } from "@/types/personalFood";
import {
  SavedMeal,
  SavedMealItemMutation,
  SavedMealMacros,
} from "@/types/savedMeal";

interface SavedMealEditorProps {
  userId: number;
  initialMeal?: SavedMeal;
  onSaved: (meal: SavedMeal) => void;
  onCancel: () => void;
}

interface DraftItem {
  key: string;
  displayName: string;
  mutation: SavedMealItemMutation;
  resolvedGrams: number;
  quantityDisplay: string;
  macros: SavedMealMacros;
}

type SearchChoice =
  | { foodType: "canonical"; result: CanonicalFoodSearchResult }
  | { foodType: "personal"; result: PersonalFood };

const MEAL_TYPES = ["breakfast", "lunch", "dinner", "snack", "other"];

function initialDraftItems(meal?: SavedMeal): DraftItem[] {
  return (meal?.items ?? []).map((item) => ({
    key: `saved-${item.id}`,
    displayName: item.display_name,
    mutation:
      item.food_type === "canonical"
        ? item.canonical_serving_unit_id && item.serving_quantity
          ? {
              food_type: "canonical",
              canonical_food_id: item.canonical_food_id ?? undefined,
              serving_unit_id: item.canonical_serving_unit_id,
              serving_quantity: item.serving_quantity,
            }
          : {
              food_type: "canonical",
              canonical_food_id: item.canonical_food_id ?? undefined,
              grams: item.resolved_grams,
            }
        : item.amount_source === "personal_serving" && item.serving_quantity
          ? {
              food_type: "personal",
              personal_food_id: item.personal_food_id ?? undefined,
              personal_serving_quantity: item.serving_quantity,
            }
          : {
              food_type: "personal",
              personal_food_id: item.personal_food_id ?? undefined,
              grams: item.resolved_grams,
            },
    resolvedGrams: item.resolved_grams,
    quantityDisplay: item.quantity_display.display_text,
    macros: {
      calories: item.calories,
      protein_g: item.protein_g,
      carbs_g: item.carbs_g,
      fat_g: item.fat_g,
    },
  }));
}

export function SavedMealEditor({
  userId,
  initialMeal,
  onSaved,
  onCancel,
}: SavedMealEditorProps) {
  const [name, setName] = useState(initialMeal?.display_name ?? "");
  const [defaultMealType, setDefaultMealType] = useState(
    initialMeal?.default_meal_type ?? "",
  );
  const [instructionsText, setInstructionsText] = useState(
    (initialMeal?.cooking_instructions ?? []).join("\n"),
  );
  const [items, setItems] = useState<DraftItem[]>(() => initialDraftItems(initialMeal));
  const [query, setQuery] = useState("");
  const [canonicalResults, setCanonicalResults] = useState<
    CanonicalFoodSearchResult[]
  >([]);
  const [personalResults, setPersonalResults] = useState<PersonalFood[]>([]);
  const [choice, setChoice] = useState<SearchChoice | null>(null);
  const [servingUnits, setServingUnits] = useState<CanonicalFoodServingUnit[]>([]);
  const [amountMode, setAmountMode] = useState("grams");
  const [amount, setAmount] = useState("100");
  const [isSearching, setIsSearching] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const draftMacros = useMemo(() => aggregateDraftMacros(items), [items]);

  async function handleSearch() {
    if (query.trim().length < 2) {
      setError("Enter at least two characters.");
      return;
    }
    setIsSearching(true);
    setError(null);
    try {
      const [canonical, personal] = await Promise.all([
        searchCanonicalFoods(query, 6, userId),
        searchPersonalFoods(userId, query, 6),
      ]);
      setCanonicalResults(canonical.results);
      setPersonalResults(personal.results.filter((food) => food.active));
    } catch (searchError) {
      setError(searchError instanceof Error ? searchError.message : "Search failed.");
    } finally {
      setIsSearching(false);
    }
  }

  async function chooseFood(nextChoice: SearchChoice) {
    setChoice(nextChoice);
    setAmount("1");
    setServingUnits([]);
    if (nextChoice.foodType === "canonical") {
      setAmountMode("grams");
      setAmount("100");
      try {
        const response = await fetchCanonicalFoodServingUnits(
          nextChoice.result.canonical_food_id,
        );
        setServingUnits(response.serving_units);
      } catch {
        setServingUnits([]);
      }
    } else if (nextChoice.result.current_revision.serving_grams) {
      setAmountMode("personal-serving");
    } else {
      setAmountMode("grams");
      setAmount("100");
    }
  }

  function addChoice() {
    if (!choice) {
      return;
    }
    const numericAmount = Number(amount);
    if (!Number.isFinite(numericAmount) || numericAmount <= 0) {
      setError("Amount must be greater than zero.");
      return;
    }
    const draft = draftFromChoice(
      choice,
      amountMode,
      numericAmount,
      servingUnits,
    );
    if (!draft) {
      setError("Choose a valid amount or serving.");
      return;
    }
    setItems((current) => [...current, draft]);
    setChoice(null);
    setCanonicalResults([]);
    setPersonalResults([]);
    setQuery("");
    setError(null);
  }

  function changeItemGrams(index: number, value: string) {
    const grams = Number(value);
    if (!Number.isFinite(grams) || grams <= 0) {
      return;
    }
    setItems((current) =>
      current.map((item, itemIndex) => {
        if (itemIndex !== index) {
          return item;
        }
        const scale = grams / item.resolvedGrams;
        return {
          ...item,
          mutation: {
            food_type: item.mutation.food_type,
            ...(item.mutation.food_type === "canonical"
              ? { canonical_food_id: item.mutation.canonical_food_id }
              : { personal_food_id: item.mutation.personal_food_id }),
            grams,
          },
          resolvedGrams: grams,
          quantityDisplay: `${formatDraftGrams(grams)} g`,
          macros: scaleMacros(item.macros, scale),
        };
      }),
    );
  }

  function moveItem(index: number, direction: -1 | 1) {
    setItems((current) => {
      const destination = index + direction;
      if (destination < 0 || destination >= current.length) {
        return current;
      }
      const next = [...current];
      [next[index], next[destination]] = [next[destination], next[index]];
      return next;
    });
  }

  async function handleSave(event: FormEvent) {
    event.preventDefault();
    if (!name.trim() || items.length === 0) {
      setError("Add a meal name and at least one item.");
      return;
    }
    setIsSaving(true);
    setError(null);
    const payload = {
      user_id: userId,
      display_name: name,
      default_meal_type: defaultMealType || null,
      cooking_instructions: instructionsText
        .split("\n")
        .map((step) => step.trim())
        .filter(Boolean),
      source_type: initialMeal?.source_type ?? "manual",
      source_provider: initialMeal?.source_provider ?? null,
      source_model: initialMeal?.source_model ?? null,
      items: items.map((item) => item.mutation),
    };
    try {
      const response = initialMeal
        ? await updateSavedMeal(initialMeal.id, payload)
        : await createSavedMeal(payload);
      onSaved(response.saved_meal);
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Unable to save meal.");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <form onSubmit={handleSave} className="space-y-4" aria-label="Recipe editor">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h3 className="text-base font-semibold text-text-strong">
            {initialMeal ? "Edit recipe" : "Create recipe manually"}
          </h3>
          <p className="text-xs text-text-muted">
            Amounts are saved as stable grams in the shared recipe system.
          </p>
        </div>
        <button
          type="button"
          onClick={onCancel}
          className="rounded-lg border border-border-subtle px-3 py-2 text-sm font-semibold text-text-body"
        >
          Cancel
        </button>
      </div>

      <label className="block text-sm font-medium text-text-body">
        Cooking instructions <span className="font-normal text-text-muted">Optional</span>
        <textarea
          value={instructionsText}
          onChange={(event) => setInstructionsText(event.target.value)}
          rows={4}
          placeholder="Enter one step per line."
          className="mt-1 w-full rounded-xl border border-border bg-surface px-3 py-2.5 text-text-strong"
        />
      </label>

      <div className="grid gap-3 sm:grid-cols-2">
        <label className="text-sm font-medium text-text-body">
          Meal name
          <input
            value={name}
            onChange={(event) => setName(event.target.value)}
            maxLength={120}
            required
            className="mt-1 w-full rounded-xl border border-border bg-surface px-3 py-2.5 text-text-strong"
          />
        </label>
        <label className="text-sm font-medium text-text-body">
          Default meal type
          <select
            value={defaultMealType}
            onChange={(event) => setDefaultMealType(event.target.value)}
            className="mt-1 w-full rounded-xl border border-border bg-surface px-3 py-2.5 text-text-strong"
          >
            <option value="">Choose when logging</option>
            {MEAL_TYPES.map((mealType) => (
              <option key={mealType} value={mealType}>
                {mealType[0].toUpperCase() + mealType.slice(1)}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="grid grid-cols-4 gap-1.5 rounded-xl bg-surface-muted p-2 text-center">
        <Macro label="Cal" value={draftMacros.calories} />
        <Macro label="Protein" value={draftMacros.protein_g} suffix="g" />
        <Macro label="Carbs" value={draftMacros.carbs_g} suffix="g" />
        <Macro label="Fat" value={draftMacros.fat_g} suffix="g" />
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <h4 className="text-sm font-semibold text-text-strong">Items</h4>
          <span className="text-xs text-text-muted">{items.length} added</span>
        </div>
        {items.map((item, index) => (
          <div
            key={item.key}
            className="grid gap-2 rounded-xl border border-border-subtle bg-surface-muted/60 p-2.5 sm:grid-cols-[1fr_auto]"
          >
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold text-text-strong">
                {index + 1}. {item.displayName}
              </p>
              <p className="mt-0.5 text-xs font-medium text-text-body">
                {item.quantityDisplay}
              </p>
              <label className="mt-1 flex items-center gap-2 text-xs text-text-muted">
                Canonical grams
                <input
                  type="number"
                  min="0.01"
                  max="5000"
                  step="0.01"
                  value={item.resolvedGrams}
                  onChange={(event) => changeItemGrams(index, event.target.value)}
                  className="w-24 rounded-lg border border-border bg-surface px-2 py-1.5 text-sm text-text-strong"
                  aria-label={`${item.displayName} grams`}
                />
              </label>
            </div>
            <div className="flex items-center gap-1">
              <button type="button" onClick={() => moveItem(index, -1)} disabled={index === 0} className="rounded-lg border border-border-subtle px-2 py-1.5 text-xs disabled:opacity-40" aria-label={`Move ${item.displayName} up`}>↑</button>
              <button type="button" onClick={() => moveItem(index, 1)} disabled={index === items.length - 1} className="rounded-lg border border-border-subtle px-2 py-1.5 text-xs disabled:opacity-40" aria-label={`Move ${item.displayName} down`}>↓</button>
              <button type="button" onClick={() => setItems((current) => current.filter((_, itemIndex) => itemIndex !== index))} className="rounded-lg border border-danger-action px-2 py-1.5 text-xs font-semibold text-danger-action">Remove</button>
            </div>
          </div>
        ))}
      </div>

      <div className="rounded-xl border border-border-subtle p-3">
        <div className="flex gap-2">
          <label className="sr-only" htmlFor="meal-food-search">Search foods</label>
          <input id="meal-food-search" value={query} onChange={(event) => setQuery(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter") { event.preventDefault(); void handleSearch(); } }} placeholder="Search canonical or My Foods" className="min-w-0 flex-1 rounded-xl border border-border bg-surface px-3 py-2.5 text-sm text-text-strong" />
          <button type="button" onClick={() => void handleSearch()} disabled={isSearching} className="rounded-xl bg-action-primary px-3 py-2.5 text-sm font-semibold text-action-primary-foreground hover:bg-action-primary-hover disabled:opacity-60">{isSearching ? "Searching…" : "Search"}</button>
        </div>
        {(canonicalResults.length > 0 || personalResults.length > 0) && !choice ? (
          <div className="mt-2 max-h-56 space-y-1 overflow-y-auto">
            {canonicalResults.map((food) => (
              <button key={`canonical-${food.canonical_food_id}`} type="button" onClick={() => void chooseFood({ foodType: "canonical", result: food })} className="flex w-full items-center justify-between rounded-lg px-2 py-2 text-left hover:bg-surface-muted">
                <span className="truncate text-sm text-text-strong">{food.display_name}</span><span className="ml-2 text-[0.68rem] font-semibold uppercase text-text-muted">Catalog</span>
              </button>
            ))}
            {personalResults.map((food) => (
              <button key={`personal-${food.id}`} type="button" onClick={() => void chooseFood({ foodType: "personal", result: food })} className="flex w-full items-center justify-between rounded-lg px-2 py-2 text-left hover:bg-surface-muted">
                <span className="truncate text-sm text-text-strong">{food.display_name}</span><span className="ml-2 text-[0.68rem] font-semibold uppercase text-text-muted">My Food</span>
              </button>
            ))}
          </div>
        ) : null}
        {choice ? (
          <div className="mt-3 space-y-2 rounded-xl bg-surface-muted p-3">
            <p className="text-sm font-semibold text-text-strong">{choice.result.display_name}</p>
            <div className="grid gap-2 sm:grid-cols-[1fr_8rem_auto]">
              <select value={amountMode} onChange={(event) => { const nextMode = event.target.value; setAmountMode(nextMode); setAmount(nextMode === "grams" ? "100" : "1"); }} className="rounded-lg border border-border bg-surface px-2 py-2 text-sm text-text-strong">
                <option value="grams">Grams</option>
                {choice.foodType === "canonical" ? servingUnits.map((unit) => <option key={unit.id} value={`serving-${unit.id}`}>{unit.display_label}</option>) : null}
                {choice.foodType === "personal" && choice.result.current_revision.serving_grams ? <option value="personal-serving">{choice.result.current_revision.serving_name ?? "Serving"}</option> : null}
              </select>
              <input type="number" min="0.01" step="0.01" value={amount} onChange={(event) => setAmount(event.target.value)} aria-label="Item amount" className="rounded-lg border border-border bg-surface px-2 py-2 text-sm text-text-strong" />
              <button type="button" onClick={addChoice} className="rounded-lg bg-action-primary px-3 py-2 text-sm font-semibold text-action-primary-foreground hover:bg-action-primary-hover">Add item</button>
            </div>
          </div>
        ) : null}
      </div>

      {error ? <p role="alert" className="text-sm text-danger-foreground">{error}</p> : null}
      <button type="submit" disabled={isSaving} className="w-full rounded-xl bg-action-primary px-4 py-3 text-sm font-semibold text-action-primary-foreground hover:bg-action-primary-hover disabled:opacity-60">
        {isSaving ? "Saving…" : initialMeal ? "Save changes" : "Save meal"}
      </button>
    </form>
  );
}

function draftFromChoice(choice: SearchChoice, amountMode: string, amount: number, servingUnits: CanonicalFoodServingUnit[]): DraftItem | null {
  let mutation: SavedMealItemMutation;
  let grams: number;
  let quantityDisplay: string;
  let per100: SavedMealMacros;
  if (choice.foodType === "canonical") {
    const nutrients = choice.result.nutrient_summary;
    per100 = { calories: nutrients?.calories_per_100g ?? null, protein_g: nutrients?.protein_g_per_100g ?? null, carbs_g: nutrients?.carbohydrate_g_per_100g ?? null, fat_g: nutrients?.fat_g_per_100g ?? null };
    if (amountMode.startsWith("serving-")) {
      const unit = servingUnits.find((candidate) => candidate.id === Number(amountMode.slice(8)));
      if (!unit) return null;
      grams = unit.grams_per_unit * amount;
      mutation = { food_type: "canonical", canonical_food_id: choice.result.canonical_food_id, serving_unit_id: unit.id, serving_quantity: amount };
      const primary = amount === 1 ? unit.display_name : `${amount} × ${unit.display_name}`;
      quantityDisplay = `${primary} (${formatDraftGrams(grams)} g)`;
    } else {
      grams = amount;
      mutation = { food_type: "canonical", canonical_food_id: choice.result.canonical_food_id, grams };
      quantityDisplay = `${formatDraftGrams(grams)} g`;
    }
  } else {
    const revision = choice.result.current_revision;
    per100 = { calories: revision.calories_per_100g, protein_g: revision.protein_g_per_100g, carbs_g: revision.carbs_g_per_100g, fat_g: revision.fat_g_per_100g };
    if (amountMode === "personal-serving" && revision.serving_grams) {
      grams = revision.serving_grams * amount;
      mutation = { food_type: "personal", personal_food_id: choice.result.id, personal_serving_quantity: amount };
      const servingName = revision.serving_name ?? "serving";
      quantityDisplay = `${amount} ${servingName}${amount === 1 ? "" : "s"} (${formatDraftGrams(grams)} g)`;
    } else {
      grams = amount;
      mutation = { food_type: "personal", personal_food_id: choice.result.id, grams };
      quantityDisplay = `${formatDraftGrams(grams)} g`;
    }
  }
  return { key: `${choice.foodType}-${Date.now()}-${Math.random()}`, displayName: choice.result.display_name, mutation, resolvedGrams: grams, quantityDisplay, macros: scaleMacros(per100, grams / 100) };
}

function formatDraftGrams(value: number): string {
  return value.toFixed(2).replace(/\.00$/, "").replace(/(\.\d)0$/, "$1");
}

function scaleMacros(macros: SavedMealMacros, scale: number): SavedMealMacros {
  return { calories: macros.calories === null ? null : macros.calories * scale, protein_g: macros.protein_g === null ? null : macros.protein_g * scale, carbs_g: macros.carbs_g === null ? null : macros.carbs_g * scale, fat_g: macros.fat_g === null ? null : macros.fat_g * scale };
}

function aggregateDraftMacros(items: DraftItem[]): SavedMealMacros {
  const total = (key: keyof SavedMealMacros) => items.length > 0 && items.every((item) => item.macros[key] !== null) ? items.reduce((sum, item) => sum + Number(item.macros[key]), 0) : null;
  return { calories: total("calories"), protein_g: total("protein_g"), carbs_g: total("carbs_g"), fat_g: total("fat_g") };
}

function Macro({ label, value, suffix = "" }: { label: string; value: number | null; suffix?: string }) {
  return <div><p className="text-[0.65rem] uppercase tracking-wide text-text-muted">{label}</p><p className="text-sm font-semibold text-text-strong">{value === null ? "—" : `${Math.round(value)}${suffix}`}</p></div>;
}
