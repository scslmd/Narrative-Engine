import { useState } from 'react';
import type { StoryFlowStage } from '../../types/flow';

interface StageActionsProps {
  stage: StoryFlowStage;
  onEdit: (stageId: string) => void;
  onDisable: (stageId: string) => void;
  onArchive: (stageId: string) => void;
  onDelete?: (stageId: string) => void;
  isUpdating: boolean;
}

export default function StageActions({
  stage,
  onEdit,
  onDisable,
  onArchive,
  onDelete,
  isUpdating,
}: StageActionsProps) {
  const [showConfirm, setShowConfirm] = useState<string | null>(null);

  const isDefaultStage = ['brainstorm', 'foundation', 'character', 'world_bible', 'arc_selection', 'planning', 'drafting', 'review'].includes(stage.stage_kind);

  if (stage.stage_configuration_state === 'ARCHIVED') {
    return (
      <button
        onClick={() => onEdit(stage.stage_id)}
        disabled={isUpdating}
        className="text-xs text-gray-500 hover:text-blue-600 transition-colors"
      >
        Restore
      </button>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <button
        onClick={() => onEdit(stage.stage_id)}
        disabled={isUpdating}
        className="text-xs text-blue-600 hover:text-blue-800 transition-colors"
      >
        Edit
      </button>

      {stage.stage_configuration_state === 'ACTIVE' && (
        <>
          <span className="text-gray-300">|</span>
          
          <button
            onClick={() => onDisable(stage.stage_id)}
            disabled={isUpdating}
            className="text-xs text-gray-600 hover:text-red-600 transition-colors"
          >
            Disable
          </button>

          <span className="text-gray-300">|</span>
          
          <button
            onClick={() => setShowConfirm('archive')}
            disabled={isUpdating}
            className="text-xs text-gray-600 hover:text-red-600 transition-colors"
          >
            Archive
          </button>

          {!isDefaultStage && onDelete && (
            <>
              <span className="text-gray-300">|</span>
              
              <button
                onClick={() => setShowConfirm('delete')}
                disabled={isUpdating}
                className="text-xs text-red-600 hover:text-red-800 transition-colors"
              >
                Delete
              </button>
            </>
          )}
        </>
      )}

      {showConfirm === 'archive' && (
        <div className="absolute bg-white border rounded-lg shadow-lg p-3 z-10">
          <p className="text-sm text-gray-700 mb-2">Archive this stage?</p>
          <div className="flex gap-2">
            <button
              onClick={() => { onArchive(stage.stage_id); setShowConfirm(null); }}
              className="px-3 py-1 bg-red-600 text-white rounded text-xs hover:bg-red-700"
            >
              Archive
            </button>
            <button
              onClick={() => setShowConfirm(null)}
              className="px-3 py-1 border rounded text-xs hover:bg-gray-50"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {showConfirm === 'delete' && onDelete && (
        <div className="absolute bg-white border rounded-lg shadow-lg p-3 z-10">
          <p className="text-sm text-gray-700 mb-2">Delete this stage permanently?</p>
          <div className="flex gap-2">
            <button
              onClick={() => { onDelete(stage.stage_id); setShowConfirm(null); }}
              className="px-3 py-1 bg-red-600 text-white rounded text-xs hover:bg-red-700"
            >
              Delete
            </button>
            <button
              onClick={() => setShowConfirm(null)}
              className="px-3 py-1 border rounded text-xs hover:bg-gray-50"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
