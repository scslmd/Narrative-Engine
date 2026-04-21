import type { StoryFlowStage } from '../../types/flow';
import StageCard from './StageCard';
import StageActions from './StageActions';

interface StageListProps {
  stages: StoryFlowStage[];
  updatingStageId: string | null;
  onEdit?: (stageId: string, currentName: string) => void;
  onDelete?: (stageId: string) => void;
  onToggleState?: (stageId: string, currentState: string) => void;
  onArchive?: (stageId: string) => Promise<unknown>;
  isDefaultKind?: (kind: string) => boolean;
  onAddStage?: (stageKind: StoryFlowStage['stage_kind']) => void;
}

export default function StageList({
  stages,
  updatingStageId,
  onEdit,
  onDelete,
  onToggleState,
  onArchive,
  isDefaultKind,
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

          {(onEdit || onDelete || onToggleState || onArchive) && (
            <div className="absolute right-4 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-opacity">
              <StageActions
                stage={stage}
                onEdit={onEdit}
                onDelete={onDelete}
                onToggleState={onToggleState}
                onArchive={onArchive}
                isDefaultKind={isDefaultKind}
                isUpdating={updatingStageId === stage.stage_id}
              />
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
