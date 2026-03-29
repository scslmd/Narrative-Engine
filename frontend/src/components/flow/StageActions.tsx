import { useState } from 'react';
import type { StoryFlowStage } from '../../types/flow';

interface StageActionsProps {
  stage: StoryFlowStage;
  onEdit?: (stageId: string) => void;
  onDelete?: (stageId: string) => void;
  isUpdating: boolean;
}

export default function StageActions({
  stage,
  onEdit,
  onDelete,
  isUpdating,
}: StageActionsProps) {
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const isDefaultStage = ['brainstorm', 'foundation', 'character', 'world_bible', 'arc_selection', 'planning', 'drafting', 'review'].includes(stage.stage_kind);

  if (!onEdit && !onDelete) return null;

  return (
    <div className="flex items-center gap-2">
      {onEdit && (
        <button
          onClick={() => onEdit(stage.stage_id)}
          disabled={isUpdating}
          className="text-xs text-blue-600 hover:text-blue-800 transition-colors"
        >
          Edit
        </button>
      )}

      {onDelete && (
        <>
          {!isDefaultStage && onEdit && <span className="text-gray-300">|</span>}
          
          {showDeleteConfirm ? (
            <div className="flex items-center gap-2">
              <button
                onClick={() => { onDelete(stage.stage_id); setShowDeleteConfirm(false); }}
                disabled={isUpdating}
                className="text-xs text-red-600 hover:text-red-800 transition-colors"
              >
                Confirm Delete
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
    </div>
  );
}
