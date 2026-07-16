export type BarcodeApiFormat =
  | "UPC_A"
  | "UPC_E"
  | "EAN_8"
  | "EAN_13"
  | "GTIN_14";

export interface BarcodeCandidate {
  raw_food_source_record_id: number;
  normalized_gtin: string;
  barcode: string;
  product_name: string;
  brand_name: string | null;
  source_name: string;
  source_record_id: string;
  nutrient_summary: {
    calories_per_100g: number | null;
    protein_g_per_100g: number | null;
    carbohydrate_g_per_100g: number | null;
    fat_g_per_100g: number | null;
  };
  serving_label: string | null;
  serving_grams: number | null;
}

export interface BarcodeCanonicalFood {
  canonical_food_id: number;
  display_name: string;
  food_type: string;
  default_unit: string | null;
  default_grams: number | null;
  search_priority: number;
  matched_on: string;
  aliases: string[];
  nutrient_summary?: {
    calories_per_100g?: number;
    protein_g_per_100g?: number;
    carbohydrate_g_per_100g?: number;
    fat_g_per_100g?: number;
  };
}

export interface BarcodeResolveResponse {
  status:
    | "resolved"
    | "candidate"
    | "not_found"
    | "incomplete"
    | "provider_unavailable"
    | "conflict"
    | "invalid_barcode";
  provider: string | null;
  reason: string | null;
  barcode_input?: string;
  barcode_format?: BarcodeApiFormat | null;
  normalized_gtin?: string;
  lookup_variants?: string[];
  canonical_food?: BarcodeCanonicalFood;
  candidate?: BarcodeCandidate;
}

export function scannerFormatToApiFormat(
  scannerFormat: string,
  decodedText: string,
): BarcodeApiFormat | null {
  const normalized = scannerFormat.trim().toUpperCase().replaceAll("-", "_");
  if (normalized === "UPC_A" || normalized === "UPC_E") {
    return normalized;
  }
  if (normalized === "EAN_8" || normalized === "EAN_13") {
    return normalized;
  }
  if (normalized === "ITF" && /^\d{14}$/.test(decodedText.trim())) {
    return "GTIN_14";
  }
  return null;
}

export function barcodeFailureMessage(response: BarcodeResolveResponse): string {
  switch (response.status) {
    case "not_found":
      return "We couldn't find this barcode.";
    case "incomplete":
      return "We found this product, but its nutrition information is incomplete.";
    case "provider_unavailable":
      return "Barcode lookup providers are unavailable right now.";
    case "conflict":
      return "This barcode is linked to conflicting saved products.";
    case "invalid_barcode":
      return response.reason || "Enter a valid product barcode.";
    default:
      return response.reason || "Unable to resolve this barcode.";
  }
}

export function resolvedBarcodeFood(
  response: BarcodeResolveResponse,
): BarcodeCanonicalFood | null {
  return response.status === "resolved" && response.canonical_food
    ? response.canonical_food
    : null;
}
