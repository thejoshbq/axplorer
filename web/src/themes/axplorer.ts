import type { ThemeDefinition } from "./types";

export const axplorerTheme: ThemeDefinition = {
  id: "axplorer",
  name: "Axplorer",
  colors: {
    light: {
      surface: "250 253 253",
      panel: "238 248 248",
      textPrimary: "10 20 20",
      textSecondary: "70 100 100",
      accent: "0 180 182",
      accentHover: "0 145 148",
      accentContrast: "0 0 0",
      border: "70 100 100",
      input: "245 251 251",
    },
    dark: {
      surface: "10 10 10",
      panel: "14 18 20",
      textPrimary: "210 245 245",
      textSecondary: "120 175 175",
      accent: "0 212 216",
      accentHover: "0 175 180",
      accentContrast: "0 0 0",
      border: "0 212 216",
      input: "6 8 10",
    },
  },
  font: "mono",
  radius: { sm: "0.375rem", md: "0.375rem", lg: "0.625rem" },
  glass: { enabled: true, opacity: 0.85, blur: "6px" },
  branding: { text: "Axplorer" },
  background: "neon-grid",
};
