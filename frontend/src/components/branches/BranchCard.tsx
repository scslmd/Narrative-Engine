import type { StoryBranch } from '../../types/branches';

interface BranchCardProps {
  branch: StoryBranch;
  isActive: boolean;
  onSetActive: (branchId: string) => void;
}

export function BranchCard({ branch, isActive, onSetActive }: BranchCardProps) {
  const getStateColor = () => {
    switch (branch.branch_state) {
      case 'ACTIVE':
        return 'bg-green-100 text-green-800 border-green-300';
      case 'ARCHIVED':
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  return (
    <div className={`border rounded-lg p-4 ${isActive ? 'border-blue-500 bg-blue-50' : 'bg-white hover:border-gray-300'}`}>
      <div className="flex items-start justify-between mb-2">
        <h4 className="font-semibold text-gray-900">{branch.branch_name}</h4>
        <span className={`px-2 py-1 rounded text-xs font-medium border ${getStateColor()}`}>
          {branch.branch_state}
        </span>
      </div>

      <div className="text-xs text-gray-500 mb-3">
        <span>Branch point: {branch.branch_point_id}</span>
      </div>

      <div className="flex gap-2">
        {branch.branch_state === 'ACTIVE' ? (
          <span className="text-xs text-blue-600 font-medium">Currently active</span>
        ) : (
          <button
            onClick={() => onSetActive(branch.branch_id)}
            disabled={branch.branch_state === 'ARCHIVED'}
            className={`px-3 py-1.5 text-sm rounded ${branch.branch_state === 'ARCHIVED' ? 'bg-gray-200 text-gray-400 cursor-not-allowed' : 'bg-blue-600 text-white hover:bg-blue-700'}`}
          >
            Set Active
          </button>
        )}
      </div>
    </div>
  );
}
