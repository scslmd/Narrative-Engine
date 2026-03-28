import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { StoryBranch } from '../../types/branches';
import { createBranch, createBranchComparison, getBranches, setActiveBranch } from '../../services/branches';
import { useToastStore } from '../../stores/toastStore';
import { BranchCard } from './BranchCard';

interface BranchListProps {
  projectId: string;
}

interface CreateBranchFormState {
  branchName: string;
  branchPointId: string;
}

export function BranchList({ projectId }: BranchListProps) {
  const queryClient = useQueryClient();
  const addToast = useToastStore((state) => state.addToast);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createFormState, setCreateFormState] = useState<CreateBranchFormState>({
    branchName: '',
    branchPointId: '',
  });

  const { data: branches = [], isLoading } = useQuery<StoryBranch[]>({
    queryKey: ['branches', projectId],
    queryFn: () => getBranches(projectId),
  });

  const activeBranch = branches.find(b => b.state === 'active');

  const setActiveMutation = useMutation({
    mutationFn: (branchId: string) => setActiveBranch(projectId, branchId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['branches', projectId] });
      queryClient.invalidateQueries({ queryKey: ['active-branch', projectId] });
    },
  });

  const createBranchMutation = useMutation({
    mutationFn: ({ branchName, branchPointId }: CreateBranchFormState) => 
      createBranch(projectId, branchName, branchPointId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['branches', projectId] });
      setShowCreateModal(false);
      setCreateFormState({ branchName: '', branchPointId: '' });
      addToast('Branch created successfully', 'success');
    },
    onError: (error) => {
      addToast(error instanceof Error ? error.message : 'Failed to create branch', 'error');
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

  const handleCreateBranch = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!createFormState.branchName.trim()) {
      addToast('Branch name is required', 'warning');
      return;
    }
    
    if (!createFormState.branchPointId.trim()) {
      addToast('Branch point is required', 'warning');
      return;
    }

    await createBranchMutation.mutateAsync(createFormState);
  };

  const handleOpenCreateModal = () => {
    setCreateFormState({
      branchName: '',
      branchPointId: activeBranch?.branch_id || '',
    });
    setShowCreateModal(true);
  };

  const handleCloseCreateModal = () => {
    setShowCreateModal(false);
    setCreateFormState({ branchName: '', branchPointId: '' });
  };

  if (isLoading) {
    return <div className="text-gray-500">Loading branches...</div>;
  }

  return (
    <div className="space-y-4">
      {branches.length === 0 ? (
        <div className="border rounded-lg p-8 text-center bg-gray-50">
          <p className="text-gray-600 mb-4">No branches yet</p>
          <button 
            onClick={handleOpenCreateModal}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Create First Branch
          </button>
        </div>
      ) : (
        <>
          <div className="flex justify-end">
            <button
              onClick={handleOpenCreateModal}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              + New Branch
            </button>
          </div>
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
        </>
      )}

      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
            <h3 className="text-lg font-semibold mb-4">Create New Branch</h3>
            <form onSubmit={handleCreateBranch} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Branch Name
                </label>
                <input
                  type="text"
                  value={createFormState.branchName}
                  onChange={(e) => setCreateFormState({ ...createFormState, branchName: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Enter branch name"
                  autoFocus
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Branch Point
                </label>
                <select
                  value={createFormState.branchPointId}
                  onChange={(e) => setCreateFormState({ ...createFormState, branchPointId: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">Select a branch point</option>
                  {branches.map(branch => (
                    <option key={branch.branch_id} value={branch.branch_id}>
                      {branch.name} {branch.state === 'active' ? '(active)' : ''}
                    </option>
                  ))}
                </select>
                <p className="text-xs text-gray-500 mt-1">
                  This branch will diverge from the selected branch.
                </p>
              </div>
              <div className="flex gap-2">
                <button
                  type="submit"
                  disabled={createBranchMutation.isPending}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
                >
                  {createBranchMutation.isPending ? 'Creating...' : 'Create Branch'}
                </button>
                <button
                  type="button"
                  onClick={handleCloseCreateModal}
                  className="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
