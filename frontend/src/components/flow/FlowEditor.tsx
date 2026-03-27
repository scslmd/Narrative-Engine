import { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { StoryFlowStage } from '../../types/flow';
import { flowService } from '../../services/flow';
import { useToastStore } from '../../stores/toastStore';
import StageList from './StageList';

interface FlowEditorProps {
  projectId: string;
}

const STAGE_KINDS: StoryFlowStage['stage_kind'][] = [
  'brainstorm',
  'foundation',
  'character',
  'world_bible',
  'arc_selection',
  'planning',
  'drafting',
  'review',
];

export default function FlowEditor({ projectId }: FlowEditorProps) {
  const queryClient = useQueryClient();
  const addToast = useToastStore((state) => state.addToast);
  const [updatingStageId, setUpdatingStageId] = useState<string | null>(null);
  const [editingStage, setEditingStage] = useState<StoryFlowStage | null>(null);
  const [editedDisplayName, setEditedDisplayName] = useState('');
  const [editedDescription, setEditedDescription] = useState('');
  const [editedPromptGuidance, setEditedPromptGuidance] = useState('');

  const { data: stages, isLoading, isError, error } = useQuery<StoryFlowStage[]>({
    queryKey: ['flow-stages', projectId],
    queryFn: () => flowService.getStages(projectId),
  });

  const addStageMutation = useMutation({
    mutationFn: (kind: StoryFlowStage['stage_kind']) => flowService.addStage(projectId, kind),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['flow-stages', projectId] });
      addToast('Stage added successfully', 'success');
    },
    onError: (err: unknown) => {
      addToast(err instanceof Error ? err.message : 'Failed to add stage', 'error');
    },
  });

  const updateStageMutation = useMutation({
    mutationFn: ({ stageId, updates }: { stageId: string; updates: Partial<StoryFlowStage> }) =>
      flowService.updateStageWithProject(projectId, stageId, updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['flow-stages', projectId] });
      setUpdatingStageId(null);
      addToast('Stage updated successfully', 'success');
    },
    onError: (err: unknown) => {
      addToast(err instanceof Error ? err.message : 'Failed to update stage', 'error');
    },
  });

  const deleteStageMutation = useMutation({
    mutationFn: (stageId: string) => flowService.deleteStage(projectId, stageId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['flow-stages', projectId] });
      addToast('Stage deleted successfully', 'success');
    },
  });

  const handleAddStage = useCallback(
    (kind: StoryFlowStage['stage_kind']) => {
      addStageMutation.mutate(kind);
    },
    [addStageMutation]
  );

  const handleEdit = useCallback((stageId: string) => {
    if (!stages) return;
    const stage = stages.find((s) => s.stage_id === stageId) || null;
    setEditingStage(stage);
    setEditedDisplayName(stage?.display_name || '');
    setEditedDescription(stage?.description || '');
    setEditedPromptGuidance(stage?.custom_prompt_guidance || '');
  }, [stages]);

  const handleSaveEdit = useCallback(() => {
    if (!editingStage) return;
    
    const updates: Partial<StoryFlowStage> = {};
    if (editedDisplayName !== editingStage.display_name) {
      updates.display_name = editedDisplayName;
    }
    if (editedDescription !== editingStage.description) {
      updates.description = editedDescription;
    }
    if (editedPromptGuidance !== editingStage.custom_prompt_guidance) {
      // Note: custom_prompt_guidance is not in StoryFlowStage type, cast needed
      (updates as any).custom_prompt_guidance = editedPromptGuidance;
    }
    
    if (Object.keys(updates).length > 0) {
      updateStageMutation.mutate({ stageId: editingStage.stage_id, updates });
    }
    setEditingStage(null);
  }, [editingStage, editedDisplayName, editedDescription, editedPromptGuidance, updateStageMutation]);

  const handleCloseEdit = useCallback(() => {
    setEditingStage(null);
    setEditedDisplayName('');
    setEditedDescription('');
    setEditedPromptGuidance('');
  }, []);

  const handleDisable = useCallback(
    async (stageId: string) => {
      setUpdatingStageId(stageId);
      try {
        await flowService.disableStage(projectId, stageId);
        queryClient.invalidateQueries({ queryKey: ['flow-stages', projectId] });
        addToast('Stage disabled', 'success');
      } catch (err) {
        addToast(err instanceof Error ? err.message : 'Failed to disable stage', 'error');
      } finally {
        setUpdatingStageId(null);
      }
    },
    [queryClient, projectId, addToast]
  );

  const handleArchive = useCallback(
    async (stageId: string) => {
      setUpdatingStageId(stageId);
      try {
        await flowService.archiveStage(projectId, stageId);
        queryClient.invalidateQueries({ queryKey: ['flow-stages', projectId] });
        addToast('Stage archived', 'success');
      } catch (err) {
        addToast(err instanceof Error ? err.message : 'Failed to archive stage', 'error');
      } finally {
        setUpdatingStageId(null);
      }
    },
    [queryClient, projectId, addToast]
  );

  const handleDelete = useCallback(
    async (stageId: string) => {
      try {
        await deleteStageMutation.mutateAsync(stageId);
      } catch (err) {
        addToast(err instanceof Error ? err.message : 'Failed to delete stage', 'error');
      }
    },
    [deleteStageMutation, addToast]
  );

  if (isLoading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="p-4">
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error instanceof Error ? error.message : 'Failed to load flow stages'}
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      <div className="p-4 border-b">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-lg font-semibold text-gray-900">Flow Editor</h2>
          
          <select
            onChange={(e) => {
              const kind = e.target.value as StoryFlowStage['stage_kind'];
              if (kind) handleAddStage(kind);
              e.target.value = '';
            }}
            className="px-3 py-1.5 border rounded text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            defaultValue=""
          >
            <option value="" disabled>Add Stage</option>
            {STAGE_KINDS.map((kind) => (
              <option key={kind} value={kind}>
                {kind.replace('_', ' ').charAt(0).toUpperCase() + kind.replace('_', ' ').slice(1)}
              </option>
            ))}
          </select>
        </div>

        <p className="text-sm text-gray-500">Configure your story development stages</p>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        {stages && (
          <StageList
            stages={stages}
            updatingStageId={updatingStageId}
            onEdit={handleEdit}
            onDisable={handleDisable}
            onArchive={handleArchive}
            onDelete={handleDelete}
            onAddStage={handleAddStage}
          />
        )}
      </div>

      {editingStage && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">Edit Stage</h3>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Display Name</label>
                <input
                  type="text"
                  value={editedDisplayName}
                  onChange={(e) => setEditedDisplayName(e.target.value)}
                  className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <textarea
                  value={editedDescription}
                  onChange={(e) => setEditedDescription(e.target.value)}
                  rows={3}
                  className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Custom Prompt Guidance</label>
                <textarea
                  value={editedPromptGuidance}
                  onChange={(e) => setEditedPromptGuidance(e.target.value)}
                  rows={4}
                  className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>

              <div className="flex gap-2">
                <button
                  onClick={handleSaveEdit}
                  disabled={updateStageMutation.isPending}
                  className="flex-1 px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700 disabled:opacity-50"
                >
                  {updateStageMutation.isPending ? 'Saving...' : 'Save'}
                </button>
                <button
                  onClick={handleCloseEdit}
                  className="flex-1 px-4 py-2 bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
