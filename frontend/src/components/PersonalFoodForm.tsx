"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import {
  createPersonalFood,
  fetchPersonalFood,
  updatePersonalFood,
} from "@/lib/personalFoodApi";
import {
  PersonalFoodInputBasis,
  PersonalFoodUpsertRequest,
} from "@/types/personalFood";

interface PersonalFoodFormProps {
  mode: "create" | "edit";
  userId: number;
  personalFoodId?: number;
  targetDate?: string;
}

const nutrientFields = [
  { key: "calories", label: "Calories" },
  { key: "protein_g", label: "Protein" },
  { key: "carbs_g", label: "Carbohydrates" },
  { key: "fat_g", label: "Fat" },
] as const;

type NutrientKey = (typeof nutrientFields)[number]["key"];
type NutrientState = Record<NutrientKey, string>;

const emptyNutrients: NutrientState = {
  calories: "",
  protein_g: "",
  carbs_g: "",
  fat_g: "",
};

function optionalNumber(value: string): number | undefined {
  if (!value.trim()) {
    return undefined;
  }
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : undefined;
}

export function PersonalFoodForm({
  mode,
  userId,
  personalFoodId,
  targetDate,
}: PersonalFoodFormProps) {
  const router = useRouter();
  const [displayName, setDisplayName] = useState("");
  const [brandName, setBrandName] = useState("");
  const [inputBasis, setInputBasis] =
    useState<PersonalFoodInputBasis>("nutrition_label");
  const [servingName, setServingName] = useState("");
  const [servingGrams, setServingGrams] = useState("");
  const [nutrients, setNutrients] = useState<NutrientState>(emptyNutrients);
  const [isLoading, setIsLoading] = useState(mode === "edit");
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [basisMessage, setBasisMessage] = useState<string | null>(null);

  useEffect(() => {
    if (mode !== "edit" || personalFoodId === undefined) {
      return;
    }
    let isActive = true;
    void fetchPersonalFood(userId, personalFoodId)
      .then((response) => {
        if (!isActive) {
          return;
        }
        const food = response.personal_food;
        const revision = food.current_revision;
        setDisplayName(food.display_name);
        setBrandName(food.brand_name ?? "");
        setInputBasis(revision.input_basis);
        setServingName(revision.serving_name ?? "");
        setServingGrams(
          revision.serving_grams === null ? "" : String(revision.serving_grams),
        );
        setNutrients({
          calories:
            revision.entered_calories === null
              ? ""
              : String(revision.entered_calories),
          protein_g:
            revision.entered_protein_g === null
              ? ""
              : String(revision.entered_protein_g),
          carbs_g:
            revision.entered_carbs_g === null
              ? ""
              : String(revision.entered_carbs_g),
          fat_g:
            revision.entered_fat_g === null
              ? ""
              : String(revision.entered_fat_g),
        });
      })
      .catch((loadError) => {
        if (isActive) {
          setError(
            loadError instanceof Error
              ? loadError.message
              : "Unable to load this personal food.",
          );
        }
      })
      .finally(() => {
        if (isActive) {
          setIsLoading(false);
        }
      });
    return () => {
      isActive = false;
    };
  }, [mode, personalFoodId, userId]);

  async function submit() {
    setError(null);
    setSuccess(null);
    if (!displayName.trim()) {
      setError("Food name is required.");
      return;
    }
    const parsedNutrients = {
      calories: optionalNumber(nutrients.calories),
      protein_g: optionalNumber(nutrients.protein_g),
      carbs_g: optionalNumber(nutrients.carbs_g),
      fat_g: optionalNumber(nutrients.fat_g),
    };
    if (Object.values(parsedNutrients).every((value) => value === undefined)) {
      setError("Enter at least one nutrition value.");
      return;
    }
    const parsedServingGrams = optionalNumber(servingGrams);
    if (inputBasis === "nutrition_label" && parsedServingGrams === undefined) {
      setError("Serving weight in grams is required.");
      return;
    }

    const payload: PersonalFoodUpsertRequest = {
      user_id: userId,
      display_name: displayName.trim(),
      brand_name: brandName.trim(),
      input_basis: inputBasis,
      ...(inputBasis === "nutrition_label"
        ? {
            serving_name: servingName.trim(),
            serving_grams: parsedServingGrams,
          }
        : {}),
      ...parsedNutrients,
    };

    setIsSaving(true);
    try {
      if (mode === "create") {
        await createPersonalFood(payload);
        const params = new URLSearchParams({ user_id: String(userId) });
        if (targetDate) {
          params.set("date", targetDate);
        }
        router.push(`/personal-foods?${params.toString()}`);
        return;
      }
      if (personalFoodId === undefined) {
        throw new Error("Personal food ID is unavailable.");
      }
      await updatePersonalFood(personalFoodId, payload);
      setSuccess("Food updated for future logs.");
      router.refresh();
    } catch (saveError) {
      setError(
        saveError instanceof Error
          ? saveError.message
          : "Unable to save this personal food.",
      );
    } finally {
      setIsSaving(false);
    }
  }

  if (isLoading) {
    return (
      <p className="rounded-2xl bg-neutral-surface px-4 py-3 text-sm text-neutral-foreground">
        Loading food...
      </p>
    );
  }

  return (
    <div className="space-y-5">
      <div className="space-y-3">
        <label className="block space-y-1.5">
          <span className="text-sm font-semibold text-text-primary">Food name</span>
          <input
            value={displayName}
            onChange={(event) => setDisplayName(event.target.value)}
            required
            className="w-full rounded-2xl border border-border bg-surface px-4 py-2.5 text-sm text-text-primary outline-none focus:border-focus"
          />
        </label>
        <label className="block space-y-1.5">
          <span className="text-sm font-semibold text-text-primary">Brand (optional)</span>
          <input
            value={brandName}
            onChange={(event) => setBrandName(event.target.value)}
            className="w-full rounded-2xl border border-border bg-surface px-4 py-2.5 text-sm text-text-primary outline-none focus:border-focus"
          />
        </label>
      </div>

      <fieldset className="space-y-2">
        <legend className="text-sm font-semibold text-text-primary">Nutrition basis</legend>
        <div className="inline-flex rounded-2xl bg-surface-muted p-1">
          {(
            [
              ["nutrition_label", "Nutrition label"],
              ["per_100g", "Per 100g"],
            ] as const
          ).map(([value, label]) => (
            <button
              key={value}
              type="button"
              onClick={() => {
                if (value === inputBasis) {
                  return;
                }
                setInputBasis(value);
                setNutrients(emptyNutrients);
                setError(null);
                setSuccess(null);
                setBasisMessage(
                  "Nutrition values were cleared because the basis changed.",
                );
              }}
              className={`rounded-xl px-3 py-2 text-sm font-semibold transition ${
                inputBasis === value
                  ? "bg-surface text-positive-foreground-strong shadow-sm"
                  : "text-text-secondary hover:text-text-primary"
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </fieldset>

      {inputBasis === "nutrition_label" ? (
        <div className="grid gap-3 sm:grid-cols-2">
          <label className="space-y-1.5">
            <span className="text-sm font-semibold text-text-primary">
              Serving name (optional)
            </span>
            <input
              value={servingName}
              onChange={(event) => setServingName(event.target.value)}
              placeholder="1 cup"
              className="w-full rounded-2xl border border-border bg-surface px-4 py-2.5 text-sm text-text-primary outline-none focus:border-focus"
            />
          </label>
          <label className="space-y-1.5">
            <span className="text-sm font-semibold text-text-primary">
              Serving weight in grams
            </span>
            <input
              type="number"
              min="0"
              step="any"
              value={servingGrams}
              onChange={(event) => setServingGrams(event.target.value)}
              className="w-full rounded-2xl border border-border bg-surface px-4 py-2.5 text-sm text-text-primary outline-none focus:border-focus"
            />
          </label>
        </div>
      ) : null}

      <div className="space-y-2">
        <p className="text-sm font-semibold text-text-primary">
          {inputBasis === "nutrition_label"
            ? "Nutrition per serving"
            : "Nutrition per 100g"}
        </p>
        <div className="grid gap-3 sm:grid-cols-2">
          {nutrientFields.map((field) => (
            <label key={field.key} className="space-y-1.5">
              <span className="text-sm text-text-body">{field.label}</span>
              <input
                type="number"
                min="0"
                step="any"
                value={nutrients[field.key]}
                onChange={(event) =>
                  setNutrients((current) => ({
                    ...current,
                    [field.key]: event.target.value,
                  }))
                }
                className="w-full rounded-2xl border border-border bg-surface px-4 py-2.5 text-sm text-text-primary outline-none focus:border-focus"
              />
            </label>
          ))}
        </div>
        <p className="text-xs leading-5 text-text-secondary">
          Leave anything you do not know blank.
        </p>
        {basisMessage ? (
          <p className="text-xs leading-5 text-text-secondary">{basisMessage}</p>
        ) : null}
      </div>

      {mode === "edit" ? (
        <p className="rounded-2xl bg-neutral-surface px-4 py-3 text-sm text-neutral-foreground">
          Changes apply to future logs. Existing logs stay unchanged.
        </p>
      ) : null}
      {error ? (
        <p className="rounded-2xl bg-danger-surface px-4 py-3 text-sm text-danger-foreground">
          {error}
        </p>
      ) : null}
      {success ? (
        <p className="rounded-2xl bg-positive-surface px-4 py-3 text-sm text-positive-foreground-strong">
          {success}
        </p>
      ) : null}

      <button
        type="button"
        onClick={() => void submit()}
        disabled={isSaving}
        className="inline-flex w-full items-center justify-center rounded-2xl bg-action-primary px-4 py-2.5 text-sm font-semibold text-action-primary-foreground transition hover:bg-action-primary-hover disabled:opacity-60 sm:w-auto"
      >
        {isSaving ? "Saving..." : mode === "create" ? "Add food" : "Save changes"}
      </button>
    </div>
  );
}
