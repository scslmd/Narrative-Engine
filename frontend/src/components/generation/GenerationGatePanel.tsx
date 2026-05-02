import type { GenerationGateResult } from '../../types/storyGeneration';

interface GenerationGatePanelProps {
  gates: GenerationGateResult[];
}

export function GenerationGatePanel({ gates }: GenerationGatePanelProps) {
  if (!gates.length) {
    return null;
  }
  return (
    <div className="rounded border border-slate-300 p-3">
      <p className="text-sm font-semibold mb-2">Gate Results</p>
      <div className="space-y-2">
        {gates.map((gate) => (
          <div key={gate.gate_result_id} className="text-xs border border-slate-200 rounded p-2">
            <p className="font-medium">{gate.gate_name}</p>
            <p>Status: {gate.passed ? 'passed' : 'failed'}</p>
            {gate.reasons.length > 0 && <p>Reasons: {gate.reasons.join('; ')}</p>}
          </div>
        ))}
      </div>
    </div>
  );
}
