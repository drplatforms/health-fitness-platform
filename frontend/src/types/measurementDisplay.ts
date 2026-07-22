export interface QuantityPresentation {
  canonical_grams: number;
  primary_quantity: string;
  primary_unit: string;
  primary_text: string;
  secondary_grams: number | null;
  secondary_text: string | null;
  display_text: string;
  conversion_source:
    | "food_specific_measure"
    | "exact_mass_conversion"
    | "grams_fallback"
    | string;
  reliability: "Exact" | "High" | "Moderate" | "Canonical" | string;
  source: string | null;
  source_note: string | null;
  serving_unit_id: number | null;
}
