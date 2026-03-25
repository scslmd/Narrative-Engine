import { useState } from 'react';
import type { StoryBranch, BranchMergeDecision } from '../../types/branches';

interface MergeDecisionFormProps {
  sourceBranch: StoryBranch;
  targetBranch: StoryBranch;
  onSubmit: (decision: Omit<BranchMergeDecision, 'merge_decision_id' | 'created_at'>) => void;
  onCancel: () => void;
}

export function MergeDecisionForm({ sourceBranch, targetBranch, onSubmit, onCancel }: MergeDecisionFormProps) {
  const [decision, setDecision] = useState<'merge' | 'reject' | 'defer'>('merge');
  const [rationale, setRationale] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      project_id: sourceBranch.project_id,
      source_branch_id: sourceBranch.branch_id,
      target_branch_id: targetBranch.branch_id,
      decision,
      rationale: rationale || undefined,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Source Branch</label>
        <input
          type="text"
          value={sourceBranch.name}
          disabled
          className="w-full px-3 py-2 border rounded-md bg-gray-50 text-gray-600"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Target Branch</label>
        <input
          type="text"
          value={targetBranch.name}
          disabled
          className="w-full px-3 py-2 border rounded-md bg-gray-50 text-gray-600"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Decision</label>
        <select
          value={decision}
          onChange={(e) => setDecision(e.target.value as 'merge' | 'reject' | 'defer')}
          className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="merge">Merge</option>
          <option value="reject">Reject</option>
          <option value="defer">Defer</option>
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Rationale (optional)</label>
        <textarea
          value={rationale}
          onChange={(e) => setRationale(e.target.value)}
          rows={4}
          className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Explain your decision..."
        />
      </div>

      <div className="flex gap-2">
        <button
          type="submit"
          className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          Record Decision
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
        >
          Cancel
        </button>
      </div>
    </form>
  );
}
