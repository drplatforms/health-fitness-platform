import assert from "node:assert/strict";
import test from "node:test";

import {
  barcodeFailureMessage,
  resolvedBarcodeFood,
  scannerFormatToApiFormat,
} from "./barcodeFood.ts";

test("maps only supported packaged-food scanner formats", () => {
  assert.equal(scannerFormatToApiFormat("UPC_A", "036000291452"), "UPC_A");
  assert.equal(scannerFormatToApiFormat("UPC_E", "04252614"), "UPC_E");
  assert.equal(scannerFormatToApiFormat("EAN_8", "96385074"), "EAN_8");
  assert.equal(scannerFormatToApiFormat("EAN_13", "4006381333931"), "EAN_13");
  assert.equal(scannerFormatToApiFormat("ITF", "10012345000017"), "GTIN_14");
  assert.equal(scannerFormatToApiFormat("ITF", "123456"), null);
  assert.equal(scannerFormatToApiFormat("QR_CODE", "036000291452"), null);
});

test("maps bounded barcode failure states to user-facing copy", () => {
  assert.equal(
    barcodeFailureMessage({ status: "not_found", provider: null, reason: null }),
    "We couldn't find this barcode.",
  );
  assert.equal(
    barcodeFailureMessage({ status: "incomplete", provider: null, reason: null }),
    "We found this product, but its nutrition information is incomplete.",
  );
});

test("returns a canonical food only from a resolved response", () => {
  const canonicalFood = {
    canonical_food_id: 7,
    display_name: "Saved Product",
    food_type: "branded",
    default_unit: "grams",
    default_grams: 100,
    search_priority: 100,
    matched_on: "barcode",
    aliases: [],
  };
  assert.deepEqual(
    resolvedBarcodeFood({
      status: "resolved",
      provider: "local",
      reason: null,
      canonical_food: canonicalFood,
    }),
    canonicalFood,
  );
  assert.equal(
    resolvedBarcodeFood({ status: "candidate", provider: "local_raw", reason: null }),
    null,
  );
});
