import { useDataStore } from "../../store/useDataStore";

export function StatusIndicator() {
  const { status, loading, fovCount } = useDataStore();
  const isLoaded = fovCount > 0;

  return (
    <div className={`text-label px-s2 py-s1 rounded border ${
      isLoaded
        ? "border-accent/30 text-accent bg-accent/5"
        : loading
          ? "border-warn/30 text-warn bg-warn/5 animate-status-pulse"
          : "border-edge text-ink-muted"
    }`}>
      {status}
    </div>
  );
}
