import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      fontFamily: {
        mono: ['"JetBrains Mono"', "ui-monospace", "SFMono-Regular", "monospace"],
      },
      colors: {
        surface: {
          DEFAULT: "rgb(var(--color-surface) / <alpha-value>)",
        },
        panel: {
          DEFAULT: "rgb(var(--color-panel) / <alpha-value>)",
        },
        accent: {
          DEFAULT: "rgb(var(--color-accent) / <alpha-value>)",
          hover: "rgb(var(--color-accent-hover) / <alpha-value>)",
          contrast: "rgb(var(--color-accent-contrast) / <alpha-value>)",
        },
        theme: {
          border: "rgb(var(--color-border) / 0.12)",
          text: "rgb(var(--color-text-primary) / <alpha-value>)",
        },
        input: "rgb(var(--color-input) / <alpha-value>)",
      },
      boxShadow: {
        glow: "0 0 12px rgb(var(--color-accent) / 0.25)",
        "glow-sm": "0 0 6px rgb(var(--color-accent) / 0.15)",
      },
      keyframes: {
        "reacher-glow": {
          "0%, 100%": { filter: "drop-shadow(0 0 3px rgb(var(--color-accent) / 0.3))" },
          "50%": { filter: "drop-shadow(0 0 8px rgb(var(--color-accent) / 0.6))" },
        },
        "status-pulse": {
          "0%, 100%": { opacity: "1", transform: "scale(1)" },
          "50%": { opacity: "0.6", transform: "scale(0.92)" },
        },
      },
      animation: {
        "reacher-glow": "reacher-glow 3s ease-in-out infinite",
        "status-pulse": "status-pulse 2s ease-in-out infinite",
      },
    },
  },
  plugins: [],
} satisfies Config;
