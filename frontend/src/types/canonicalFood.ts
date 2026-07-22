export interface CanonicalFoodNutrientSummary {
  calories_per_100g?: number;
  protein_g_per_100g?: number;
  carbohydrate_g_per_100g?: number;
  fat_g_per_100g?: number;
}

export interface CanonicalFoodSearchResult {
  canonical_food_id: number;
  display_name: string;
  original_display_name?: string;
  custom_display_name?: string | null;
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

export type CanonicalFoodBrowseScope = "all" | "catalog" | "added";

export interface CanonicalFoodBrowseResponse {
  success: boolean;
  scope: CanonicalFoodBrowseScope;
  query: string;
  start_letter: string;
  offset: number;
  next_offset: number | null;
  has_more: boolean;
  results: CanonicalFoodSearchResult[];
}

export interface CanonicalFoodNameMutationResponse {
  success: boolean;
  user_id: number;
  food_name?: {
    canonical_food_id: number;
    display_name: string;
    custom_display_name: string;
    original_display_name: string;
  };
  canonical_food_id?: number;
  deleted?: boolean;
}

export type FoodPreferenceState =
  | "love"
  | "like"
  | "neutral"
  | "dislike"
  | "never_suggest";

export interface FoodPreference {
  canonical_food_id: number;
  preference: Exclude<FoodPreferenceState, "neutral">;
  is_hard_exclusion: boolean;
  display_name: string;
  original_display_name: string;
  custom_display_name: string | null;
  food_type: string;
  default_unit: string | null;
  default_grams: number | null;
  search_priority: number;
  updated_at: string;
}

export interface FoodPreferencesResponse {
  success: boolean;
  user_id: number;
  results: FoodPreference[];
}

export interface FoodPreferenceMutationResponse {
  success: boolean;
  user_id: number;
  food_preference?: Pick<
    FoodPreference,
    "canonical_food_id" | "preference" | "is_hard_exclusion"
  > | {
    canonical_food_id: number;
    preference: "neutral";
    is_hard_exclusion: false;
  };
  canonical_food_id?: number;
  preference?: "neutral";
  is_hard_exclusion?: false;
  deleted?: boolean;
}

export interface CanonicalFoodLogRequest {
  user_id: number;
  entry_date?: string;
  canonical_food_id: number;
  grams?: number;
  serving_unit_id?: number;
  quantity?: number;
  meal_type?: string;
}

export interface CanonicalFoodServingUnit {
  id: number;
  serving_unit_id: number;
  display_label: string;
  display_name: string;
  unit_name: string;
  unit_quantity: number;
  grams_per_unit: number;
  grams_default: number;
  grams_min: number | null;
  grams_max: number | null;
  confidence: "Low" | "Moderate" | "High";
  is_default: boolean;
  amount_source: string;
  source: string | null;
  source_notes: string | null;
  sort_order: number;
}

export interface CanonicalFoodServingUnitsResponse {
  success: boolean;
  canonical_food_id: number;
  display_name: string;
  serving_units: CanonicalFoodServingUnit[];
}

export interface RecentCanonicalFood {
  canonical_food_id: number;
  display_name: string;
  original_display_name: string;
  custom_display_name: string | null;
  last_logged_at: string;
  last_logged_date: string;
  last_meal_type: string | null;
  last_grams: number;
  last_serving_unit_id?: number;
  last_serving_unit_label?: string;
  last_quantity?: number;
  usage_count: number;
  nutrient_summary?: {
    calories?: number;
    protein_g?: number;
    carbohydrate_g?: number;
    fat_g?: number;
  };
}

export interface RecentCanonicalFoodsResponse {
  success: boolean;
  user_id: number;
  results: RecentCanonicalFood[];
}

export type PinnedFoodType = "canonical" | "personal";

export interface PinnedFood {
  food_type: PinnedFoodType;
  food_id: number;
  canonical_food_id?: number;
  personal_food_id?: number;
  display_name: string;
  original_display_name?: string;
  custom_display_name?: string | null;
  default_grams: number | null;
  serving_name?: string | null;
  serving_grams?: number | null;
  pinned_at: string;
  nutrient_summary?: CanonicalFoodNutrientSummary;
}

export interface PinnedFoodsResponse {
  success: boolean;
  user_id: number;
  results: PinnedFood[];
}

export interface PinnedFoodMutationResponse {
  success: boolean;
  user_id: number;
  pinned_food?: PinnedFood;
  deleted?: boolean;
  food_type?: PinnedFoodType;
  food_id?: number;
}

export interface AvailableIngredient {
  canonical_food_id: number;
  display_name: string;
  original_display_name?: string;
  custom_display_name?: string | null;
  food_type: string;
  added_at: string;
}

export interface AvailableIngredientsResponse {
  success: boolean;
  user_id: number;
  results: AvailableIngredient[];
}

export interface AvailableIngredientMutationResponse {
  success: boolean;
  user_id: number;
  available_ingredient?: AvailableIngredient;
  deleted?: boolean;
  canonical_food_id?: number;
}

export interface AvailableIngredientStarterItem {
  canonical_food_id: number;
  display_name: string;
  food_type: string;
}

export interface AvailableIngredientStarterGroup {
  key: string;
  title: string;
  items: AvailableIngredientStarterItem[];
}

export interface AvailableIngredientStarterGroupsResponse {
  success: boolean;
  groups: AvailableIngredientStarterGroup[];
}

export interface CanonicalFoodLogResponse {
  success: boolean;
  user_id: number;
  logged_food_entry_id: number;
  canonical_food_id: number;
  display_name: string;
  grams: number;
  resolved_grams?: number;
  serving_unit_id?: number;
  serving_quantity?: number;
  serving_display?: string;
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
export const FOOD_LIBRARY_CHANGED_EVENT = "food-library-changed";

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
  serving_unit_id?: number;
  serving_quantity?: number;
  serving_display?: string;
  resolved_grams?: number;
  amount_source?: string;
  serving_unit_confidence?: "Low" | "Moderate" | "High";
}

export interface CanonicalFoodLogsResponse {
  success: boolean;
  user_id: number;
  date: string;
  entries: CanonicalFoodLoggedEntry[];
}

export interface CanonicalFoodLogUpdateRequest {
  user_id: number;
  entry_id: number;
  grams?: number;
  serving_unit_id?: number;
  quantity?: number;
  meal_type?: string;
  entry_date: string;
}

export interface CanonicalFoodLogUpdateResponse {
  success: boolean;
  user_id: number;
  entry: CanonicalFoodLoggedEntry;
}

export interface CanonicalFoodLogDeleteRequest {
  user_id: number;
  entry_id: number;
  entry_date: string;
}

export interface CanonicalFoodLogDeleteResponse {
  success: boolean;
  user_id: number;
  deleted: boolean;
  entry_id: number;
}
