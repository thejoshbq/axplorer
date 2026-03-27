import { useDataStore } from "../../store/useDataStore";

export function StatusIndicator() {
  const { status, loading, fovCount, populationNames } = useDataStore();
  const isLoaded = fovCount > 0;

  return (
    <div className={`text-xs px-2 py-1.5 rounded border ${
      isLoaded
        ? "border-accent/30 text-accent bg-accent/5"
        : loading
          ? "border-yellow-500/30 text-yellow-400 bg-yellow-500/5 animate-status-pulse"
          : "border-theme-border text-[rgb(var(--color-text-secondary))]"
    }`}>
      {status}
      {isLoaded && populationNames.length > 0 && (
        <div className="mt-1 text-[rgb(var(--color-text-secondary))]">
          Populations: {populationNames.join(", ")}
        </div>
      )}
    </div>
  );
}
