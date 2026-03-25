import { useState } from 'react';
import type { CheckerFinding, ReviewDecision, DecisionAction } from '../../types/review';
import { createMockDecision } from '../../services/mocks/reviewMock';

interface DecisionFormProps {
  finding: CheckerFinding;
  onSuccess?: (decision: ReviewDecision) => void;
}

const decisionActions: DecisionAction[] = ['accept', 'reject', 'defer', 'escalate', 'refine'];

const getRoutedStageForAction = (action: DecisionAction): string | undefined => {
  switch (action) {
    case 'accept':
      return 'drafting';
    case 'reject':
      return 'archive';
    case 'refine':
      return 'drafting';
    default:
      return undefined;
  }
};

export function DecisionForm({ finding, onSuccess }: DecisionFormProps) {
  const [decisionAction, setDecisionAction] = useState<DecisionAction>('accept');
  const [rationale, setRationale] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const routedStage = getRoutedStageForAction(decisionAction);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!rationale.trim()) {
      setError('Please provide a rationale for your decision');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const decision = await createMockDecision({
        project_id: finding.project_id,
        finding_id: finding.finding_id,
        target_kind: finding.source_object_kind,
        target_id: finding.source_object_id,
        decision_action: decisionAction,
        rationale,
        routed_to_stage: routedStage,
      });

      onSuccess?.(decision);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to record decision');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="border-t border-gray-200 p-4 bg-gray-50">
      <div className="mb-3">
        <span className="text-xs font-semibold text-yellow-600 bg-yellow-100 px-2 py-1 rounded">
          Mock Mode - Backend endpoint not yet available
        </span>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Finding Summary
          </label>
          <p className="text-sm text-gray-600">{finding.summary}</p>
        </div>

        <div>
          <label htmlFor="decision-action" className="block text-sm font-medium text-gray-700 mb-1">
            Decision Action
          </label>
          <select
            id="decision-action"
            value={decisionAction}
            onChange={(e) => setDecisionAction(e.target.value as DecisionAction)}
            className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {decisionActions.map((action) => (
              <option key={action} value={action}>
                {action.charAt(0).toUpperCase() + action.slice(1)}
              </option>
            ))}
          </select>
        </div>

        {routedStage && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Routed To Stage
            </label>
            <p className="text-sm text-blue-600">{routedStage.charAt(0).toUpperCase() + routedStage.slice(1)}</p>
          </div>
        )}

        <div>
          <label htmlFor="rationale" className="block text-sm font-medium text-gray-700 mb-1">
            Rationale *
          </label>
          <textarea
            id="rationale"
            value={rationale}
            onChange={(e) => setRationale(e.target.value)}
            rows={4}
            className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            placeholder="Explain your decision..."
          />
        </div>

        {error && (
          <p className="text-sm text-red-600">{error}</p>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'Recording...' : 'Record Decision'}
        </button>
      </form>
    </div>
  );
}
