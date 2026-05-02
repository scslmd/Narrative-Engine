interface CanonSelectionDrawerProps {
  onGenerate: () => void;
  onFork: () => void;
}

export function CanonSelectionDrawer({ onGenerate, onFork }: CanonSelectionDrawerProps) {
  return (
    <div className="rounded border border-slate-200 bg-white p-3 flex gap-2">
      <button type="button" className="rounded bg-indigo-700 text-white px-3 py-1.5 text-sm" onClick={onGenerate}>
        Generate with Selected
      </button>
      <button type="button" className="rounded bg-slate-700 text-white px-3 py-1.5 text-sm" onClick={onFork}>
        Fork Selected to New Story
      </button>
    </div>
  );
}
