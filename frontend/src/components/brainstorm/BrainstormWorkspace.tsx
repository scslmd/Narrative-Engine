import { useState, type KeyboardEvent } from 'react';
import type {
  BrainstormItem,
  BrainstormItemCreateRequest,
  BrainstormItemPromoteRequest,
  BrainstormItemStatus,
} from '../../types/brainstorm';
import type { BrainstormItemType } from '../../types/braindump';

interface BrainstormWorkspaceProps {
  projectId: string;
  items?: BrainstormItem[];
  onItemAdd?: (item: BrainstormItemCreateRequest) => void;
  onClusterCreate?: (itemIds: string[]) => void;
  onPromote?: (request: BrainstormItemPromoteRequest) => Promise<void>;
}

const TARGET_TYPES = [
  { value: 'character', label: 'Character' },
  { value: 'world_bible', label: 'World Bible' },
  { value: 'arc', label: 'Arc' },
];

const STATUS_OPTIONS: Array<{ value: BrainstormItemStatus; label: string }> = [
  { value: 'keep', label: 'Keep' },
  { value: 'park', label: 'Park' },
  { value: 'discard', label: 'Discard' },
];

const CATEGORY_BADGE_STYLES: Record<BrainstormItemType, { color: string; label: string }> = {
  character: { color: 'bg-blue-100 dark:bg-blue-900/40 text-blue-800 dark:text-blue-300 border-blue-200 dark:border-blue-800', label: 'Character' },
  location: { color: 'bg-green-100 dark:bg-green-900/40 text-green-800 dark:text-green-300 border-green-200 dark:border-green-800', label: 'Location' },
  plot_point: { color: 'bg-amber-100 dark:bg-amber-900/40 text-amber-800 dark:text-amber-300 border-amber-200 dark:border-amber-800', label: 'Plot Point' },
  theme: { color: 'bg-purple-100 dark:bg-purple-900/40 text-purple-800 dark:text-purple-300 border-purple-200 dark:border-purple-800', label: 'Theme' },
  conflict: { color: 'bg-red-100 dark:bg-red-900/40 text-red-800 dark:text-red-300 border-red-200 dark:border-red-800', label: 'Conflict' },
  world_building: { color: 'bg-teal-100 dark:bg-teal-900/40 text-teal-800 dark:text-teal-300 border-teal-200 dark:border-teal-800', label: 'World' },
  dialogue: { color: 'bg-pink-100 dark:bg-pink-900/40 text-pink-800 dark:text-pink-300 border-pink-200 dark:border-pink-800', label: 'Dialogue' },
  relationship: { color: 'bg-orange-100 dark:bg-orange-900/40 text-orange-800 dark:text-orange-300 border-orange-200 dark:border-orange-800', label: 'Relationship' },
  object: { color: 'bg-cyan-100 dark:bg-cyan-900/40 text-cyan-800 dark:text-cyan-300 border-cyan-200 dark:border-cyan-800', label: 'Object' },
  rule: { color: 'bg-indigo-100 dark:bg-indigo-900/40 text-indigo-800 dark:text-indigo-300 border-indigo-200 dark:border-indigo-800', label: 'Rule' },
};

