import { useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import { UploadPanel } from "../upload/UploadPanel";
import { ControlsPanel } from "../analysis/ControlsPanel";
import { ExportPanel } from "../export/ExportPanel";

function Section({ title, defaultOpen = true, children }: { title: string; defaultOpen?: boolean; children: React.ReactNode }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div>
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center gap-s2 py-s2 text-label font-semibold text-ink-muted hover:text-accent transition-colors"
      >
        {open ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        {title}
      </button>
      {open && <div className="space-y-s3 pb-s2">{children}</div>}
    </div>
  );
}

export function Sidebar() {
  return (
    <aside className="bg-surface-1 border-r border-edge w-80 min-w-80 overflow-y-auto p-s4 space-y-s1">
      <Section title="Data Upload">
        <UploadPanel />
      </Section>
      <div className="h-line" data-prefix="01 //" />
      <Section title="Analysis">
        <ControlsPanel />
      </Section>
      <div className="h-line" data-prefix="02 //" />
      <Section title="Export">
        <ExportPanel />
      </Section>
    </aside>
  );
}
