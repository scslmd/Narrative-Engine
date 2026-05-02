interface CanonOverviewPanelProps {
  characterCount: number;
  worldCount: number;
  mythosCount: number;
  patternCount: number;
  annotationCount: number;
}

export function CanonOverviewPanel({
  characterCount,
  worldCount,
  mythosCount,
  patternCount,
  annotationCount,
}: CanonOverviewPanelProps) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
      <Stat label="Characters" value={characterCount} />
      <Stat label="World" value={worldCount} />
      <Stat label="Mythos" value={mythosCount} />
      <Stat label="Patterns" value={patternCount} />
      <Stat label="Annotations" value={annotationCount} />
    </div>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded border border-slate-200 bg-white px-3 py-2">
      <div className="text-xs text-slate-500">{label}</div>
      <div className="text-lg font-semibold text-slate-900">{value}</div>
    </div>
  );
}
