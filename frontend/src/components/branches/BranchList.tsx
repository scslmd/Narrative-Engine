import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import type { StoryBranch } from '../../types/branches';
import { getBranches, setActiveBranch } from '../../services/branches';
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

  const activeBranch = branches.find((branch) => branch.branch_state === 'ACTIVE');

  const setActiveMutation = useMutation({
    mutationFn: (branchId: string) => setActiveBranch(projectId, branchId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['branches', projectId] });
      queryClient.invalidateQueries({ queryKey: ['active-branch', projectId] });
    },
    onError: (error) => {
      addToast(error instanceof Error ? error.message : 'Failed to set active branch', 'error');
    },
  });

  const handleSetActive = async (branchId: string) => {
    await setActiveMutation.mutateAsync(branchId);
  };

  if (isLoading) {
    return <div className="text-gray-500">Loading branches...</div>;
  }

  return (
    <div className="space-y-4">
      {branches.length === 0 ? (
        <div className="border rounded-lg p-8 text-center bg-gray-50">
          <p className="text-gray-600 mb-4">No branches yet</p>
          <p className="text-sm text-gray-500">
            Branch creation is unavailable in the UI until branch points are exposed by the API.
          </p>
        </div>
      ) : (
        <div className="grid gap-4">
          {branches.map((branch) => (
            <BranchCard
              key={branch.branch_id}
              branch={branch}
              isActive={activeBranch?.branch_id === branch.branch_id}
              onSetActive={handleSetActive}
            />
          ))}
        </div>
      )}
    </div>
  );
}
