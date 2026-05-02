import type { GenerationMode } from '../../types/storyGeneration';

interface GenerationModeSelectorProps {
  value: GenerationMode;
  onChange: (value: GenerationMode) => void;
}

const MODES: Array<{ value: GenerationMode; label: string }> = [
  { value: 'same_project_new_arc', label: 'New Arc' },
  { value: 'same_project_sequel', label: 'Sequel' },
  { value: 'same_project_prequel', label: 'Prequel' },
  { value: 'same_project_side_story', label: 'Side Story' },
  { value: 'same_project_alternate_route', label: 'Alternate Route' },
  { value: 'new_project_character_fork', label: 'Character Fork' },
  { value: 'new_project_world_fork', label: 'World Fork' },
  { value: 'new_project_hybrid_fork', label: 'Hybrid Fork' },
];

export function GenerationModeSelector({ value, onChange }: GenerationModeSelectorProps) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
      {MODES.map((mode) => (
        <button
          key={mode.value}
          type="button"
          onClick={() => onChange(mode.value)}
          className={`px-3 py-2 rounded border text-sm ${
            value === mode.value ? 'bg-indigo-600 text-white border-indigo-600' : 'border-slate-300'
          }`}
        >
          {mode.label}
        </button>
      ))}
    </div>
  );
}
