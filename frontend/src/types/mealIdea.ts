import { AIRunTelemetry } from "@/types/aiRunTelemetry";
import { QuantityPresentation } from "@/types/measurementDisplay";

export type MealIdeaProvider = "local" | "openai";

export type MealIdeaSteering =
  | "sweet"
  | "savory"
  | "quick"
  | "high_volume"
  | "comfort"
  | "light_fresh"
  | "portable"
  | "surprise_me";

export type MealIdeaMealType =
  | "breakfast"
  | "lunch"
  | "dinner"
  | "snack"
  | "dessert";

export interface GroundedMealIdeaIngredient {
  canonical_food_id: number;
  display_name: string;
  amount_grams: number;
  quantity_display: QuantityPresentation;
  is_available: boolean;
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
}

export interface GroundedMealIdea {
  name: string;
  meal_type: MealIdeaMealType;
  ingredients: GroundedMealIdeaIngredient[];
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  available_ingredient_count: number;
}

export interface MealIdeasResponse {
  success: true;
  provider: MealIdeaProvider;
  model: string;
  target_date: string;
  ideas: GroundedMealIdea[];
  rejected_concept_count: number;
  context_signals: {
    usable_catalog_food_count: number;
    available_ingredient_count: number;
    food_preference_count: number;
    recent_food_count: number;
    nutrition_context_available: boolean;
  };
  telemetry: AIRunTelemetry;
}

export interface MealIdeaGenerationHistoryItem {
  id: number;
  created_at: string;
  request: {
    provider: MealIdeaProvider;
    model: string;
    creative_steering: MealIdeaSteering;
    meal_type: MealIdeaMealType | null;
    intent: string | null;
  };
  result: MealIdeasResponse;
}

export interface MealIdeaGenerationHistoryResponse {
  success: true;
  user_id: number;
  results: MealIdeaGenerationHistoryItem[];
}

export interface MealInstructionsResponse {
  success: true;
  provider: MealIdeaProvider;
  model: string;
  instructions: string[];
  telemetry: AIRunTelemetry;
}

export interface MealIdeaModelOption {
  id: string;
  label: string;
}

export interface MealIdeaProviderModelOptions {
  models: MealIdeaModelOption[];
  default_model: string;
  source: "ollama" | "configured_fallback" | "curated";
  message: string | null;
}

export interface MealIdeaModelOptionsResponse {
  providers: Record<MealIdeaProvider, MealIdeaProviderModelOptions>;
}

export interface GenerateMealIdeasInput {
  userId: number;
  targetDate: string;
  provider: MealIdeaProvider;
  model: string;
  creativeSteering: MealIdeaSteering;
  mealType: MealIdeaMealType | null;
  intent: string;
  generationNonce: string;
  previousIdeaNames: string[];
  recentGeneratedFoodNames: string[];
}
