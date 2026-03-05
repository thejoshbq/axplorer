export type { ColorPalette, ThemeDefinition } from "./types";
export { axplorerTheme } from "./axplorer";

import { axplorerTheme } from "./axplorer";
import type { ThemeDefinition } from "./types";

export const themes: Record<string, ThemeDefinition> = {
  axplorer: axplorerTheme,
};

export const defaultThemeId = "axplorer";
