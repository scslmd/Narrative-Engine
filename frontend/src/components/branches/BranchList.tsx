import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { StoryBranch } from '../../types/branches';
import { createBranchComparison, getBranches, setActiveBranch } from '../../services/branches';
import { useToastStore } from '../../stores/toastStore';
import { BranchCard } from './BranchCard';

interface BranchListProps {
  projectId: string;
}

export function BranchList({ projectId }: BranchListProps) {
  const queryClient = useQueryClient();
  const addToast = useToastStore((state) => state.addToast);

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

  const handleCompare = async (branchAId: string, branchBId: string) => {
    if (!branchBId) {
      addToast('Branch comparison requires a parent branch', 'warning');
      return;
    }

    try {
      await createBranchComparison(projectId, branchAId, branchBId);
      addToast('Comparison created', 'success');
    } catch (error) {
      addToast(error instanceof Error ? error.message : 'Failed to compare branches', 'error');
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
