import { useState } from 'react';
import type { BranchComparisonRecord, BranchMergeDecision, StoryBranch } from '../../types/branches';
import { createBranchComparison, createMergeDecision, getBranch, getBranchComparison, getBranchStateRefs, getMergeDecision } from '../../services/branches';
import { useToastStore } from '../../stores/toastStore';
import { MergeDecisionForm } from './MergeDecisionForm';

interface BranchComparisonProps {
  projectId: string;
  branches: StoryBranch[];
  onClose: () => void;
}

export function BranchComparison({ projectId, branches, onClose }: BranchComparisonProps) {
  const [selectedA, setSelectedA] = useState<string>('');
  const [selectedB, setSelectedB] = useState<string>('');
  const [comparison, setComparison] = useState<BranchComparisonRecord | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showMergeForm, setShowMergeForm] = useState(false);
  const [stateRefCount, setStateRefCount] = useState<number>(0);
  const addToast = useToastStore((state) => state.addToast);

  const handleCompare = async () => {
    if (!selectedA || !selectedB) return;

    setLoading(true);
    setError(null);

    try {
      const result = await createBranchComparison(projectId, selectedA, selectedB);
      const hydrated = await getBranchComparison(result.comparison_id, projectId);
      await Promise.all([getBranch(selectedA, projectId), getBranch(selectedB, projectId)]);
      const refs = await getBranchStateRefs(selectedA, projectId);
      setStateRefCount(refs.length);
      setComparison(hydrated);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to compare branches');
    } finally {
      setLoading(false);
    }
  };

  const handleMergeDecisionSubmit = async (
    decisionData: Omit<BranchMergeDecision, 'merge_decision_id' | 'resulting_decision_node_ids'>,
  ) => {
    try {
      const decision = await createMergeDecision(
        projectId,
        decisionData.source_branch_id,
        decisionData.target_branch_id,
        decisionData.merge_rationale,
      );
      await getMergeDecision(decision.merge_decision_id, projectId);
      addToast('Merge decision recorded', 'success');
      setShowMergeForm(false);
    } catch (err) {
      addToast(err instanceof Error ? err.message : 'Failed to record merge decision', 'error');
    }
  };

  const branchA = branches.find((branch) => branch.branch_id === selectedA);
  const branchB = branches.find((branch) => branch.branch_id === selectedB);

  return (
    <div className="border rounded-lg p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-gray-900">Compare Branches</h3>
        <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
          x
        </button>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-100 text-red-800 rounded-md text-sm">
          {error}
        </div>
      )}

      {!comparison ? (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Select First Branch</label>
            <select
              value={selectedA}
              onChange={(e) => setSelectedA(e.target.value)}
              className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">-- Select branch --</option>
              {branches.map((branch) => (
                <option key={branch.branch_id} value={branch.branch_id}>
                  {branch.branch_name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Select Second Branch</label>
            <select
              value={selectedB}
              onChange={(e) => setSelectedB(e.target.value)}
              className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">-- Select branch --</option>
              {branches.filter((branch) => branch.branch_id !== selectedA).map((branch) => (
                <option key={branch.branch_id} value={branch.branch_id}>
                  {branch.branch_name}
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={handleCompare}
            disabled={!selectedA || !selectedB || loading}
            className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-gray-300"
          >
            {loading ? 'Comparing...' : 'Compare Branches'}
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {showMergeForm ? (
            <div>
              <h4 className="font-semibold text-gray-900 mb-4">Record Merge Decision</h4>
              {branchA && branchB ? (
                <MergeDecisionForm
                  sourceBranch={branchA}
                  targetBranch={branchB}
                  onSubmit={handleMergeDecisionSubmit}
                  onCancel={() => setShowMergeForm(false)}
                />
              ) : null}
            </div>
          ) : (
            <>
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <span>{branchA?.branch_name}</span>
                <span>vs</span>
                <span>{branchB?.branch_name}</span>
                <span className="ml-auto text-xs text-gray-500">State refs: {stateRefCount}</span>
              </div>

              <div className="border rounded-lg divide-y">
                {comparison.review_notes.length > 0 ? (
                  comparison.review_notes.map((note, index) => (
                    <div key={index} className="p-3">
                      <p className="text-sm text-gray-700">{note}</p>
                    </div>
                  ))
                ) : (
                  <div className="p-3 text-sm text-gray-500">
                    No review notes were returned for this comparison.
                  </div>
                )}
              </div>

              <div className="flex gap-2">
                <button
                  onClick={() => setShowMergeForm(true)}
                  className="flex-1 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
                >
                  Record Merge Decision
                </button>
                <button onClick={onClose} className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700">
                  Close
                </button>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
