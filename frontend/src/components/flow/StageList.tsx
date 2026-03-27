import type { StoryFlowStage } from '../../types/flow';
import StageCard from './StageCard';
import StageActions from './StageActions';

interface StageListProps {
  stages: StoryFlowStage[];
  updatingStageId: string | null;
  onEdit: (stageId: string) => void;
  onDisable: (stageId: string) => void;
  onArchive: (stageId: string) => void;
  onDelete?: (stageId: string) => void;
  onAddStage?: (stageKind: StoryFlowStage['stage_kind']) => void;
}

export default function StageList({
  stages,
  updatingStageId,
  onEdit,
  onDisable,
  onArchive,
  onDelete,
  onAddStage,
}: StageListProps) {
  if (!stages || stages.length === 0) {
    return (
      <div className="p-6 text-center">
        <p className="text-gray-500 mb-2">No stages configured</p>
        {onAddStage && (
          <button
            onClick={() => onAddStage('brainstorm')}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Add Stage
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {stages.map((stage, index) => (
        <div key={stage.stage_id} className="relative group">
          <StageCard
            stage={stage}
            position={index}
            isUpdating={updatingStageId === stage.stage_id}
          />

          <div className="absolute right-4 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-opacity">
            <StageActions
              stage={stage}
              onEdit={onEdit}
              onDisable={onDisable}
              onArchive={onArchive}
              onDelete={onDelete}
              isUpdating={updatingStageId === stage.stage_id}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
