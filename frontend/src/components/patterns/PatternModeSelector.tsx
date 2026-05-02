interface PatternModeSelectorProps {
  modes: string[];
}

export function PatternModeSelector({ modes }: PatternModeSelectorProps) {
  return (
    <div className="flex flex-wrap gap-1">
      {modes.map((mode) => (
        <span key={mode} className="rounded border border-sky-200 bg-sky-50 text-sky-700 px-2 py-0.5 text-xs">
          {mode}
        </span>
      ))}
    </div>
  );
}
