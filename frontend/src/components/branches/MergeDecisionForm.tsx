import { useState } from 'react';
import type { BranchMergeDecision, StoryBranch } from '../../types/branches';

interface MergeDecisionFormProps {
  sourceBranch: StoryBranch;
  targetBranch: StoryBranch;
  onSubmit: (decision: Omit<BranchMergeDecision, 'merge_decision_id' | 'resulting_decision_node_ids'>) => void;
  onCancel: () => void;
}

export function MergeDecisionForm({ sourceBranch, targetBranch, onSubmit, onCancel }: MergeDecisionFormProps) {
  const [mergeRationale, setMergeRationale] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!mergeRationale.trim()) {
      return;
    }

    onSubmit({
      project_id: sourceBranch.project_id,
      source_branch_id: sourceBranch.branch_id,
      target_branch_id: targetBranch.branch_id,
      merge_rationale: mergeRationale.trim(),
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Source Branch</label>
        <input
          type="text"
          value={sourceBranch.branch_name}
          disabled
          className="w-full px-3 py-2 border rounded-md bg-gray-50 text-gray-600"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Target Branch</label>
        <input
          type="text"
          value={targetBranch.branch_name}
          disabled
          className="w-full px-3 py-2 border rounded-md bg-gray-50 text-gray-600"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Merge Rationale</label>
        <textarea
          value={mergeRationale}
          onChange={(e) => setMergeRationale(e.target.value)}
          rows={4}
          className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Explain why these branches should be merged..."
        />
      </div>

      <div className="flex gap-2">
        <button
          type="submit"
          disabled={!mergeRationale.trim()}
          className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Record Merge Decision
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