export function BrainstormWorkspace({
  projectId,
  items = [],
  onItemAdd,
  onClusterCreate,
  onPromote,
}: BrainstormWorkspaceProps) {
  const [newItemContent, setNewItemContent] = useState('');
  const [newItemStatus, setNewItemStatus] = useState<BrainstormItemStatus>('keep');
  const [newItemTags, setNewItemTags] = useState('');
  const [selectedItems, setSelectedItems] = useState<Set<string>>(new Set());
  const [filter, setFilter] = useState<'all' | BrainstormItemStatus>('all');

  // Promotion dialog state
  const [promoteOpen, setPromoteOpen] = useState(false);
  const [promoteItemId, setPromoteItemId] = useState<string | null>(null);
  const [promoteTargetKind, setPromoteTargetKind] = useState('character');
  const [promoteTargetId, setPromoteTargetId] = useState('');
  const [promoteError, setPromoteError] = useState<string | null>(null);
  const [promoteLoading, setPromoteLoading] = useState(false);

  const filteredItems = items.filter((item) => filter === 'all' || item.status === filter);

  const handleAddItem = () => {
    const content = newItemContent.trim();
    if (!content || !onItemAdd) {
      return;
    }

    const tags = parseTags(newItemTags);
    onItemAdd({
      project_id: projectId,
      content,
      status: newItemStatus,
      tags,
    });

    setNewItemContent('');
    setNewItemTags('');
    setNewItemStatus('keep');
  };

  const handleToggleSelect = (itemId: string) => {
    setSelectedItems((prev) => {
      const next = new Set(prev);
      if (next.has(itemId)) {
        next.delete(itemId);
      } else {
        next.add(itemId);
      }
      return next;
    });
  };

  const handleCreateCluster = () => {
    if (!onClusterCreate || selectedItems.size < 2) {
      return;
    }

    onClusterCreate(Array.from(selectedItems));
    setSelectedItems(new Set());
  };

  const handleOpenPromote = (itemId: string) => {
    setPromoteItemId(itemId);
    setPromoteTargetKind('character');
    setPromoteTargetId('');
    setPromoteError(null);
    setPromoteOpen(true);
  };

  const handleClosePromote = () => {
    setPromoteOpen(false);
    setPromoteItemId(null);
    setPromoteError(null);
    setPromoteLoading(false);
  };

  const handlePromoteSubmit = async () => {
    if (!promoteItemId || !onPromote) return;
    if (!promoteTargetId.trim()) {
      setPromoteError('Target ID is required');
      return;
    }

    setPromoteLoading(true);
    setPromoteError(null);

    try {
      await onPromote({
        item_id: promoteItemId,
        project_id: projectId,
        target_object_kind: promoteTargetKind,
        target_object_id: promoteTargetId.trim(),
      });
      handleClosePromote();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Promotion failed';
      setPromoteError(message);
    } finally {
      setPromoteLoading(false);
    }
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleAddItem();
    }
  };

  const isAddDisabled = !newItemContent.trim() || !onItemAdd;
  const isClusterDisabled = selectedItems.size < 2 || !onClusterCreate;

  return (
    <div className="flex flex-col h-full bg-gray-50 dark:bg-slate-900">
      <div className="p-4 bg-white dark:bg-slate-800 border-b border-gray-200 dark:border-slate-700">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-slate-100">Brainstorm</h2>
            <p className="text-sm text-gray-500 dark:text-slate-400 mt-1">
              Capture raw ideas, sort them by status, and cluster related notes.
            </p>
          </div>
          <span className="text-sm text-gray-500 dark:text-slate-400">
            {items.length} items | {selectedItems.size} selected
          </span>
        </div>

        <div className="grid gap-2 md:grid-cols-[1fr_auto_auto]">
          <input
            type="text"
            value={newItemContent}
            onChange={(e) => setNewItemContent(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Add a new idea or note..."
            className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <select
            value={newItemStatus}
            onChange={(e) => setNewItemStatus(e.target.value as BrainstormItemStatus)}
            className="px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {STATUS_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
          <button
            onClick={handleAddItem}
            disabled={isAddDisabled}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Add
          </button>
        </div>

        <div className="mt-3">
          <label className="block text-xs font-medium text-gray-600 dark:text-slate-400 mb-1">Tags</label>
          <input
            type="text"
            value={newItemTags}
            onChange={(e) => setNewItemTags(e.target.value)}
            placeholder="comma-separated tags"
            className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      <div className="flex items-center justify-between p-3 bg-white dark:bg-slate-800 border-b border-gray-200 dark:border-slate-700">
        <div className="flex flex-wrap gap-1">
          {(['all', 'keep', 'park', 'discard'] as const).map((value) => (
            <button
              key={value}
              onClick={() => setFilter(value)}
              className={`px-3 py-1 text-sm rounded-md capitalize ${
                filter === value
                  ? 'bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300'
                  : 'text-gray-600 dark:text-slate-400 hover:bg-gray-100 dark:hover:bg-slate-700'
              }`}
            >
              {value}
            </button>
          ))}
        </div>

        <button
          onClick={handleCreateCluster}
          disabled={isClusterDisabled}
               className="px-3 py-1 text-sm bg-purple-100 dark:bg-purple-900/40 text-purple-700 dark:text-purple-300 rounded-md hover:bg-purple-200 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Group Selected ({selectedItems.size})
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {filteredItems.map((item) => (
            <BrainstormCard
              key={item.item_id}
              item={item}
              selected={selectedItems.has(item.item_id)}
              onSelect={() => handleToggleSelect(item.item_id)}
              onPromote={onPromote ? () => handleOpenPromote(item.item_id) : undefined}
            />
          ))}
        </div>

        {filteredItems.length === 0 && (
          <div className="text-center py-12 text-gray-500 dark:text-slate-400">
            <p>No brainstorm items yet</p>
            <p className="text-sm mt-2">Add ideas above and group the ones that belong together.</p>
          </div>
        )}
      </div>

      {promoteOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="w-full max-w-md bg-white dark:bg-slate-800 rounded-xl shadow-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-slate-100 mb-4">Promote to</h3>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1">Target type</label>
                <select
                  value={promoteTargetKind}
                  onChange={(e) => setPromoteTargetKind(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {TARGET_TYPES.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1">Target ID</label>
                <input
                  type="text"
                  value={promoteTargetId}
                  onChange={(e) => setPromoteTargetId(e.target.value)}
                  placeholder="Enter target ID"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {promoteError && (
                <p className="text-sm text-red-600">{promoteError}</p>
              )}
            </div>

            <div className="flex justify-end gap-2 mt-6">
              <button
                type="button"
                onClick={handleClosePromote}
                disabled={promoteLoading}
                className="px-4 py-2 text-sm text-gray-700 dark:text-slate-300 bg-gray-100 dark:bg-slate-700 rounded-lg hover:bg-gray-200 dark:hover:bg-slate-600 disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handlePromoteSubmit}
                disabled={promoteLoading || !promoteTargetId.trim()}
                className="px-4 py-2 text-sm text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {promoteLoading ? 'Promoting...' : 'Confirm'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

interface BrainstormCardProps {
  item: BrainstormItem;
  selected: boolean;
  onSelect: () => void;
  onPromote?: () => void;
}

function BrainstormCard({ item, selected, onSelect, onPromote }: BrainstormCardProps) {
  const statusStyles: Record<BrainstormItemStatus, string> = {
    keep: 'bg-green-100 dark:bg-green-900/40 text-green-800 dark:text-green-300 border-green-200 dark:border-green-800',
    park: 'bg-yellow-100 dark:bg-yellow-900/40 text-yellow-800 dark:text-yellow-300 border-yellow-200 dark:border-yellow-800',
    discard: 'bg-red-100 dark:bg-red-900/40 text-red-800 dark:text-red-300 border-red-200 dark:border-red-800',
  };

  const isPromoted = item.promoted_to != null;

  return (
    <div
      className={`bg-white dark:bg-slate-800 border-2 rounded-lg p-3 transition-all ${
        selected ? 'border-blue-500 ring-2 ring-blue-100' : 'border-gray-200 dark:border-slate-700 hover:border-gray-300 dark:hover:border-slate-600'
      }`}
    >
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-1.5 flex-wrap">
          {item.item_type && (
            <span className={`px-1.5 py-0.5 text-xs rounded border ${CATEGORY_BADGE_STYLES[item.item_type as BrainstormItemType].color}`}>
              {CATEGORY_BADGE_STYLES[item.item_type as BrainstormItemType].label}
            </span>
          )}
          <span className={`px-2 py-0.5 text-xs rounded border ${statusStyles[item.status]}`}>
            {item.status}
          </span>
          {isPromoted && item.promoted_to && (
            <span className="px-2 py-0.5 text-xs rounded border bg-indigo-100 dark:bg-indigo-900/40 text-indigo-800 dark:text-indigo-300 border-indigo-200 dark:border-indigo-800">
              Promoted: {item.promoted_to}
            </span>
          )}
        </div>
        {!isPromoted && onPromote && (
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              onPromote();
            }}
            className="px-2 py-0.5 text-xs font-medium text-blue-700 dark:text-blue-300 bg-blue-50 dark:bg-blue-900/40 rounded hover:bg-blue-100 dark:hover:bg-blue-900/60 transition-colors"
          >
            Promote
          </button>
        )}
      </div>

      <p
        className="text-sm text-gray-700 dark:text-slate-300 mb-3 whitespace-pre-wrap break-words cursor-pointer"
        onClick={onSelect}
      >
        {item.content}
      </p>

      {item.tags.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-2">
          {item.tags.map((tag) => (
            <span key={tag} className="px-1.5 py-0.5 text-xs bg-gray-100 text-gray-600 dark:text-slate-400 rounded">
              #{tag}
            </span>
          ))}
        </div>
      )}

      {item.source_notes && (
        <p className="text-xs text-gray-500 dark:text-slate-400 italic line-clamp-2">{item.source_notes}</p>
      )}
    </div>
  );
}

function parseTags(value: string): string[] {
  return Array.from(
    new Set(
      value
        .split(',')
        .map((tag) => tag.trim())
        .filter(Boolean),
    ),
  );
}
