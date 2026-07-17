export type NutritionGapMacro =
  | "calories"
  | "protein_g"
  | "carbohydrate_g"
  | "fat_g";

export interface NutritionFoodSuggestion {
  canonical_food_id: number;
  display_name: string;
  suggested_grams: number;
  estimated_calories: number | null;
  estimated_protein_g: number | null;
  estimated_carbohydrate_g: number | null;
  estimated_fat_g: number | null;
  macro_gap_addressed: NutritionGapMacro;
  suggestion_summary: string;
  confidence: "Limited" | "Low" | "Moderate" | "High";
  reason_codes: string[];
  limitations: string[];
}

export interface NutritionFoodSuggestionsResponse {
  success: boolean;
  user_id: number;
  suggestion_date: string;
  primary_gap: NutritionGapMacro | null | "none";
  macro_gaps: unknown[];
  suggestions: NutritionFoodSuggestion[];
  confidence: "Limited" | "Low" | "Moderate" | "High";
  reason_codes: string[];
  limitations: string[];
}
