"use client";

import React, {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
} from "react";

// ─── Theme Definitions ────────────────────────────────────────────────────────

export interface ThemeDefinition {
  id: string;
  label: string;
  emoji: string;
  group: "dark" | "light" | "accessibility";
  isDark: boolean;
}

export const THEMES: ThemeDefinition[] = [
  // Dark Themes
  { id: "forest",   label: "Forest Green",    emoji: "🌿", group: "dark",          isDark: true },
  { id: "midnight", label: "Midnight Dark",    emoji: "🌙", group: "dark",          isDark: true },
  { id: "carbon",   label: "Carbon Black",     emoji: "⚫", group: "dark",          isDark: true },
  { id: "ocean",    label: "Ocean Blue",       emoji: "🔵", group: "dark",          isDark: true },
  { id: "aurora",   label: "Aurora Purple",    emoji: "🟣", group: "dark",          isDark: true },
  { id: "sunset",   label: "Sunset Orange",    emoji: "🟠", group: "dark",          isDark: true },
  { id: "crimson",  label: "Crimson Red",      emoji: "🔴", group: "dark",          isDark: true },
  { id: "emerald",  label: "Emerald Green",    emoji: "🟢", group: "dark",          isDark: true },
  { id: "golden",   label: "Golden Sand",      emoji: "🟡", group: "dark",          isDark: true },
  { id: "arctic",   label: "Arctic Blue",      emoji: "🔷", group: "dark",          isDark: true },
  // Light Themes
  { id: "light",      label: "Light",          emoji: "☀️",  group: "light",         isDark: false },
  { id: "pearl",      label: "Pearl White",    emoji: "🤍", group: "light",         isDark: false },
  { id: "frost",      label: "Frost",          emoji: "🧊", group: "light",         isDark: false },
  { id: "mint-light", label: "Mint",           emoji: "🍃", group: "light",         isDark: false },
  { id: "warm-light", label: "Warm Light",     emoji: "🌤️", group: "light",         isDark: false },
  // Accessibility Themes
  { id: "hc-dark",  label: "High Contrast Dark",  emoji: "◼", group: "accessibility", isDark: true  },
  { id: "hc-light", label: "High Contrast Light", emoji: "◻", group: "accessibility", isDark: false },
  { id: "amoled",   label: "AMOLED Black",        emoji: "⬛", group: "accessibility", isDark: true  },
];

export const THEME_GROUPS = {
  dark: THEMES.filter(t => t.group === "dark"),
  light: THEMES.filter(t => t.group === "light"),
  accessibility: THEMES.filter(t => t.group === "accessibility"),
};

const STORAGE_KEY = "ct-theme";
const DEFAULT_THEME = "forest";

// ─── Context ──────────────────────────────────────────────────────────────────

interface ThemeContextValue {
  theme: string;
  themeData: ThemeDefinition;
  themes: ThemeDefinition[];
  setTheme: (id: string) => void;
  isDark: boolean;
  toggleDark: () => void;
}

const ThemeContext = createContext<ThemeContextValue | null>(null);

// ─── Provider ─────────────────────────────────────────────────────────────────

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setThemeState] = useState<string>(DEFAULT_THEME);

  // Initialize from localStorage + system preference
  useEffect(() => {
    if (typeof window === "undefined") return;
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored && THEMES.find(t => t.id === stored)) {
      applyTheme(stored);
      setThemeState(stored);
    } else {
      // Detect system dark preference
      const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
      const auto = prefersDark ? DEFAULT_THEME : "light";
      applyTheme(auto);
      setThemeState(auto);
    }
  }, []);

  const applyTheme = useCallback((id: string) => {
    const def = THEMES.find(t => t.id === id);
    if (!def) return;
    const html = document.documentElement;
    // Set data-theme for CSS custom properties
    html.setAttribute("data-theme", id);
    // Set dark/light class for Tailwind darkMode: "class"
    if (def.isDark) {
      html.classList.add("dark");
      html.classList.remove("light");
    } else {
      html.classList.remove("dark");
      html.classList.add("light");
    }
  }, []);

  const setTheme = useCallback((id: string) => {
    if (!THEMES.find(t => t.id === id)) return;
    applyTheme(id);
    setThemeState(id);
    localStorage.setItem(STORAGE_KEY, id);
  }, [applyTheme]);

  const toggleDark = useCallback(() => {
    const current = THEMES.find(t => t.id === theme);
    if (!current) return;
    if (current.isDark) {
      setTheme("light");
    } else {
      setTheme(DEFAULT_THEME);
    }
  }, [theme, setTheme]);

  const themeData = THEMES.find(t => t.id === theme) ?? THEMES[0];
  const isDark = themeData.isDark;

  return (
    <ThemeContext.Provider
      value={{ theme, themeData, themes: THEMES, setTheme, isDark, toggleDark }}
    >
      {children}
    </ThemeContext.Provider>
  );
}

// ─── Hook ─────────────────────────────────────────────────────────────────────

export function useTheme(): ThemeContextValue {
  const ctx = useContext(ThemeContext);
  if (!ctx) {
    // Graceful fallback outside provider
    return {
      theme: DEFAULT_THEME,
      themeData: THEMES[0],
      themes: THEMES,
      setTheme: () => {},
      isDark: true,
      toggleDark: () => {},
    };
  }
  return ctx;
}
