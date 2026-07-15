import { CanonicalFoodNutrientSummary } from "@/types/canonicalFood";

export type PersonalFoodInputBasis = "nutrition_label" | "per_100g";

export interface PersonalFoodRevisionSummary {
  id: number;
  revision_number: number;
  display_name_snapshot: string;
  brand_name_snapshot: string | null;
  input_basis: PersonalFoodInputBasis;
  created_at: string;
}

export interface PersonalFoodRevision extends PersonalFoodRevisionSummary {
  personal_food_id: number;
  serving_name: string | null;
  serving_grams: number | null;
  calories_per_100g: number | null;
  protein_g_per_100g: number | null;
  carbs_g_per_100g: number | null;
  fat_g_per_100g: number | null;
  entered_calories: number | null;
  entered_protein_g: number | null;
  entered_carbs_g: number | null;
  entered_fat_g: number | null;
  source_note: string | null;
}

export interface PersonalFood {
  id: number;
  user_id: number;
  display_name: string;
  brand_name: string | null;
  active: boolean;
  current_revision_id: number;
  created_at: string;
  updated_at: string;
  current_revision: PersonalFoodRevision;
  revisions: PersonalFoodRevisionSummary[];
}

export interface PersonalFoodUpsertRequest {
  user_id: number;
  display_name: string;
  brand_name?: string;
  input_basis: PersonalFoodInputBasis;
  serving_name?: string;
  serving_grams?: number;
  calories?: number;
  protein_g?: number;
  carbs_g?: number;
  fat_g?: number;
}

export interface PersonalFoodResponse {
  success: boolean;
  user_id: number;
  personal_food: PersonalFood;
}

export interface PersonalFoodsResponse {
  success: boolean;
  user_id: number;
  results: PersonalFood[];
}

export interface PersonalFoodLogRequest {
  user_id: number;
  personal_food_id: number;
  entry_date?: string;
  grams?: number;
  serving_quantity?: number;
  meal_type?: string;
}

export interface PersonalFoodLogResponse {
  success: boolean;
  user_id: number;
  logged_food_entry_id: number;
  personal_food_id: number;
  personal_food_revision_id: number;
  display_name: string;
  grams: number;
  serving_quantity?: number;
  logged_date: string;
  meal_type?: string;
  nutrient_summary?: {
    calories?: number;
    protein_g?: number;
    carbs_g?: number;
    fat_g?: number;
  };
}

export interface PersonalFoodLoggedEntry {
  entry_id: number;
  food_type: "personal";
  personal_food_id: number;
  personal_food_revision_id: number;
  food_name: string;
  grams: number;
  meal_type: string | null;
  calories: number | null;
  protein_g: number | null;
  carbs_g: number | null;
  fat_g: number | null;
  serving_name: string | null;
  serving_grams: number | null;
}

export interface PersonalFoodLogsResponse {
  success: boolean;
  user_id: number;
  date: string;
  entries: PersonalFoodLoggedEntry[];
}

export interface PersonalFoodLogUpdateRequest {
  user_id: number;
  entry_id: number;
  entry_date: string;
  grams?: number;
  serving_quantity?: number;
  meal_type?: string;
}

export interface PersonalFoodLogUpdateResponse {
  success: boolean;
  user_id: number;
  entry: PersonalFoodLoggedEntry;
}

export interface PersonalFoodLogDeleteResponse {
  success: boolean;
  user_id: number;
  deleted: boolean;
  entry_id: number;
}

export const PERSONAL_FOOD_LOGGED_EVENT = "personal-food-logged";

export function personalFoodNutrientSummary(
  food: PersonalFood,
): CanonicalFoodNutrientSummary {
  const revision = food.current_revision;
  return {
    ...(revision.calories_per_100g === null
      ? {}
      : { calories_per_100g: revision.calories_per_100g }),
    ...(revision.protein_g_per_100g === null
      ? {}
      : { protein_g_per_100g: revision.protein_g_per_100g }),
    ...(revision.carbs_g_per_100g === null
      ? {}
      : { carbohydrate_g_per_100g: revision.carbs_g_per_100g }),
    ...(revision.fat_g_per_100g === null
      ? {}
      : { fat_g_per_100g: revision.fat_g_per_100g }),
  };
}
