import type { StoryBranch } from '../../types/branches';

interface BranchCardProps {
  branch: StoryBranch;
  isActive: boolean;
  onSetActive: (branchId: string) => void;
  onCompare: (branchAId: string, branchBId: string) => void;
}

export function BranchCard({ branch, isActive, onSetActive, onCompare }: BranchCardProps) {
  const getStateColor = () => {
    switch (branch.state) {
      case 'active':
        return 'bg-green-100 text-green-800 border-green-300';
      case 'merged':
        return 'bg-blue-100 text-blue-800 border-blue-300';
      case 'archived':
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  return (
    <div className={`border rounded-lg p-4 ${isActive ? 'border-blue-500 bg-blue-50' : 'bg-white hover:border-gray-300'}`}>
      <div className="flex items-start justify-between mb-2">
        <h4 className="font-semibold text-gray-900">{branch.name}</h4>
        <span className={`px-2 py-1 rounded text-xs font-medium border ${getStateColor()}`}>
          {branch.state}
        </span>
      </div>

      {branch.description && (
        <p className="text-sm text-gray-600 mb-3 line-clamp-2">
          {branch.description}
        </p>
      )}

      <div className="flex items-center justify-between text-xs text-gray-500 mb-3">
        <span>Created: {formatDate(branch.created_at)}</span>
        {branch.parent_branch_id && (
          <span>From parent branch</span>
        )}
      </div>

      <div className="flex gap-2">
        {branch.state === 'active' ? (
          <span className="text-xs text-blue-600 font-medium">Currently active</span>
        ) : (
          <button
            onClick={() => onSetActive(branch.branch_id)}
            disabled={branch.state === 'archived'}
            className={`px-3 py-1.5 text-sm rounded ${branch.state === 'archived' ? 'bg-gray-200 text-gray-400 cursor-not-allowed' : 'bg-blue-600 text-white hover:bg-blue-700'}`}
          >
            Set Active
          </button>
        )}

        {branch.state !== 'archived' && (
          <button
            onClick={() => onCompare(branch.branch_id, branch.parent_branch_id || '')}
            className="px-3 py-1.5 text-sm rounded bg-gray-600 text-white hover:bg-gray-700"
          >
            Compare
          </button>
        )}
      </div>
    </div>
  );
}
