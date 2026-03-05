import { create } from "zustand";
import { themes, defaultThemeId } from "../themes";
import type { ThemeDefinition, ColorPalette } from "../themes";

type Mode = "dark" | "light";

interface ThemeStore {
  mode: Mode;
  theme: ThemeDefinition;
  toggleMode: () => void;
}

function getInitialMode(): Mode {
  if (typeof window === "undefined") return "dark";
  const stored = localStorage.getItem("axplorer-mode");
  if (stored === "light" || stored === "dark") return stored;
  return "dark";
}

function apply(theme: ThemeDefinition, mode: Mode) {
  const root = document.documentElement;
  const palette: ColorPalette = theme.colors[mode];

  root.classList.toggle("dark", mode === "dark");

  root.style.setProperty("--color-surface", palette.surface);
  root.style.setProperty("--color-panel", palette.panel);
  root.style.setProperty("--color-text-primary", palette.textPrimary);
  root.style.setProperty("--color-text-secondary", palette.textSecondary);
  root.style.setProperty("--color-accent", palette.accent);
  root.style.setProperty("--color-accent-hover", palette.accentHover);
  root.style.setProperty("--color-accent-contrast", palette.accentContrast);
  root.style.setProperty("--color-border", palette.border);
  root.style.setProperty("--color-input", palette.input);

  root.style.setProperty("--glass-opacity", String(theme.glass.opacity));
  root.style.setProperty("--glass-blur", theme.glass.blur);

  localStorage.setItem("axplorer-mode", mode);
}

export const useThemeStore = create<ThemeStore>((set) => {
  const initialMode = getInitialMode();
  const initialTheme = themes[defaultThemeId];

  apply(initialTheme, initialMode);

  return {
    mode: initialMode,
    theme: initialTheme,

    toggleMode: () =>
      set((s) => {
        const next: Mode = s.mode === "dark" ? "light" : "dark";
        apply(s.theme, next);
        return { mode: next };
      }),
  };
});
