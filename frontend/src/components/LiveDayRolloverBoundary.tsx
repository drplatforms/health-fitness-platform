"use client";

import { useEffect } from "react";

import { startLiveDayRolloverWatcher } from "@/lib/dateFormatting";

interface LiveDayRolloverBoundaryProps {
  requestedDate?: string;
}

export function LiveDayRolloverBoundary({
  requestedDate,
}: LiveDayRolloverBoundaryProps) {
  useEffect(() => {
    return startLiveDayRolloverWatcher({
      requestedDate,
      now: () => new Date(),
      schedule: (callback, delayMilliseconds) =>
        window.setTimeout(callback, delayMilliseconds),
      cancel: (timeoutId) => window.clearTimeout(timeoutId),
      reload: () => window.location.reload(),
      isVisible: () => document.visibilityState === "visible",
      onVisibilityChange: (callback) => {
        document.addEventListener("visibilitychange", callback);
        return () => document.removeEventListener("visibilitychange", callback);
      },
      onFocus: (callback) => {
        window.addEventListener("focus", callback);
        return () => window.removeEventListener("focus", callback);
      },
    });
  }, [requestedDate]);

  return null;
}
