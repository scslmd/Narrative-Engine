import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { StoryBranch } from '../../types/branches';
import { getBranches, setActiveBranch } from '../../services/branches';
import { BranchCard } from './BranchCard';

interface BranchListProps {
  projectId: string;
}

export function BranchList({ projectId }: BranchListProps) {
  const queryClient = useQueryClient();
  const [selectedForCompare, setSelectedForCompare] = useState<string | null>(null);

  const { data: branches = [], isLoading } = useQuery<StoryBranch[]>({
    queryKey: ['branches', projectId],
    queryFn: () => getBranches(projectId),
  });

  const setActiveMutation = useMutation({
    mutationFn: (branchId: string) => setActiveBranch(projectId, branchId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['branches', projectId] });
      queryClient.invalidateQueries({ queryKey: ['active-branch', projectId] });
    },
  });

  const handleSetActive = async (branchId: string) => {
    await setActiveMutation.mutateAsync(branchId);
  };

  const handleCompare = (branchAId: string, branchBId: string) => {
    if (!selectedForCompare) {
      setSelectedForCompare(branchAId);
    } else if (selectedForCompare !== branchAId) {
      // Trigger comparison between selected and current
      console.log('Comparing branches:', selectedForCompare, branchAId);
      setSelectedForCompare(null);
    } else {
      setSelectedForCompare(null);
    }
  };

  const activeBranch = branches.find(b => b.state === 'active');

  if (isLoading) {
    return <div className="text-gray-500">Loading branches...</div>;
  }

  if (branches.length === 0) {
    return (
      <div className="border rounded-lg p-8 text-center bg-gray-50">
        <p className="text-gray-600 mb-4">No branches yet</p>
        <button className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
          Create First Branch
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {selectedForCompare && (
        <div className="bg-yellow-50 border border-yellow-300 rounded p-3 text-sm text-yellow-800">
          Select another branch to compare with the selected one
        </div>
      )}

      <div className="grid gap-4">
        {branches.map(branch => (
          <BranchCard
            key={branch.branch_id}
            branch={branch}
            isActive={activeBranch?.branch_id === branch.branch_id}
            onSetActive={handleSetActive}
            onCompare={handleCompare}
          />
        ))}
      </div>
    </div>
  );
}
