import { useState } from 'react';
import type { StoryFlowStage } from '../../types/flow';

interface StageActionsProps {
  stage: StoryFlowStage;
  onEdit?: (stageId: string, currentName: string) => void;
  onDelete?: (stageId: string) => void;
  onToggleState?: (stageId: string, currentState: string) => void;
  onArchive?: (stageId: string) => Promise<unknown>;
  isDefaultKind?: (kind: string) => boolean;
  isUpdating: boolean;
}

export default function StageActions({
  stage,
  onEdit,
  onDelete,
  onToggleState,
  onArchive,
  isDefaultKind,
  isUpdating,
}: StageActionsProps) {
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const isArchived = stage.stage_configuration_state === 'ARCHIVED';
  const stateLabel = stage.stage_configuration_state === 'DISABLED' ? 'Enable' : 'Disable';

  if (!onEdit && !onDelete && !onToggleState && !onArchive) return null;

  return (
    <div className="flex items-center gap-2">
      {onToggleState && !isArchived && (
        <button
          onClick={() => onToggleState(stage.stage_id, stage.stage_configuration_state)}
          disabled={isUpdating}
          className="text-xs text-amber-600 hover:text-amber-800 transition-colors"
          title={stateLabel === 'Enable' ? 'Enable stage' : 'Disable stage'}
        >
          {stateLabel}
        </button>
      )}

      {onEdit && (
        <button
          onClick={() => onEdit(stage.stage_id, stage.display_name)}
          disabled={isUpdating}
          className="text-xs text-blue-600 hover:text-blue-800 transition-colors"
        >
          Rename
        </button>
      )}

      {onDelete && isDefaultKind?.(stage.stage_kind) !== true && (
        <>
          {(onEdit || onToggleState) && <span className="text-gray-300">|</span>}
          
          {showDeleteConfirm ? (
            <div className="flex items-center gap-2">
              <button
                onClick={() => { onDelete(stage.stage_id); setShowDeleteConfirm(false); }}
                disabled={isUpdating}
                className="text-xs text-red-600 hover:text-red-800 transition-colors"
              >
                Confirm
              </button>
              <button
                onClick={() => setShowDeleteConfirm(false)}
                className="text-xs text-gray-600 hover:text-gray-800 transition-colors"
              >
                Cancel
              </button>
            </div>
          ) : (
            <button
              onClick={() => setShowDeleteConfirm(true)}
              disabled={isUpdating}
              className="text-xs text-red-600 hover:text-red-800 transition-colors"
            >
              Delete
            </button>
          )}
        </>
      )}

      {onArchive && !isArchived && (
        <>
          <span className="text-gray-300">|</span>
          <button
            onClick={() => onArchive(stage.stage_id)}
            disabled={isUpdating}
            className="text-xs text-gray-600 hover:text-gray-800 transition-colors"
          >
            Archive
          </button>
        </>
      )}
    </div>
  );
}
