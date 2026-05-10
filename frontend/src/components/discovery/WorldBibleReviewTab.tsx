import type { StagedEntity } from '../../types/discovery';

interface WorldBibleReviewTabProps {
  entities: StagedEntity[];
  onToggleApproval: (entityId: string, approved: boolean) => void;
}

export function WorldBibleReviewTab({ entities, onToggleApproval }: WorldBibleReviewTabProps) {
  const confidenceBadge = (entity: StagedEntity) => {
    const label = entity.confidence >= 0.7 ? 'High' : entity.confidence >= 0.4 ? 'Medium' : 'Low';
    const color = entity.confidence >= 0.7 ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' : entity.confidence >= 0.4 ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200' : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
    return <span className={`px-2 py-0.5 text-xs rounded-full ${color}`}>{label}</span>;
  };

  const renderEntity = (entity: StagedEntity) => {
    const title = entity.entity_json.title as string;
    const entryType = entity.entity_json.entry_type as string;
    const summary = entity.entity_json.summary as string;

    return (
      <div key={entity.entity_id} className={`flex items-center justify-between p-3 border rounded-lg ${entity.approved ? 'border-blue-300 bg-blue-50 dark:border-blue-600 dark:bg-blue-900/20' : 'border-gray-200 dark:border-gray-700'}`}>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-medium text-gray-900 dark:text-white">{title}</span>
            <span className="px-2 py-0.5 text-xs rounded-full bg-teal-100 text-teal-800 dark:bg-teal-900 dark:text-teal-200">{entryType}</span>
            {confidenceBadge(entity)}
          </div>
          {summary && <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">{summary}</p>}
          {entity.source_excerpt && (
            <details className="mt-2">
              <summary className="text-xs text-blue-600 dark:text-blue-400 cursor-pointer">Source excerpt</summary>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 italic">{entity.source_excerpt}</p>
            </details>
          )}
        </div>
        <div className="flex gap-2 ml-4">
          <button onClick={() => onToggleApproval(entity.entity_id, true)} className={`px-3 py-1 text-sm rounded-lg ${entity.approved ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-600'}`}>
            {entity.approved ? 'Approved' : 'Approve'}
          </button>
          <button onClick={() => onToggleApproval(entity.entity_id, false)} className="px-3 py-1 text-sm bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-200 rounded-lg hover:bg-red-100 dark:hover:bg-red-900">
            Reject
          </button>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-3">
      <div className="text-sm text-gray-500 dark:text-gray-400 mb-2">{entities.length} world entry{entities.length !== 1 ? 'ies' : 'y'} discovered</div>
      <div className="space-y-2">{entities.map(renderEntity)}</div>
    </div>
  );
}
