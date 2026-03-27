import type { JobPhase } from '../../types/job';

interface PhaseSelectorProps {
  selectedPhase: JobPhase | null;
  onSelectPhase: (phase: JobPhase) => void;
}

const PHASES: Array<{ value: JobPhase; label: string; description: string }> = [
  { value: 'P-100', label: 'Architect', description: 'Generate story foundation and bible' },
  { value: 'P-200', label: 'Sequencer', description: 'Create chapter and scene structure' },
  { value: 'P-300', label: 'Drafter', description: 'Write manuscript content' },
  { value: 'P-400', label: 'Compiler', description: 'Assemble final document' },
];

export default function PhaseSelector({ selectedPhase, onSelectPhase }: PhaseSelectorProps) {
  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-gray-700">Job Phase *</label>
      
      <div className="grid grid-cols-1 gap-2">
        {PHASES.map((phase) => (
          <button
            key={phase.value}
            type="button"
            onClick={() => onSelectPhase(phase.value)}
            className={`p-3 border rounded-lg text-left transition-all ${
              selectedPhase === phase.value
                ? 'border-blue-500 bg-blue-50 ring-2 ring-blue-200'
                : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
            }`}
          >
            <div className="flex items-center justify-between">
              <span className={`font-semibold ${selectedPhase === phase.value ? 'text-blue-700' : 'text-gray-900'}`}>
                {phase.label}
              </span>
              <span className="text-xs text-gray-500">{phase.value}</span>
            </div>
            <p className="text-sm text-gray-600 mt-1">{phase.description}</p>
          </button>
        ))}
      </div>
    </div>
  );
}
