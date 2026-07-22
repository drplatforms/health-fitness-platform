import { AIRunTelemetry } from "@/types/aiRunTelemetry";

export type SavedMealFoodType = "canonical" | "personal";

export const SAVED_MEAL_CHANGED_EVENT = "fitness-ai:saved-meal-changed";

export interface SavedMealMacros {
  calories: number | null;
  protein_g: number | null;
  carbs_g: number | null;
  fat_g: number | null;
}

export interface SavedMealItem {
  id: number;
  item_order: number;
  food_type: SavedMealFoodType;
  canonical_food_id: number | null;
  personal_food_id: number | null;
  display_name: string;
  active: boolean;
  resolved_grams: number;
  canonical_serving_unit_id: number | null;
  serving_quantity: number | null;
  serving_display_snapshot: string | null;
  amount_source: "grams" | "canonical_serving" | "personal_serving" | string;
  validation_status: "valid" | "invalid";
  validation_reason: string | null;
  calories: number | null;
  protein_g: number | null;
  carbs_g: number | null;
  fat_g: number | null;
}

export interface SavedMeal {
  id: number;
  user_id: number;
  display_name: string;
  default_meal_type: string | null;
  active: boolean;
  created_at: string;
  updated_at: string;
  cooking_instructions: string[];
  instruction_telemetry: AIRunTelemetry | null;
  source_type: "manual" | "ai";
  source_provider: string | null;
  source_model: string | null;
  item_count: number;
  items: SavedMealItem[];
  current_macros: SavedMealMacros;
  validation_status: "valid" | "invalid" | "empty";
  invalid_item_count: number;
}

export interface SavedMealItemMutation {
  food_type: SavedMealFoodType;
  canonical_food_id?: number;
  personal_food_id?: number;
  grams?: number;
  serving_unit_id?: number;
  serving_quantity?: number;
  personal_serving_quantity?: number;
}

export interface SavedMealMutation {
  user_id: number;
  display_name: string;
  default_meal_type?: string | null;
  cooking_instructions?: string[];
  instruction_telemetry?: AIRunTelemetry | null;
  source_type?: "manual" | "ai";
  source_provider?: string | null;
  source_model?: string | null;
  items: SavedMealItemMutation[];
}

export interface ScaledSavedMealRecipe {
  saved_meal_id: number;
  multiplier: 1 | 2 | 3 | 4;
  ingredients: Array<{
    food_type: SavedMealFoodType;
    canonical_food_id: number | null;
    personal_food_id: number | null;
    display_name: string;
    amount_grams: number;
  }>;
  current_macros: SavedMealMacros;
}

export interface SavedMealResponse {
  success: boolean;
  user_id: number;
  saved_meal: SavedMeal;
}

export interface SavedMealsResponse {
  success: boolean;
  user_id: number;
  results: SavedMeal[];
}

export interface SavedMealLogResponse {
  success: boolean;
  user_id: number;
  saved_meal_id: number;
  meal_name: string;
  entry_date: string;
  meal_type: string;
  logged_item_count: number;
  logged_entries: Array<{
    entry_id: number;
    food_type: SavedMealFoodType;
    canonical_food_id: number | null;
    personal_food_id: number | null;
    personal_food_revision_id: number | null;
    display_name: string;
    grams: number;
    calories: number | null;
    protein_g: number | null;
    carbs_g: number | null;
    fat_g: number | null;
  }>;
  aggregate_logged_macros: SavedMealMacros;
}
