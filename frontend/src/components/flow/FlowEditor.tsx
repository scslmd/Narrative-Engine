import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { StoryFlowStage, StageKind } from '../../types/flow';
import { getStages, addStage, renameStage, deleteStage, updateStageWithProject, archiveStage } from '../../services/flow';
import StageList from './StageList';
import { useState } from 'react';

interface FlowEditorProps {
  projectId: string;
}

const STAGE_KIND_OPTIONS: { value: StageKind; label: string }[] = [
  { value: 'brainstorm', label: 'Brainstorm' },
  { value: 'foundation', label: 'Foundation' },
  { value: 'character', label: 'Character' },
  { value: 'world_bible', label: 'World Bible' },
  { value: 'arc_selection', label: 'Arc Selection' },
  { value: 'planning', label: 'Planning' },
  { value: 'drafting', label: 'Drafting' },
  { value: 'review', label: 'Review' },
];

export default function FlowEditor({ projectId }: FlowEditorProps) {
  const queryClient = useQueryClient();
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [editingStageId, setEditingStageId] = useState<string | null>(null);
  const [addStageKind, setAddStageKind] = useState<StageKind>('brainstorm');
  const [newStageName, setNewStageName] = useState('');
  const [editingName, setEditingName] = useState('');
  const [error, setError] = useState<string | null>(null);

  const { data: stages, isLoading, isError } = useQuery<StoryFlowStage[]>({
    queryKey: ['flow-stages', projectId],
    queryFn: () => getStages(projectId),
  });

  const addStageMutation = useMutation({
    mutationFn: ({ kind, name }: { kind: StageKind; name: string }) => addStage(projectId, kind, name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['flow-stages', projectId] });
      setShowAddDialog(false);
      setNewStageName('');
      setError(null);
    },
    onError: (err: Error) => {
      setError(err.message);
    },
  });

  const renameMutation = useMutation({
    mutationFn: ({ stageId, displayName }: { stageId: string; displayName: string }) =>
      renameStage(projectId, stageId, displayName),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['flow-stages', projectId] });
      setEditingStageId(null);
      setError(null);
    },
    onError: (err: Error) => {
      setError(err.message);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (stageId: string) => deleteStage(projectId, stageId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['flow-stages', projectId] });
      setError(null);
    },
    onError: (err: Error) => {
      setError(err.message);
    },
  });

  const toggleStateMutation = useMutation({
    mutationFn: ({
      stageId,
      currentState,
    }: {
      stageId: string;
      currentState: string;
    }) => {
      const newState = currentState === 'DISABLED' ? 'ENABLED' : 'DISABLED';
      return updateStageWithProject(projectId, stageId, {
        stage_configuration_state: newState,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['flow-stages', projectId] });
      setError(null);
    },
    onError: (err: Error) => {
      setError(err.message);
    },
  });

  const archiveMutation = useMutation({
    mutationFn: (stageId: string) => archiveStage(projectId, stageId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['flow-stages', projectId] });
      setError(null);
    },
    onError: (err: Error) => {
      setError(err.message);
    },
  });

  const handleAddStage = () => {
    if (!newStageName.trim()) {
      setError('Stage name is required');
      return;
    }
    addStageMutation.mutate({ kind: addStageKind, name: newStageName.trim() });
  };

  const handleRename = (stageId: string, currentName: string) => {
    setEditingStageId(stageId);
    setEditingName(currentName);
  };

  const submitRename = () => {
    if (!editingStageId || !editingName.trim()) return;
    renameMutation.mutate({ stageId: editingStageId, displayName: editingName.trim() });
  };

  const handleDelete = (stageId: string) => {
    deleteMutation.mutate(stageId);
  };

  const handleToggleState = (stageId: string, currentState: string) => {
    toggleStateMutation.mutate({ stageId, currentState });
  };

  const isDefaultKind = (kind: string) =>
    ['brainstorm', 'foundation', 'character', 'world_bible', 'arc_selection', 'planning', 'drafting', 'review'].includes(kind);

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
          Failed to load flow stages
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      <div className="p-4 border-b flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">Flow Stages</h2>
          <p className="text-sm text-gray-500">Current routed stage overview for this project</p>
        </div>
        <button
          onClick={() => setShowAddDialog(true)}
          className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
        >
          Add Stage
        </button>
      </div>

      {error && (
        <div className="mx-4 mt-3 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <div className="flex-1 overflow-y-auto p-4">
        {stages && (
          <StageList
            stages={stages}
            updatingStageId={editingStageId}
            onEdit={handleRename}
            onDelete={handleDelete}
            onToggleState={handleToggleState}
            onArchive={archiveMutation.mutateAsync.bind(archiveMutation)}
            isDefaultKind={isDefaultKind}
          />
        )}
      </div>

      {showAddDialog && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-md p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Add New Stage</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Stage Kind</label>
                <select
                  value={addStageKind}
                  onChange={(e) => setAddStageKind(e.target.value as StageKind)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                >
                  {STAGE_KIND_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Stage Name</label>
                <input
                  type="text"
                  value={newStageName}
                  onChange={(e) => setNewStageName(e.target.value)}
                  placeholder="Enter stage name..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                  autoFocus
                  onKeyDown={(e) => e.key === 'Enter' && handleAddStage()}
                />
              </div>
              <div className="flex justify-end gap-2">
                <button
                  onClick={() => { setShowAddDialog(false); setError(null); }}
                  className="px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-100 rounded"
                >
                  Cancel
                </button>
                <button
                  onClick={handleAddStage}
                  disabled={addStageMutation.isPending}
                  className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
                >
                  {addStageMutation.isPending ? 'Adding...' : 'Add'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {editingStageId && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-md p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Rename Stage</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Stage Name</label>
                <input
                  type="text"
                  value={editingName}
                  onChange={(e) => setEditingName(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                  autoFocus
                  onKeyDown={(e) => e.key === 'Enter' && submitRename()}
                />
              </div>
              <div className="flex justify-end gap-2">
                <button
                  onClick={() => { setEditingStageId(null); setError(null); }}
                  className="px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-100 rounded"
                >
                  Cancel
                </button>
                <button
                  onClick={submitRename}
                  disabled={renameMutation.isPending || !editingName.trim()}
                  className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
                >
                  {renameMutation.isPending ? 'Saving...' : 'Save'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
