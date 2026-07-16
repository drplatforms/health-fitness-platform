export const THEME_PREFERENCE_STORAGE_KEY =
  "fitness_ai_theme_preference_v1";
const THEME_PREFERENCE_CHANGE_EVENT = "fitness-ai-theme-preference-change";

export const THEME_PREFERENCES = ["system", "light", "dark"] as const;

export type ThemePreference = (typeof THEME_PREFERENCES)[number];

let inMemoryThemePreference: ThemePreference = "system";

export function isThemePreference(value: unknown): value is ThemePreference {
  return (
    typeof value === "string" &&
    THEME_PREFERENCES.includes(value as ThemePreference)
  );
}

export function applyThemePreference(preference: ThemePreference): void {
  const root = document.documentElement;

  if (preference === "light" || preference === "dark") {
    root.dataset.theme = preference;
    return;
  }

  root.removeAttribute("data-theme");
}

export function readThemePreference(): ThemePreference {
  try {
    const storedPreference = window.localStorage.getItem(
      THEME_PREFERENCE_STORAGE_KEY,
    );
    if (isThemePreference(storedPreference)) {
      inMemoryThemePreference = storedPreference;
      return storedPreference;
    }
  } catch {
    // Fall through to the live in-memory preference.
  }

  return inMemoryThemePreference;
}

export function saveThemePreference(preference: ThemePreference): void {
  inMemoryThemePreference = preference;
  applyThemePreference(preference);

  try {
    window.localStorage.setItem(THEME_PREFERENCE_STORAGE_KEY, preference);
  } catch {
    // The live preference still applies when browser storage is unavailable.
  }

  window.dispatchEvent(new Event(THEME_PREFERENCE_CHANGE_EVENT));
}

export function subscribeThemePreference(
  onStoreChange: () => void,
): () => void {
  const syncPreference = () => {
    applyThemePreference(readThemePreference());
    onStoreChange();
  };

  window.addEventListener("storage", syncPreference);
  window.addEventListener(THEME_PREFERENCE_CHANGE_EVENT, syncPreference);

  return () => {
    window.removeEventListener("storage", syncPreference);
    window.removeEventListener(THEME_PREFERENCE_CHANGE_EVENT, syncPreference);
  };
}

export const THEME_PREFERENCE_BOOTSTRAP_SCRIPT = `(() => {
  const root = document.documentElement;
  try {
    const storedPreference = window.localStorage.getItem(${JSON.stringify(THEME_PREFERENCE_STORAGE_KEY)});
    if (storedPreference === "light" || storedPreference === "dark") {
      root.dataset.theme = storedPreference;
      return;
    }
  } catch {}
  root.removeAttribute("data-theme");
})();`;
