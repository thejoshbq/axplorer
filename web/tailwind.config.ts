import type { Config } from "tailwindcss";

export default {
  presets: [require("@phoxel/tokens/tailwind")],
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      // Axplorer-specific decorative extras -- not part of the token contract.
      boxShadow: {
        glow: "0 0 12px var(--accent-soft)",
        "glow-sm": "0 0 6px var(--accent-soft)",
      },
      keyframes: {
        blink: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0" },
        },
        "bolt-flicker": {
          "0%, 90%, 100%": { opacity: "0.8" },
          "93%": { opacity: "0.3" },
          "96%": { opacity: "0.9" },
          "98%": { opacity: "0.4" },
        },
        "ember-sway": {
          "0%, 100%": { transform: "rotate(0deg) scale(1)" },
          "25%": { transform: "rotate(-2deg) scale(1.03)" },
          "75%": { transform: "rotate(2deg) scale(0.97)" },
        },
        "reacher-glow": {
          "0%, 100%": { filter: "drop-shadow(0 0 3px var(--accent-soft))" },
          "50%": { filter: "drop-shadow(0 0 8px var(--accent))" },
        },
        "mouse-run": {
          "0%, 100%": { transform: "rotate(0deg)" },
          "25%": { transform: "rotate(25deg)" },
          "75%": { transform: "rotate(-25deg)" },
        },
        "status-pulse": {
          "0%, 100%": { opacity: "1", transform: "scale(1)" },
          "50%": { opacity: "0.6", transform: "scale(0.92)" },
        },
        "grid-drift": {
          to: { backgroundPosition: "60px 60px" },
        },
        glitch: {
          "0%": { clipPath: "inset(40% 0 61% 0)", transform: "skewX(0deg)" },
          "20%": { clipPath: "inset(92% 0 1% 0)", transform: "skewX(-2deg)" },
          "40%": { clipPath: "inset(43% 0 1% 0)", transform: "skewX(1deg)" },
          "60%": { clipPath: "inset(25% 0 58% 0)", transform: "skewX(-1deg)" },
          "80%": { clipPath: "inset(54% 0 7% 0)", transform: "skewX(2deg)" },
          "100%": { clipPath: "inset(58% 0 43% 0)", transform: "skewX(0deg)" },
        },
      },
      animation: {
        blink: "blink 1s step-end infinite",
        "pulse-glow": "pulse-glow 2s ease-in-out infinite",
        "btn-flash": "btn-flash 0.4s ease-out",
        "bolt-flicker": "bolt-flicker 3s ease-in-out infinite",
        "ember-sway": "ember-sway 2s ease-in-out infinite",
        "reacher-glow": "reacher-glow 3s ease-in-out infinite",
        "mouse-run": "mouse-run 0.3s ease-in-out infinite",
        "status-pulse": "status-pulse 2s ease-in-out infinite",
        "grid-drift": "grid-drift 60s linear infinite",
        glitch: "glitch 0.3s linear",
      },
    },
  },
  plugins: [],
} satisfies Config;
