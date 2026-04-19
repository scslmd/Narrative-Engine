import { useState, type KeyboardEvent } from 'react';
import type { BrainstormItem, BrainstormItemCreateRequest, BrainstormItemStatus } from '../../types/brainstorm';
import type { BrainstormItemType } from '../../types/braindump';

interface BrainstormWorkspaceProps {
  projectId: string;
  items?: BrainstormItem[];
  onItemAdd?: (item: BrainstormItemCreateRequest) => void;
  onClusterCreate?: (itemIds: string[]) => void;
}

const STATUS_OPTIONS: Array<{ value: BrainstormItemStatus; label: string }> = [
  { value: 'keep', label: 'Keep' },
  { value: 'park', label: 'Park' },
  { value: 'discard', label: 'Discard' },
];

const CATEGORY_BADGE_STYLES: Record<BrainstormItemType, { color: string; label: string }> = {
  character: { color: 'bg-blue-100 text-blue-800 border-blue-200', label: 'Character' },
  location: { color: 'bg-green-100 text-green-800 border-green-200', label: 'Location' },
  plot_point: { color: 'bg-amber-100 text-amber-800 border-amber-200', label: 'Plot Point' },
  theme: { color: 'bg-purple-100 text-purple-800 border-purple-200', label: 'Theme' },
  conflict: { color: 'bg-red-100 text-red-800 border-red-200', label: 'Conflict' },
  world_building: { color: 'bg-teal-100 text-teal-800 border-teal-200', label: 'World' },
  dialogue: { color: 'bg-pink-100 text-pink-800 border-pink-200', label: 'Dialogue' },
  relationship: { color: 'bg-orange-100 text-orange-800 border-orange-200', label: 'Relationship' },
  object: { color: 'bg-cyan-100 text-cyan-800 border-cyan-200', label: 'Object' },
  rule: { color: 'bg-indigo-100 text-indigo-800 border-indigo-200', label: 'Rule' },
};

export function BrainstormWorkspace({
  projectId,
  items = [],
  onItemAdd,
  onClusterCreate,
}: BrainstormWorkspaceProps) {
  const [newItemContent, setNewItemContent] = useState('');
  const [newItemStatus, setNewItemStatus] = useState<BrainstormItemStatus>('keep');
  const [newItemTags, setNewItemTags] = useState('');
  const [selectedItems, setSelectedItems] = useState<Set<string>>(new Set());
  const [filter, setFilter] = useState<'all' | BrainstormItemStatus>('all');

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

  const handleKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleAddItem();
    }
  };

  const isAddDisabled = !newItemContent.trim() || !onItemAdd;
  const isClusterDisabled = selectedItems.size < 2 || !onClusterCreate;

  return (
    <div className="flex flex-col h-full bg-gray-50">
      <div className="p-4 bg-white border-b border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Brainstorm</h2>
            <p className="text-sm text-gray-500 mt-1">
              Capture raw ideas, sort them by status, and cluster related notes.
            </p>
          </div>
          <span className="text-sm text-gray-500">
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
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <select
            value={newItemStatus}
            onChange={(e) => setNewItemStatus(e.target.value as BrainstormItemStatus)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
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
          <label className="block text-xs font-medium text-gray-600 mb-1">Tags</label>
          <input
            type="text"
            value={newItemTags}
            onChange={(e) => setNewItemTags(e.target.value)}
            placeholder="comma-separated tags"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      <div className="flex items-center justify-between p-3 bg-white border-b border-gray-200">
        <div className="flex flex-wrap gap-1">
          {(['all', 'keep', 'park', 'discard'] as const).map((value) => (
            <button
              key={value}
              onClick={() => setFilter(value)}
              className={`px-3 py-1 text-sm rounded-md capitalize ${
                filter === value
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              {value}
            </button>
          ))}
        </div>

        <button
          onClick={handleCreateCluster}
          disabled={isClusterDisabled}
          className="px-3 py-1 text-sm bg-purple-100 text-purple-700 rounded-md hover:bg-purple-200 disabled:opacity-50 disabled:cursor-not-allowed"
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
            />
          ))}
        </div>

        {filteredItems.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            <p>No brainstorm items yet</p>
            <p className="text-sm mt-2">Add ideas above and group the ones that belong together.</p>
          </div>
        )}
      </div>
    </div>
  );
}

interface BrainstormCardProps {
  item: BrainstormItem;
  selected: boolean;
  onSelect: () => void;
}

function BrainstormCard({ item, selected, onSelect }: BrainstormCardProps) {
  const statusStyles: Record<BrainstormItemStatus, string> = {
    keep: 'bg-green-100 text-green-800 border-green-200',
    park: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    discard: 'bg-red-100 text-red-800 border-red-200',
  };

  return (
    <button
      type="button"
      onClick={onSelect}
      className={`text-left bg-white border-2 rounded-lg p-3 transition-all ${
        selected ? 'border-blue-500 ring-2 ring-blue-100' : 'border-gray-200 hover:border-gray-300'
      }`}
    >
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-1.5">
          {item.item_type && (
            <span className={`px-1.5 py-0.5 text-xs rounded border ${CATEGORY_BADGE_STYLES[item.item_type as BrainstormItemType].color}`}>
              {CATEGORY_BADGE_STYLES[item.item_type as BrainstormItemType].label}
            </span>
          )}
          <span className={`px-2 py-0.5 text-xs rounded border ${statusStyles[item.status]}`}>
            {item.status}
          </span>
        </div>
      </div>

      <p className="text-sm text-gray-700 mb-3 whitespace-pre-wrap break-words">
        {item.content}
      </p>

      {item.tags.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-2">
          {item.tags.map((tag) => (
            <span key={tag} className="px-1.5 py-0.5 text-xs bg-gray-100 text-gray-600 rounded">
              #{tag}
            </span>
          ))}
        </div>
      )}

      {item.source_notes && (
        <p className="text-xs text-gray-500 italic line-clamp-2">{item.source_notes}</p>
      )}
    </button>
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
