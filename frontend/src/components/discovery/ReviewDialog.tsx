import { useState } from 'react';
import type { StagedEntity, CascadeApplyResponse } from '../../types/discovery';
import { CharacterReviewTab } from './CharacterReviewTab';
import { RelationshipReviewTab } from './RelationshipReviewTab';
import { WorldBibleReviewTab } from './WorldBibleReviewTab';

type TabKey = 'characters' | 'relationships' | 'world_bible';

interface ReviewDialogProps {
  stageId: string;
  characters: StagedEntity[];
  relationships: StagedEntity[];
  worldBible: StagedEntity[];
  onToggleApproval: (entityId: string, approved: boolean) => void;
  onApply: () => Promise<CascadeApplyResponse>;
  onClose: () => void;
  applyLoading?: boolean;
}

export function ReviewDialog({ characters, relationships, worldBible, onToggleApproval, onApply, onClose, applyLoading }: ReviewDialogProps) {
  const [activeTab, setActiveTab] = useState<TabKey>('characters');
  const [result, setResult] = useState<CascadeApplyResponse | null>(null);

  const tabs: { key: TabKey; label: string; count: number }[] = [
    { key: 'characters', label: 'Characters', count: characters.length },
    { key: 'relationships', label: 'Relationships', count: relationships.length },
    { key: 'world_bible', label: 'World Bible', count: worldBible.length },
  ];

  const approvedCount = characters.filter((e) => e.approved).length + relationships.filter((e) => e.approved).length + worldBible.filter((e) => e.approved).length;

  const handleBulkAction = (type: TabKey, approve: boolean) => {
    const entities = type === 'characters' ? characters : type === 'relationships' ? relationships : worldBible;
    entities.forEach((e) => onToggleApproval(e.entity_id, approve));
  };

  const handleApply = async () => {
    const res = await onApply();
    setResult(res);
  };

  if (result) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 w-full max-w-lg mx-4" onClick={(e) => e.stopPropagation()}>
          <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">Applied Successfully</h2>
          <ul className="space-y-2 mb-6">
            {result.characters_added > 0 && <li className="text-green-600 dark:text-green-400">+{result.characters_added} new character{result.characters_added !== 1 ? 's' : ''}</li>}
            {result.characters_enriched > 0 && <li className="text-blue-600 dark:text-blue-400">{result.characters_enriched} existing character{result.characters_enriched !== 1 ? 's' : ''} enriched</li>}
            {result.relationships_added > 0 && <li className="text-purple-600 dark:text-purple-400">+{result.relationships_added} relationship{result.relationships_added !== 1 ? 's' : ''}</li>}
            {result.world_bible_added > 0 && <li className="text-teal-600 dark:text-teal-400">+{result.world_bible_added} world entry{result.world_bible_added !== 1 ? 'ies' : 'y'}</li>}
          </ul>
          <button onClick={onClose} className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">Done</button>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 w-full max-w-4xl mx-4 h-[80vh] flex flex-col" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Discovery Review</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 text-2xl">&times;</button>
        </div>

        <div className="flex gap-1 border-b border-gray-200 dark:border-gray-700 mb-4">
          {tabs.map((tab) => (
            <button key={tab.key} onClick={() => setActiveTab(tab.key)} className={`px-4 py-2 text-sm font-medium border-b-2 ${activeTab === tab.key ? 'border-blue-600 text-blue-600 dark:text-blue-400' : 'border-transparent text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'}`}>
              {tab.label} ({tab.count})
            </button>
          ))}
        </div>

        <div className="flex gap-2 mb-4">
          <button onClick={() => handleBulkAction(activeTab, true)} className="px-3 py-1 text-sm bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200 rounded-lg hover:bg-green-200 dark:hover:bg-green-800">Approve All</button>
          <button onClick={() => handleBulkAction(activeTab, false)} className="px-3 py-1 text-sm bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200 rounded-lg hover:bg-red-200 dark:hover:bg-red-800">Reject All</button>
        </div>

        <div className="flex-1 overflow-y-auto">
          {activeTab === 'characters' && <CharacterReviewTab entities={characters} onToggleApproval={onToggleApproval} />}
          {activeTab === 'relationships' && <RelationshipReviewTab entities={relationships} onToggleApproval={onToggleApproval} />}
          {activeTab === 'world_bible' && <WorldBibleReviewTab entities={worldBible} onToggleApproval={onToggleApproval} />}
        </div>

        <div className="flex justify-between items-center mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
          <span className="text-sm text-gray-500 dark:text-gray-400">{approvedCount} approved</span>
          <button onClick={handleApply} disabled={applyLoading || approvedCount === 0} className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed">
            {applyLoading ? 'Applying...' : `Apply ${approvedCount} change${approvedCount !== 1 ? 's' : ''}`}
          </button>
        </div>
      </div>
    </div>
  );
}
