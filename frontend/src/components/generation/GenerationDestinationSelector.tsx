import type { GenerationDestination } from '../../types/storyGeneration';

interface GenerationDestinationSelectorProps {
  destination: GenerationDestination;
  onChange: (destination: GenerationDestination) => void;
}

export function GenerationDestinationSelector({ destination, onChange }: GenerationDestinationSelectorProps) {
  const isNewProject = destination.destination_kind === 'new_project';
  return (
    <div className="space-y-2">
      <div className="flex gap-2">
        <button
          type="button"
          onClick={() => onChange({ destination_kind: 'same_project', target_project_id: destination.target_project_id })}
          className={`px-3 py-2 rounded border text-sm ${
            !isNewProject ? 'bg-indigo-600 text-white border-indigo-600' : 'border-slate-300'
          }`}
        >
          Same Project
        </button>
        <button
          type="button"
          onClick={() => onChange({ destination_kind: 'new_project', target_project_name: destination.target_project_name || '' })}
          className={`px-3 py-2 rounded border text-sm ${
            isNewProject ? 'bg-indigo-600 text-white border-indigo-600' : 'border-slate-300'
          }`}
        >
          New Project
        </button>
      </div>
      {isNewProject && (
        <input
          value={destination.target_project_name || ''}
          onChange={(event) => onChange({ ...destination, target_project_name: event.target.value })}
          placeholder="Target project name"
          className="w-full rounded border border-slate-300 px-3 py-2 text-sm"
        />
      )}
    </div>
  );
}
