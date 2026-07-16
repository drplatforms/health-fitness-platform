"use client";

import { useSyncExternalStore, type ChangeEvent } from "react";

import {
  isThemePreference,
  readThemePreference,
  saveThemePreference,
  subscribeThemePreference,
} from "@/lib/themePreference";

interface ThemePreferenceControlProps {
  className?: string;
}

export function ThemePreferenceControl({
  className = "",
}: ThemePreferenceControlProps) {
  const preference = useSyncExternalStore(
    subscribeThemePreference,
    readThemePreference,
    () => "system",
  );

  function handleChange(event: ChangeEvent<HTMLSelectElement>) {
    const nextPreference = event.target.value;
    if (!isThemePreference(nextPreference)) {
      return;
    }

    saveThemePreference(nextPreference);
  }

  return (
    <label
      className={`inline-flex items-center gap-2 rounded-full border border-border bg-surface/90 px-2.5 py-2 text-xs font-semibold text-text-secondary shadow-sm sm:px-3 ${className}`}
    >
      <span className="hidden sm:inline">Theme</span>
      <select
        aria-label="Theme preference"
        value={preference}
        onChange={handleChange}
        className="min-w-0 bg-transparent font-semibold text-text-primary outline-none focus-visible:rounded focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus"
      >
        <option value="system">System</option>
        <option value="light">Light</option>
        <option value="dark">Dark</option>
      </select>
    </label>
  );
}
