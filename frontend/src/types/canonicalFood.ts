export interface CanonicalFoodNutrientSummary {
  calories_per_100g?: number;
  protein_g_per_100g?: number;
  carbohydrate_g_per_100g?: number;
  fat_g_per_100g?: number;
}

export interface CanonicalFoodSearchResult {
  canonical_food_id: number;
  display_name: string;
  food_type: string;
  default_unit: string | null;
  default_grams: number | null;
  search_priority: number;
  matched_on: string;
  aliases: string[];
  nutrient_summary?: CanonicalFoodNutrientSummary;
  source?: {
    source_name: string;
    source_record_id: string;
  };
}

export interface CanonicalFoodSearchResponse {
  success: boolean;
  query: string;
  results: CanonicalFoodSearchResult[];
}

export interface CanonicalFoodLogRequest {
  user_id: number;
  entry_date?: string;
  canonical_food_id: number;
  grams: number;
  meal_type?: string;
}

export interface CanonicalFoodLogResponse {
  success: boolean;
  user_id: number;
  logged_food_entry_id: number;
  canonical_food_id: number;
  display_name: string;
  grams: number;
  logged_date: string;
  meal_type?: string;
  nutrient_summary?: {
    calories?: number;
    protein_g?: number;
    carbohydrate_g?: number;
    fat_g?: number;
  };
}

export const CANONICAL_FOOD_LOGGED_EVENT = "canonical-food-logged";

export interface CanonicalFoodLoggedEntry {
  entry_id: number;
  canonical_food_id: number;
  food_name: string;
  grams: number;
  meal_type: string | null;
  calories: number | null;
  protein_g: number | null;
  carbs_g: number | null;
  fat_g: number | null;
}

export interface CanonicalFoodLogsResponse {
  success: boolean;
  user_id: number;
  date: string;
  entries: CanonicalFoodLoggedEntry[];
}
