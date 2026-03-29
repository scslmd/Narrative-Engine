import { useQuery } from '@tanstack/react-query';
import type { StoryFlowStage } from '../../types/flow';
import { flowService } from '../../services/flow';
import StageList from './StageList';

interface FlowEditorProps {
  projectId: string;
}

export default function FlowEditor({ projectId }: FlowEditorProps) {
  const { data: stages, isLoading, isError, error } = useQuery<StoryFlowStage[]>({
    queryKey: ['flow-stages', projectId],
    queryFn: () => flowService.getStages(projectId),
  });

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
        <h2 className="text-lg font-semibold text-gray-900">Flow Stages</h2>
        <p className="text-sm text-gray-500">Current routed stage overview for this project</p>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        {stages && (
          <StageList
            stages={stages}
            updatingStageId={null}
          />
        )}
      </div>
    </div>
  );
}
