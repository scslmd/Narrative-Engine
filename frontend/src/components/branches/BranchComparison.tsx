import { useState } from 'react';
import type { BranchComparisonRecord, StoryBranch } from '../../types/branches';

interface BranchComparisonProps {
  branches: StoryBranch[];
  onClose: () => void;
}

export function BranchComparison({ branches, onClose }: BranchComparisonProps) {
  const [selectedA, setSelectedA] = useState<string>('');
  const [selectedB, setSelectedB] = useState<string>('');
  const [comparison, setComparison] = useState<BranchComparisonRecord | null>(null);

  const handleCompare = () => {
    if (!selectedA || !selectedB) return;
    
    // Mock comparison for now - would call API in real implementation
    const mockComparison: BranchComparisonRecord = {
      comparison_id: `cmp-${Date.now()}`,
      project_id: branches[0]?.project_id || '',
      branch_a_id: selectedA,
      branch_b_id: selectedB,
      differences: [
        { object_kind: 'character-profile', branch_a_value: { name: 'John' }, branch_b_value: { name: 'Jonathan' } },
        { object_kind: 'world-bible-entry', branch_a_value: { location: 'City A' }, branch_b_value: { location: 'Metropolis' } },
      ],
      created_at: new Date().toISOString(),
    };
    
    setComparison(mockComparison);
  };

  const branchA = branches.find(b => b.branch_id === selectedA);
  const branchB = branches.find(b => b.branch_id === selectedB);

  return (
    <div className="border rounded-lg p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-gray-900">Compare Branches</h3>
        <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
          ✕
        </button>
      </div>

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
              {branches.map(branch => (
                <option key={branch.branch_id} value={branch.branch_id}>
                  {branch.name}
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
              {branches.filter(b => b.branch_id !== selectedA).map(branch => (
                <option key={branch.branch_id} value={branch.branch_id}>
                  {branch.name}
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={handleCompare}
            disabled={!selectedA || !selectedB}
            className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
          >
            Compare Branches
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <span>{branchA?.name}</span>
            <span>↔</span>
            <span>{branchB?.name}</span>
          </div>

          <div className="border rounded-lg divide-y">
            {comparison.differences.map((diff, index) => (
              <div key={index} className="p-3">
                <div className="text-xs font-medium text-gray-500 mb-2 uppercase">{diff.object_kind}</div>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div className="bg-blue-50 p-2 rounded">
                    <span className="font-medium text-blue-800">{branchA?.name}:</span>
                    <pre className="mt-1 text-gray-700 overflow-x-auto">
                      {JSON.stringify(diff.branch_a_value, null, 2)}
                    </pre>
                  </div>
                  <div className="bg-green-50 p-2 rounded">
                    <span className="font-medium text-green-800">{branchB?.name}:</span>
                    <pre className="mt-1 text-gray-700 overflow-x-auto">
                      {JSON.stringify(diff.branch_b_value, null, 2)}
                    </pre>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <button onClick={onClose} className="w-full px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700">
            Close Comparison
          </button>
        </div>
      )}
    </div>
  );
}
