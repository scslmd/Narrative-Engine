import type { StoryFlowStage } from '../../types/flow';

const KIND_COLORS: Record<string, string> = {
  brainstorm: 'bg-purple-100 text-purple-700',
  foundation: 'bg-blue-100 text-blue-700',
  character: 'bg-green-100 text-green-700',
  world_bible: 'bg-yellow-100 text-yellow-700',
  arc_selection: 'bg-orange-100 text-orange-700',
  planning: 'bg-indigo-100 text-indigo-700',
  drafting: 'bg-red-100 text-red-700',
  review: 'bg-gray-100 text-gray-700',
};

const STATE_COLORS: Record<string, string> = {
  ACTIVE: 'bg-green-50 text-green-600 border-green-200',
  DISABLED: 'bg-gray-50 text-gray-400 border-gray-200',
  ARCHIVED: 'bg-red-50 text-red-400 border-red-200',
};

interface StageCardProps {
  stage: StoryFlowStage;
  position: number;
  isUpdating: boolean;
}

export default function StageCard({ stage, position, isUpdating }: StageCardProps) {
  const kindColor = KIND_COLORS[stage.stage_kind] || 'bg-gray-100 text-gray-700';
  const stateColor = STATE_COLORS[stage.stage_configuration_state];

  return (
    <div className={`p-4 rounded-lg border ${isUpdating ? 'border-blue-300 bg-blue-50' : 'border-gray-200 bg-white'} transition-all`}>
      <div className="flex items-center gap-3">
        <span className="text-sm font-mono text-gray-400 w-6">{position + 1}</span>

        <div className="flex-1 min-w-0">
          <h4 className={`font-semibold truncate ${isUpdating ? 'text-blue-900' : 'text-gray-900'}`}>
            {stage.display_name}
            {isUpdating && <span className="ml-2 text-sm text-blue-600">Updating...</span>}
          </h4>

          <div className="flex items-center gap-2 mt-1 flex-wrap">
            <span className={`px-2 py-0.5 rounded text-xs font-medium capitalize ${kindColor}`}>
              {stage.stage_kind.replace('_', ' ')}
            </span>

            <span className={`px-2 py-0.5 rounded text-xs border ${stateColor}`}>
              {stage.stage_configuration_state}
            </span>

            {stage.progress_percentage !== undefined && (
              <div className="flex items-center gap-1">
                <div className="w-16 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-blue-500 transition-all"
                    style={{ width: `${stage.progress_percentage}%` }}
                  />
                </div>
                <span className="text-xs text-gray-500">{stage.progress_percentage}%</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {stage.description && (
        <p className="mt-2 text-sm text-gray-600 line-clamp-2">
          {stage.description}
        </p>
      )}
    </div>
  );
}
