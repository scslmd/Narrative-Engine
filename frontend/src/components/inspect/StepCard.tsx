import { type StepRecord, type StepState } from '../../types/inspect';
import ProvenanceBadge from '../common/ProvenanceBadge';

interface StepCardProps {
  step: StepRecord;
}

const STATE_STYLES: Record<StepState, string> = {
  PENDING: 'bg-gray-100 text-gray-700',
  RUNNING: 'bg-blue-100 text-blue-700 animate-pulse',
  COMPLETED: 'bg-green-100 text-green-700',
  FAILED: 'bg-red-100 text-red-700',
};

export default function StepCard({ step }: StepCardProps) {
  const {
    step_name,
    state,
    duration_seconds,
    model_id,
    backend_name,
    error_code,
    started_at,
  } = step;

  const formattedTime = started_at ? new Date(started_at).toLocaleTimeString() : null;

  return (
    <div className="bg-white rounded-lg p-4 border shadow-sm">
      <div className="flex items-start justify-between gap-3 mb-3">
        <h4 className="font-medium text-gray-900 flex-1">{step_name}</h4>
        
        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATE_STYLES[state]}`}>
          {state}
        </span>
      </div>

      <div className="flex items-center gap-4 text-sm text-gray-600">
        {duration_seconds !== undefined && (
          <span>{duration_seconds.toFixed(2)}s</span>
        )}
        
        {formattedTime && (
          <>
            <span>•</span>
            <span>{formattedTime}</span>
          </>
        )}

        {(model_id || backend_name) && (
          <>
            <span>•</span>
            <ProvenanceBadge 
              compact
              provenance={{ model: model_id, backendName: backend_name }}
            />
          </>
        )}
      </div>

      {error_code && (
        <div className="mt-3 p-2 bg-red-50 rounded text-sm text-red-700">
          Error: {error_code}
        </div>
      )}
    </div>
  );
}
