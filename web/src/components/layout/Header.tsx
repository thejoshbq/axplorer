import { ThemeToggle } from "./ThemeToggle";

function BrainSearchIcon() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 64 64"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="h-8 w-8 text-accent animate-reacher-glow"
    >
      <path d="M32 12 C24 12 18 16 16 22 C14 28 14 34 18 40 C20 44 24 48 32 50" />
      <path d="M32 12 C40 12 46 16 48 22 C50 28 50 34 46 40 C44 44 40 48 32 50" />
      <path d="M32 14 L32 48" strokeDasharray="2 3" opacity="0.4" />
      <path d="M22 20 C26 22 28 26 26 30" opacity="0.5" />
      <path d="M42 20 C38 22 36 26 38 30" opacity="0.5" />
      <circle cx="42" cy="38" r="10" strokeWidth="2.5" opacity="0.9" />
      <line x1="49" y1="45" x2="56" y2="52" strokeWidth="3" opacity="0.9" />
    </svg>
  );
}

export function Header() {
  return (
    <header className="glass-panel border-b border-theme-border px-6 py-3 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <BrainSearchIcon />
        <h1 className="text-xl font-bold text-accent title-glow tracking-wide">
          Axplorer
        </h1>
      </div>
      <ThemeToggle />
    </header>
  );
}
