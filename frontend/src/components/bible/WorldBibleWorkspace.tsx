import { useState } from 'react';
import type { BibleEntry, BibleEntryType } from '../../types/bible';

interface WorldBibleWorkspaceProps {
  projectId: string;
  entries?: BibleEntry[];
  onEntryAdd?: (entry: BibleEntry) => void;
  onEntryUpdate?: (entry: BibleEntry) => void;
  onEntryDelete?: (entryId: string) => void;
}

export function WorldBibleWorkspace({
  entries = [],
  onEntryAdd,
  onEntryUpdate,
  onEntryDelete,
}: WorldBibleWorkspaceProps) {
  const [activeTab, setActiveTab] = useState<BibleEntryType | 'all'>('all');
  const [editingEntry, setEditingEntry] = useState<BibleEntry | null>(null);
  const [newEntryTitle, setNewEntryTitle] = useState('');
  const [newEntryType, setNewEntryType] = useState<BibleEntryType>('concept');

  const filteredEntries = activeTab === 'all'
    ? entries
    : entries.filter(e => e.type === activeTab);

  const handleAddEntry = () => {
    if (!newEntryTitle.trim()) return;

    const newEntry: BibleEntry = {
      id: crypto.randomUUID(),
      type: newEntryType,
      title: newEntryTitle.trim(),
      summary: '',
      details: '',
    };

    onEntryAdd?.(newEntry);
    setNewEntryTitle('');
    setEditingEntry(newEntry);
  };

  const handleSaveEntry = () => {
    if (editingEntry) {
      onEntryUpdate?.(editingEntry);
      setEditingEntry(null);
    }
  };

  const handleDeleteEntry = (entryId: string) => {
    onEntryDelete?.(entryId);
    setEditingEntry(null);
  };

  const entryTypeLabels: Record<BibleEntryType, string> = {
    character: 'Characters',
    location: 'Locations',
    rule: 'Rules',
    object: 'Objects',
    concept: 'Concepts',
  };

  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* Header */}
      <div className="p-4 bg-white border-b border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900">World Bible</h2>
          <span className="text-sm text-gray-500">
            {entries.length} entries
          </span>
        </div>

        {/* Add new entry */}
        <div className="flex gap-2">
          <input
            type="text"
            value={newEntryTitle}
            onChange={(e) => setNewEntryTitle(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleAddEntry()}
            placeholder="Add new entry..."
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <select
            value={newEntryType}
            onChange={(e) => setNewEntryType(e.target.value as BibleEntryType)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="concept">Concept</option>
            <option value="character">Character</option>
            <option value="location">Location</option>
            <option value="rule">Rule</option>
            <option value="object">Object</option>
          </select>
          <button
            onClick={handleAddEntry}
            disabled={!newEntryTitle.trim()}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Add
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-200 bg-white">
        {(['all', 'character', 'location', 'rule', 'object', 'concept'] as const).map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 text-sm font-medium capitalize ${
              activeTab === tab
                ? 'text-blue-600 border-b-2 border-blue-600'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            {tab === 'all' ? 'All' : entryTypeLabels[tab]}
            <span className="ml-1 text-gray-400">
              ({tab === 'all' ? entries.length : entries.filter(e => e.type === tab).length})
            </span>
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        {editingEntry ? (
          <BibleEntryEditor
            entry={editingEntry}
            onSave={handleSaveEntry}
            onDelete={() => handleDeleteEntry(editingEntry.id)}
            onCancel={() => setEditingEntry(null)}
            onUpdate={(updated) => setEditingEntry(updated)}
          />
        ) : (
          <div className="flex-1 overflow-y-auto p-4">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {filteredEntries.map(entry => (
                <BibleEntryCard
                  key={entry.id}
                  entry={entry}
                  onClick={() => setEditingEntry(entry)}
                />
              ))}
            </div>

            {filteredEntries.length === 0 && (
              <div className="text-center py-12 text-gray-500">
                <p>No entries in this category</p>
                <p className="text-sm mt-2">Add entries using the form above</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

interface BibleEntryCardProps {
  entry: BibleEntry;
  onClick: () => void;
}

function BibleEntryCard({ entry, onClick }: BibleEntryCardProps) {
  const typeColors: Record<BibleEntryType, string> = {
    character: 'bg-purple-100 text-purple-800',
    location: 'bg-green-100 text-green-800',
    rule: 'bg-red-100 text-red-800',
    object: 'bg-yellow-100 text-yellow-800',
    concept: 'bg-blue-100 text-blue-800',
  };

  return (
    <div
      className="bg-white border border-gray-200 rounded-lg p-4 cursor-pointer hover:border-blue-400 hover:shadow-md transition-all"
      onClick={onClick}
    >
      <div className="flex items-start justify-between mb-2">
        <span className={`px-2 py-0.5 text-xs rounded ${typeColors[entry.type]}`}>
          {entry.type}
        </span>
      </div>
      <h3 className="font-medium text-gray-900 mb-1">{entry.title}</h3>
      <p className="text-sm text-gray-600 line-clamp-2">{entry.summary || 'No summary yet'}</p>
    </div>
  );
}

interface BibleEntryEditorProps {
  entry: BibleEntry;
  onSave: () => void;
  onDelete: () => void;
  onCancel: () => void;
  onUpdate: (entry: BibleEntry) => void;
}

function BibleEntryEditor({ entry, onSave, onDelete, onCancel, onUpdate }: BibleEntryEditorProps) {
  const handleUpdate = (field: keyof BibleEntry, value: string) => {
    onUpdate({ ...entry, [field]: value });
  };

  return (
    <div className="flex-1 overflow-y-auto p-6 bg-white">
      <div className="max-w-3xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <span className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded capitalize">
              {entry.type}
            </span>
          </div>
          <div className="flex gap-2">
            <button onClick={onSave} className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
              Save & Close
            </button>
            <button onClick={onDelete} className="px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200">
              Delete
            </button>
            <button onClick={onCancel} className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300">
              Cancel
            </button>
          </div>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Title</label>
            <input
              type="text"
              value={entry.title}
              onChange={(e) => handleUpdate('title', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-lg"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Summary</label>
            <textarea
              value={entry.summary}
              onChange={(e) => handleUpdate('summary', e.target.value)}
              placeholder="A brief summary of this entry..."
              className="w-full h-24 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Details</label>
            <textarea
              value={entry.details || ''}
              onChange={(e) => handleUpdate('details', e.target.value)}
              placeholder="Detailed description, notes, and references..."
              className="w-full h-96 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y"
            />
          </div>
        </div>
      </div>
    </div>
  );
}
