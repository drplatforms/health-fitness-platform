"use client";

import Link from "next/link";
import { ChangeEvent, useCallback, useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import type { IScannerControls } from "@zxing/browser";

import {
  BarcodeApiFormat,
  BarcodeCandidate,
  BarcodeCanonicalFood,
  BarcodeResolveResponse,
  barcodeFailureMessage,
  resolvedBarcodeFood,
  scannerFormatToApiFormat,
} from "@/lib/barcodeFood";
import {
  materializeFoodBarcode,
  resolveFoodBarcode,
} from "@/lib/canonicalFoodApi";

interface BarcodeScannerDialogProps {
  open: boolean;
  userId: number;
  targetDate: string;
  onClose: () => void;
  onFoodSelected: (food: BarcodeCanonicalFood) => void;
  onSearchFoods: () => void;
}

type ScannerView =
  | "scan"
  | "looking_up"
  | "candidate"
  | "not_found"
  | "incomplete"
  | "error";
type ScannerInput = "camera" | "photo" | "manual";

function compactNumber(value: number | null): string {
  if (value === null) {
    return "—";
  }
  return Number.isInteger(value) ? String(value) : value.toFixed(1);
}

function candidateMacroLine(candidate: BarcodeCandidate): string {
  const nutrition = candidate.nutrient_summary;
  return [
    `${compactNumber(nutrition.calories_per_100g)} kcal`,
    `${compactNumber(nutrition.protein_g_per_100g)}g protein`,
    `${compactNumber(nutrition.carbohydrate_g_per_100g)}g carbs`,
    `${compactNumber(nutrition.fat_g_per_100g)}g fat`,
  ].join(" · ");
}

export function BarcodeScannerDialog({
  open,
  userId,
  targetDate,
  onClose,
  onFoodSelected,
  onSearchFoods,
}: BarcodeScannerDialogProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const controlsRef = useRef<IScannerControls | null>(null);
  const lookupLockedRef = useRef(false);
  const [view, setView] = useState<ScannerView>("scan");
  const [activeInput, setActiveInput] = useState<ScannerInput>("camera");
  const [manualBarcode, setManualBarcode] = useState("");
  const [candidate, setCandidate] = useState<BarcodeCandidate | null>(null);
  const [normalizedGtin, setNormalizedGtin] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [cameraMessage, setCameraMessage] = useState<string | null>(null);

  const stopCamera = useCallback(() => {
    controlsRef.current?.stop();
    controlsRef.current = null;
    const stream = videoRef.current?.srcObject;
    if (stream instanceof MediaStream) {
      stream.getTracks().forEach((track) => track.stop());
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
  }, []);

  const selectResolvedFood = useCallback(
    (response: BarcodeResolveResponse) => {
      const food = resolvedBarcodeFood(response);
      if (!food) {
        return false;
      }
      stopCamera();
      onFoodSelected(food);
      onClose();
      return true;
    },
    [onClose, onFoodSelected, stopCamera],
  );

  const performLookup = useCallback(
    async (barcode: string, format?: BarcodeApiFormat | null) => {
      const trimmedBarcode = barcode.trim();
      if (!trimmedBarcode || lookupLockedRef.current) {
        return;
      }
      lookupLockedRef.current = true;
      stopCamera();
      setView("looking_up");
      setMessage(null);
      setCandidate(null);

      try {
        const response = await resolveFoodBarcode(trimmedBarcode, format);
        if (selectResolvedFood(response)) {
          return;
        }
        setNormalizedGtin(response.normalized_gtin ?? null);
        if (response.status === "candidate" && response.candidate) {
          setCandidate(response.candidate);
          setView("candidate");
          return;
        }
        setMessage(barcodeFailureMessage(response));
        setView(response.status === "incomplete" ? "incomplete" : "not_found");
      } catch (error) {
        setMessage(
          error instanceof Error ? error.message : "Unable to look up this barcode.",
        );
        setView("error");
      } finally {
        lookupLockedRef.current = false;
      }
    },
    [selectResolvedFood, stopCamera],
  );

  const startCamera = useCallback(async () => {
    stopCamera();
    setCameraMessage(null);
    if (!window.isSecureContext || !navigator.mediaDevices?.getUserMedia) {
      setCameraMessage("Live camera is unavailable here. Use a photo or enter the barcode.");
      return;
    }

    try {
      const { BarcodeFormat, BrowserMultiFormatReader } = await import(
        "@zxing/browser"
      );
      const reader = new BrowserMultiFormatReader();
      reader.possibleFormats = [
        BarcodeFormat.UPC_A,
        BarcodeFormat.UPC_E,
        BarcodeFormat.EAN_8,
        BarcodeFormat.EAN_13,
        BarcodeFormat.ITF,
      ];
      const controls = await reader.decodeFromConstraints(
        {
          audio: false,
          video: { facingMode: { ideal: "environment" } },
        },
        videoRef.current ?? undefined,
        (result) => {
          if (!result) {
            return;
          }
          const text = result.getText();
          const scannerFormat = BarcodeFormat[result.getBarcodeFormat()];
          const apiFormat = scannerFormatToApiFormat(scannerFormat, text);
          if (apiFormat) {
            void performLookup(text, apiFormat);
          }
        },
      );
      controlsRef.current = controls;
    } catch {
      stopCamera();
      setCameraMessage(
        "Camera access was unavailable or denied. Use a photo or enter the barcode.",
      );
    }
  }, [performLookup, stopCamera]);

  useEffect(() => stopCamera, [stopCamera]);

  useEffect(() => {
    if (!open) {
      return;
    }

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, [open]);

  async function handlePhoto(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) {
      return;
    }
    stopCamera();
    setMessage(null);
    try {
      const { BarcodeFormat, BrowserMultiFormatReader } = await import(
        "@zxing/browser"
      );
      const reader = new BrowserMultiFormatReader();
      reader.possibleFormats = [
        BarcodeFormat.UPC_A,
        BarcodeFormat.UPC_E,
        BarcodeFormat.EAN_8,
        BarcodeFormat.EAN_13,
        BarcodeFormat.ITF,
      ];
      const objectUrl = URL.createObjectURL(file);
      try {
        const result = await reader.decodeFromImageUrl(objectUrl);
        const text = result.getText();
        const apiFormat = scannerFormatToApiFormat(
          BarcodeFormat[result.getBarcodeFormat()],
          text,
        );
        if (!apiFormat) {
          throw new Error("The image did not contain a supported food barcode.");
        }
        await performLookup(text, apiFormat);
      } finally {
        URL.revokeObjectURL(objectUrl);
      }
    } catch (error) {
      setMessage(
        error instanceof Error
          ? error.message
          : "We couldn't read a supported barcode from that image.",
      );
      setView("error");
    }
  }

  async function handleUseProduct() {
    if (!candidate || !normalizedGtin) {
      return;
    }
    setView("looking_up");
    setMessage(null);
    try {
      const response = await materializeFoodBarcode(
        candidate.raw_food_source_record_id,
        normalizedGtin,
      );
      if (!selectResolvedFood(response)) {
        setMessage(barcodeFailureMessage(response));
        setView(response.status === "incomplete" ? "incomplete" : "error");
      }
    } catch (error) {
      setMessage(
        error instanceof Error ? error.message : "Unable to save this product.",
      );
      setView("error");
    }
  }

  function resetScanner(input: ScannerInput = "camera") {
    stopCamera();
    lookupLockedRef.current = false;
    setView("scan");
    setActiveInput(input);
    setCandidate(null);
    setNormalizedGtin(null);
    setMessage(null);
    setCameraMessage(null);
  }

  if (!open || typeof document === "undefined") {
    return null;
  }

  return createPortal(
    <div
      className="fixed inset-0 z-[100] flex h-dvh max-h-dvh items-end justify-center overflow-hidden bg-modal-backdrop sm:items-center sm:p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="barcode-scanner-title"
    >
      <div className="max-h-dvh w-full max-w-lg overscroll-contain overflow-y-auto rounded-t-[28px] border border-border bg-surface px-4 pt-4 pb-[max(1rem,env(safe-area-inset-bottom))] shadow-2xl sm:max-h-[calc(100dvh-2rem)] sm:rounded-[28px] sm:p-5">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h2 id="barcode-scanner-title" className="text-lg font-semibold text-text-strong">
              Scan packaged food
            </h2>
            <p className="mt-0.5 text-xs text-text-secondary">
              Camera, barcode photo, or manual entry
            </p>
          </div>
          <button
            type="button"
            onClick={() => {
              stopCamera();
              onClose();
            }}
            className="rounded-xl border border-border px-3 py-2 text-sm font-semibold text-text-primary"
            aria-label="Close barcode scanner"
          >
            Close
          </button>
        </div>

        {view === "scan" ? (
          <div className="mt-4 space-y-4">
            <div className="grid grid-cols-3 gap-1 rounded-2xl bg-surface-subtle p-1" role="tablist" aria-label="Barcode input method">
              {(["camera", "photo", "manual"] as const).map((input) => (
                <button
                  key={input}
                  type="button"
                  role="tab"
                  aria-selected={activeInput === input}
                  onClick={() => resetScanner(input)}
                  className={`rounded-xl px-2 py-2 text-sm font-semibold capitalize ${
                    activeInput === input
                      ? "bg-surface text-text-strong shadow-sm"
                      : "text-text-secondary"
                  }`}
                >
                  {input}
                </button>
              ))}
            </div>

            {activeInput === "camera" ? (
              <div className="space-y-3">
                <div className="relative aspect-[4/3] overflow-hidden rounded-2xl bg-black">
                  <video ref={videoRef} muted playsInline className="h-full w-full object-cover" />
                  <div className="pointer-events-none absolute inset-x-8 top-1/2 h-24 -translate-y-1/2 rounded-xl border-2 border-white/80" />
                </div>
                {cameraMessage ? (
                  <p className="rounded-2xl bg-caution-surface px-3 py-2 text-sm text-caution-foreground">
                    {cameraMessage}
                  </p>
                ) : (
                  <p className="text-center text-xs text-text-secondary">
                    Start the camera, then center the UPC, EAN, or GTIN barcode in the frame.
                  </p>
                )}
                <button
                  type="button"
                  onClick={() => void startCamera()}
                  className="w-full rounded-2xl border border-border-accent px-4 py-3 text-sm font-semibold text-accent-text"
                >
                  Start camera
                </button>
              </div>
            ) : null}

            {activeInput === "photo" ? (
              <label className="flex min-h-32 cursor-pointer flex-col items-center justify-center rounded-2xl border border-dashed border-border-accent bg-surface-subtle px-4 py-6 text-center">
                <span className="font-semibold text-text-strong">Choose barcode photo</span>
                <span className="mt-1 text-xs text-text-secondary">The image stays on this device.</span>
                <input
                  type="file"
                  accept="image/*"
                  capture="environment"
                  onChange={(event) => void handlePhoto(event)}
                  className="sr-only"
                />
              </label>
            ) : null}

            {activeInput === "manual" ? (
              <form
                className="space-y-3"
                onSubmit={(event) => {
                  event.preventDefault();
                  void performLookup(manualBarcode, null);
                }}
              >
                <label className="block space-y-1">
                  <span className="text-sm font-semibold text-text-primary">Barcode number</span>
                  <input
                    type="text"
                    inputMode="numeric"
                    autoComplete="off"
                    value={manualBarcode}
                    onChange={(event) => setManualBarcode(event.target.value.replace(/[^0-9\s-]/g, ""))}
                    placeholder="Enter UPC, EAN, or GTIN"
                    className="min-h-12 w-full rounded-2xl border border-border bg-surface px-4 py-3 text-base text-text-primary outline-none focus:border-focus"
                  />
                </label>
                <button
                  type="submit"
                  className="w-full rounded-2xl bg-action-primary px-4 py-3 text-sm font-semibold text-action-primary-foreground"
                >
                  Look up barcode
                </button>
              </form>
            ) : null}
          </div>
        ) : null}

        {view === "looking_up" ? (
          <p className="mt-5 rounded-2xl bg-surface-subtle px-4 py-6 text-center text-sm text-text-body">
            Looking up product...
          </p>
        ) : null}

        {view === "candidate" && candidate ? (
          <div className="mt-4 space-y-4 rounded-2xl bg-surface-subtle p-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-positive-foreground">Product found</p>
              {candidate.brand_name ? (
                <p className="mt-2 text-sm text-text-secondary">{candidate.brand_name}</p>
              ) : null}
              <p className="text-base font-semibold text-text-strong">{candidate.product_name}</p>
            </div>
            <div>
              <p className="text-sm text-text-primary">{candidateMacroLine(candidate)}</p>
              <p className="text-xs text-text-secondary">Per 100g</p>
            </div>
            {candidate.serving_grams ? (
              <p className="text-sm text-text-body">
                Serving: {candidate.serving_label || "1 serving"} ({compactNumber(candidate.serving_grams)}g)
              </p>
            ) : null}
            <p className="text-xs text-text-muted">Source: {candidate.source_name}</p>
            <div className="grid gap-2 sm:grid-cols-2">
              <button
                type="button"
                onClick={() => void handleUseProduct()}
                className="rounded-2xl bg-action-primary px-4 py-3 text-sm font-semibold text-action-primary-foreground"
              >
                Use this product
              </button>
              <button
                type="button"
                onClick={() => resetScanner("camera")}
                className="rounded-2xl border border-border px-4 py-3 text-sm font-semibold text-text-primary"
              >
                Scan again
              </button>
            </div>
          </div>
        ) : null}

        {view === "not_found" || view === "incomplete" || view === "error" ? (
          <div className="mt-4 space-y-4">
            <p className="rounded-2xl bg-caution-surface px-4 py-3 text-sm text-caution-foreground">
              {message || "Unable to resolve this barcode."}
            </p>
            <div className="grid gap-2 sm:grid-cols-2">
              <button
                type="button"
                onClick={() => resetScanner("manual")}
                className="rounded-2xl border border-border px-4 py-3 text-sm font-semibold text-text-primary"
              >
                Enter barcode manually
              </button>
              <button
                type="button"
                onClick={() => {
                  stopCamera();
                  onClose();
                  onSearchFoods();
                }}
                className="rounded-2xl border border-border px-4 py-3 text-sm font-semibold text-text-primary"
              >
                Search foods
              </button>
              <Link
                href={`/personal-foods/new?${new URLSearchParams({
                  user_id: String(userId),
                  date: targetDate,
                }).toString()}`}
                className="rounded-2xl border border-border px-4 py-3 text-center text-sm font-semibold !text-text-primary"
              >
                Create food
              </Link>
              <button
                type="button"
                onClick={() => resetScanner("camera")}
                className="rounded-2xl bg-action-primary px-4 py-3 text-sm font-semibold text-action-primary-foreground"
              >
                Scan another product
              </button>
            </div>
          </div>
        ) : null}
      </div>
    </div>,
    document.body,
  );
}
