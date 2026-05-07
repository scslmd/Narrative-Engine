import { useState, useEffect, useCallback } from 'react';
import type { ReviewDecision } from '../../types/review';
import { getDecisionsForFinding } from '../../services/review';
import { useUIStore } from '../../stores/uiStore';

interface DecisionHistoryProps {
  findingId: string;
}

export function DecisionHistory({ findingId }: DecisionHistoryProps) {
  const projectId = useUIStore((state) => state.projectId);
  const [decisions, setDecisions] = useState<ReviewDecision[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadDecisions = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      if (!projectId) {
        throw new Error('Project context is required to load decision history');
      }

      const data = await getDecisionsForFinding(projectId, findingId);
      setDecisions(data.sort((a, b) => 
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      ));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load decisions');
      setDecisions([]);
    } finally {
      setLoading(false);
    }
  }, [findingId, projectId]);

  useEffect(() => {
    loadDecisions();
  }, [loadDecisions]);

  const getActionColor = (action: string): string => {
    switch (action) {
      case 'accept':
        return 'bg-green-100 text-green-800';
      case 'reject':
        return 'bg-red-100 text-red-800';
      case 'defer':
        return 'bg-gray-100 text-gray-800';
      case 'escalate':
        return 'bg-purple-100 text-purple-800';
      case 'refine':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return <div className="text-sm text-gray-500">Loading decisions...</div>;
  }

  if (error) {
    return <div className="text-sm text-red-600">{error}</div>;
  }

  if (decisions.length === 0) {
    return <div className="text-sm text-gray-500">No decisions recorded yet</div>;
  }

  return (
    <div className="border-t border-gray-200 dark:border-slate-700 p-4 bg-white dark:bg-slate-800">
      <h3 className="font-medium text-gray-900 dark:text-slate-100 mb-3">Decision History ({decisions.length})</h3>
      
      <div className="space-y-3 max-h-64 overflow-y-auto">
        {decisions.map((decision) => (
          <div key={decision.decision_id} className="border rounded p-3 bg-gray-50 dark:bg-slate-700">
            <div className="flex items-center justify-between mb-2">
              <span className={`px-2 py-1 rounded text-xs font-medium ${getActionColor(decision.decision)}`}>
                {decision.decision.toUpperCase()}
              </span>
              <span className="text-xs text-gray-500 dark:text-slate-400">
                {new Date(decision.created_at).toLocaleString()}
              </span>
            </div>
            
            {decision.notes && (
              <p className="text-sm text-gray-700 dark:text-slate-300">{decision.notes}</p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
