import { useState, useCallback } from 'react';
import type { BrainstormItem, BrainstormItemCreateRequest } from '../../types/brainstorm';

interface BrainstormWorkspaceProps {
  projectId: string;
  items?: BrainstormItem[];
  onItemAdd?: (item: BrainstormItem) => void;
  onItemUpdate?: (item: BrainstormItem) => void;
  onItemDelete?: (itemId: string) => void;
  onClusterCreate?: (itemIds: string[]) => void;
  onItemPromote?: (itemId: string, targetType: string) => void;
}

export function BrainstormWorkspace({
  items = [],
  onItemAdd,
  onItemDelete,
  onClusterCreate,
  onItemPromote,
}: BrainstormWorkspaceProps) {
  const [newItemContent, setNewItemContent] = useState('');
  const [newItemType, setNewItemType] = useState<BrainstormItemCreateRequest['item_type']>('IDEA');
  const [selectedItems, setSelectedItems] = useState<Set<string>>(new Set());
  const [filter, setFilter] = useState<'all' | 'ideas' | 'characters' | 'settings' | 'plot' | 'themes'>('all');

  const filteredItems = items.filter(item => {
    if (filter === 'all') return true;
    if (filter === 'ideas') return item.item_type === 'IDEA';
    if (filter === 'characters') return item.item_type === 'CHARACTER';
    if (filter === 'settings') return item.item_type === 'SETTING';
    if (filter === 'plot') return item.item_type === 'PLOT_POINT';
    if (filter === 'themes') return item.item_type === 'THEME';
    return true;
  });

  const handleAddItem = useCallback(() => {
    if (!newItemContent.trim()) return;

    const newItem: BrainstormItemCreateRequest = {
      content: newItemContent.trim(),
      item_type: newItemType,
    };

    onItemAdd?.(newItem as BrainstormItem);
    setNewItemContent('');
  }, [newItemContent, newItemType, onItemAdd]);

  const handleToggleSelect = useCallback((itemId: string) => {
    setSelectedItems(prev => {
      const next = new Set(prev);
      if (next.has(itemId)) {
        next.delete(itemId);
      } else {
        next.add(itemId);
      }
      return next;
    });
  }, []);

  const handleCreateCluster = useCallback(() => {
    if (selectedItems.size > 1) {
      onClusterCreate?.(Array.from(selectedItems));
      setSelectedItems(new Set());
    }
  }, [selectedItems, onClusterCreate]);

  const handlePromote = useCallback((itemId: string, targetType: string) => {
    onItemPromote?.(itemId, targetType);
  }, [onItemPromote]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleAddItem();
    }
  }, [handleAddItem]);

  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* Header */}
      <div className="p-4 bg-white border-b border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900">Brainstorm</h2>
          <span className="text-sm text-gray-500">
            {items.length} items • {selectedItems.size} selected
          </span>
        </div>

        {/* Add item form */}
        <div className="flex gap-2">
          <input
            type="text"
            value={newItemContent}
            onChange={(e) => setNewItemContent(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Add a new idea..."
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <select
            value={newItemType}
            onChange={(e) => setNewItemType(e.target.value as BrainstormItemCreateRequest['item_type'])}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="IDEA">Idea</option>
            <option value="CHARACTER">Character</option>
            <option value="SETTING">Setting</option>
            <option value="PLOT_POINT">Plot Point</option>
            <option value="THEME">Theme</option>
            <option value="QUESTION">Question</option>
          </select>
          <button
            onClick={handleAddItem}
            disabled={!newItemContent.trim()}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Add
          </button>
        </div>
      </div>

      {/* Filters and actions */}
      <div className="flex items-center justify-between p-3 bg-white border-b border-gray-200">
        <div className="flex gap-1">
          {(['all', 'ideas', 'characters', 'settings', 'plot', 'themes'] as const).map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1 text-sm rounded-md capitalize ${
                filter === f
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              {f}
            </button>
          ))}
        </div>

        {selectedItems.size > 1 && (
          <button
            onClick={handleCreateCluster}
            className="px-3 py-1 text-sm bg-purple-100 text-purple-700 rounded-md hover:bg-purple-200"
          >
            Cluster Selected ({selectedItems.size})
          </button>
        )}
      </div>

      {/* Items grid */}
      <div className="flex-1 overflow-y-auto p-4">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {filteredItems.map(item => (
            <BrainstormCard
              key={item.item_id}
              item={item}
              selected={selectedItems.has(item.item_id)}
              onSelect={() => handleToggleSelect(item.item_id)}
              onPromote={(targetType) => handlePromote(item.item_id, targetType)}
              onDelete={() => onItemDelete?.(item.item_id)}
            />
          ))}
        </div>

        {filteredItems.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            <p>No brainstorm items yet</p>
            <p className="text-sm mt-2">Add ideas, characters, settings, and more above</p>
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
  onPromote: (targetType: string) => void;
  onDelete: () => void;
}

function BrainstormCard({ item, selected, onSelect, onPromote, onDelete }: BrainstormCardProps) {
  const typeColors = {
    IDEA: 'bg-blue-100 text-blue-800',
    CHARACTER: 'bg-purple-100 text-purple-800',
    SETTING: 'bg-green-100 text-green-800',
    PLOT_POINT: 'bg-orange-100 text-orange-800',
    THEME: 'bg-yellow-100 text-yellow-800',
    QUESTION: 'bg-gray-100 text-gray-800',
  };

  const stateColors = {
    KEEP: 'border-green-400',
    DISCARD: 'border-red-400',
    PARK: 'border-yellow-400',
  };

  return (
    <div
      className={`bg-white border-2 rounded-lg p-3 cursor-pointer transition-all ${
        selected ? 'border-blue-500 ring-2 ring-blue-100' : `border-gray-200 ${stateColors[item.state]}`}
      `}
      onClick={onSelect}
    >
      <div className="flex items-start justify-between mb-2">
        <span className={`px-2 py-0.5 text-xs rounded ${typeColors[item.item_type]}`}>
          {item.item_type}
        </span>
        {item.promoted_to && (
          <span className="text-xs text-green-600">✓ Promoted</span>
        )}
      </div>

      <p className="text-sm text-gray-700 mb-2 line-clamp-3">{item.content}</p>

      {item.tags.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-2">
          {item.tags.map(tag => (
            <span key={tag} className="px-1.5 py-0.5 text-xs bg-gray-100 text-gray-600 rounded">
              #{tag}
            </span>
          ))}
        </div>
      )}

      <div className="flex items-center justify-between pt-2 border-t border-gray-100">
        <div className="flex gap-1">
          <button
            onClick={(e) => { e.stopPropagation(); onPromote('character'); }}
            className="px-2 py-1 text-xs bg-purple-50 text-purple-700 rounded hover:bg-purple-100"
            title="Promote to Character"
          >
            → Character
          </button>
          <button
            onClick={(e) => { e.stopPropagation(); onPromote('setting'); }}
            className="px-2 py-1 text-xs bg-green-50 text-green-700 rounded hover:bg-green-100"
            title="Promote to Setting"
          >
            → Setting
          </button>
        </div>
        <button
          onClick={(e) => { e.stopPropagation(); onDelete(); }}
          className="text-gray-400 hover:text-red-600"
          title="Delete"
        >
          ×
        </button>
      </div>
    </div>
  );
}
