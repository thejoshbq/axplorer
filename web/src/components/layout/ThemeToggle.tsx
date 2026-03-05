import { Sun, Moon } from "lucide-react";
import { useThemeStore } from "../../store/useThemeStore";

export function ThemeToggle() {
  const { mode, toggleMode } = useThemeStore();

  return (
    <button
      onClick={toggleMode}
      className="btn-sm border border-theme-border bg-panel text-theme-text"
      title={`Switch to ${mode === "dark" ? "light" : "dark"} mode`}
    >
      {mode === "dark" ? <Sun size={16} /> : <Moon size={16} />}
    </button>
  );
}
