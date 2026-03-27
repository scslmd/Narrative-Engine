import { useState } from 'react';
import type { CheckerFinding, ReviewDecision, DecisionAction, ReviewDecisionCreateRequest } from '../../types/review';
import { createDecision } from '../../services/review';
import { toast } from '../../lib/toast';

interface DecisionFormProps {
  finding: CheckerFinding;
  onSuccess?: (decision: ReviewDecision) => void;
}

const decisionActions: DecisionAction[] = ['accept', 'reject', 'defer', 'escalate', 'refine'];

export function DecisionForm({ finding, onSuccess }: DecisionFormProps) {
  const [decisionAction, setDecisionAction] = useState<DecisionAction>('accept');
  const [notes, setNotes] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!notes.trim()) {
      setError('Please provide notes for your decision');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const request: ReviewDecisionCreateRequest = {
        decision_id: `decision-${Date.now()}`,
        project_id: finding.project_id,
        target_kind: 'checker_finding',
        target_id: finding.finding_id,
        decision: decisionAction,
        notes,
      };

      const decision = await createDecision(request);
      
      toast.success('Decision recorded successfully');
      onSuccess?.(decision);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to record decision');
      toast.error('Failed to record decision');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="border-t border-gray-200 p-4 bg-gray-50">
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

        <div>
          <label htmlFor="notes" className="block text-sm font-medium text-gray-700 mb-1">
            Notes *
          </label>
          <textarea
            id="notes"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
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
