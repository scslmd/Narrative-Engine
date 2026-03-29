import { useState } from 'react';
import type { WorldBibleEntry, WorldBibleEntryCreateRequest, WorldBibleEntryType } from '../../types/bible';

interface WorldBibleWorkspaceProps {
  projectId: string;
  entries?: WorldBibleEntry[];
  onEntryAdd?: (entry: WorldBibleEntryCreateRequest) => void;
  onEntryUpdate?: (entry: WorldBibleEntry, originalTitle: string) => void;
}

export function WorldBibleWorkspace({
  projectId,
  entries = [],
  onEntryAdd,
  onEntryUpdate,
}: WorldBibleWorkspaceProps) {
  const [activeTab, setActiveTab] = useState<WorldBibleEntryType | 'all'>('all');
  const [editingEntry, setEditingEntry] = useState<WorldBibleEntry | null>(null);
  const [editingOriginalTitle, setEditingOriginalTitle] = useState('');
  const [newEntryTitle, setNewEntryTitle] = useState('');
  const [newEntrySummary, setNewEntrySummary] = useState('');
  const [newEntryType, setNewEntryType] = useState<WorldBibleEntryType>('concept');

  const handleAddEntry = () => {
    if (!newEntryTitle.trim() || !newEntrySummary.trim() || !onEntryAdd) return;

    onEntryAdd({
      project_id: projectId,
      entry_type: newEntryType,
      title: newEntryTitle.trim(),
      summary: newEntrySummary.trim(),
      canonical_facts: [],
      related_character_ids: [],
      source_artifacts: [],
      visibility_scope: 'project',
      continuity_warnings: [],
      writer_notes: null,
    });

    setNewEntryTitle('');
    setNewEntrySummary('');
  };

  const handleSaveEntry = () => {
    if (!editingEntry || !onEntryUpdate || !editingEntry.title.trim() || !editingEntry.summary.trim()) return;
    onEntryUpdate(editingEntry, editingOriginalTitle);
    setEditingEntry(null);
    setEditingOriginalTitle('');
  };

  const filteredEntries =
    activeTab === 'all' ? entries : entries.filter((e) => e.entry_type === activeTab);

  const entryTypeLabels: Record<WorldBibleEntryType, string> = {
    location: 'Locations',
    organization: 'Organizations',
    artifact: 'Artifacts',
    event: 'Events',
    concept: 'Concepts',
    creature: 'Creatures',
    magic_system: 'Magic Systems',
    technology: 'Technology',
    culture: 'Cultures',
    history: 'History',
  };

  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* Header */}
      <div className="p-4 bg-white border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">World Bible</h2>
            <p className="text-sm text-gray-500 mt-1">
              Track locations, characters, concepts, and world details
            </p>
          </div>
        </div>

        {/* Add Entry Form */}
        <div className="flex gap-2 mt-4">
          <input
            type="text"
            value={newEntryTitle}
            onChange={(e) => setNewEntryTitle(e.target.value)}
            placeholder="Enter entry title"
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <input
            type="text"
            value={newEntrySummary}
            onChange={(e) => setNewEntrySummary(e.target.value)}
            placeholder="Brief summary"
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <select
            value={newEntryType}
            onChange={(e) => setNewEntryType(e.target.value as WorldBibleEntryType)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="concept">Concept</option>
            <option value="location">Location</option>
            <option value="organization">Organization</option>
            <option value="artifact">Artifact</option>
            <option value="event">Event</option>
            <option value="creature">Creature</option>
            <option value="magic_system">Magic System</option>
            <option value="technology">Technology</option>
            <option value="culture">Culture</option>
            <option value="history">History</option>
          </select>
          <button
            onClick={handleAddEntry}
            disabled={!newEntryTitle.trim() || !newEntrySummary.trim()}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Add
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-200 bg-white">
        {(['all', 'location', 'organization', 'artifact', 'event', 'concept', 'creature', 'magic_system', 'technology', 'culture', 'history'] as const).map(
          (tab) => (
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
                ({tab === 'all' ? entries.length : entries.filter((e) => e.entry_type === tab).length})
              </span>
            </button>
          ),
        )}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        {editingEntry ? (
          <WorldBibleEntryEditor
            entry={editingEntry}
            onSave={handleSaveEntry}
            onCancel={() => {
              setEditingEntry(null);
              setEditingOriginalTitle('');
            }}
            onUpdate={(updated) => setEditingEntry(updated)}
          />
        ) : (
          <div className="flex-1 overflow-y-auto p-4">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {filteredEntries.map((entry) => (
                <WorldBibleEntryCard
                  key={entry.entry_id}
                  entry={entry}
                  onClick={() => {
                    setEditingEntry(entry);
                    setEditingOriginalTitle(entry.title);
                  }}
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

interface WorldBibleEntryCardProps {
  entry: WorldBibleEntry;
  onClick: () => void;
}

function WorldBibleEntryCard({ entry, onClick }: WorldBibleEntryCardProps) {
  const typeColors: Record<WorldBibleEntryType, string> = {
    location: 'bg-green-100 text-green-800',
    organization: 'bg-purple-100 text-purple-800',
    artifact: 'bg-yellow-100 text-yellow-800',
    event: 'bg-red-100 text-red-800',
    concept: 'bg-blue-100 text-blue-800',
    creature: 'bg-orange-100 text-orange-800',
    magic_system: 'bg-indigo-100 text-indigo-800',
    technology: 'bg-cyan-100 text-cyan-800',
    culture: 'bg-pink-100 text-pink-800',
    history: 'bg-gray-100 text-gray-800',
  };

  return (
    <div
      className="bg-white border border-gray-200 rounded-lg p-4 cursor-pointer hover:border-blue-400 hover:shadow-md transition-all"
      onClick={onClick}
    >
      <div className="flex items-start justify-between mb-2">
        <span className={`px-2 py-0.5 text-xs rounded ${typeColors[entry.entry_type]}`}>
          {entry.entry_type.replace('_', ' ')}
        </span>
      </div>
      <h3 className="font-medium text-gray-900 mb-1">{entry.title}</h3>
      <p className="text-sm text-gray-600 line-clamp-2">{entry.summary || 'No summary yet'}</p>
    </div>
  );
}

interface WorldBibleEntryEditorProps {
  entry: WorldBibleEntry;
  onSave: () => void;
  onCancel: () => void;
  onUpdate: (entry: WorldBibleEntry) => void;
}

function WorldBibleEntryEditor({ entry, onSave, onCancel, onUpdate }: WorldBibleEntryEditorProps) {
  const handleUpdate = (field: keyof WorldBibleEntry, value: string | string[] | null) => {
    onUpdate({ ...entry, [field]: value });
  };

  const handleArrayChange = (
    field: keyof WorldBibleEntry,
    index: number,
    value: string,
  ) => {
    const current = (entry[field] as string[]) || [];
    const updated = [...current];
    updated[index] = value;
    handleUpdate(field, updated);
  };

  const handleAddArrayItem = (field: keyof WorldBibleEntry) => {
    const current = (entry[field] as string[]) || [];
    handleUpdate(field, [...current, '']);
  };

  const handleRemoveArrayItem = (field: keyof WorldBibleEntry, index: number) => {
    const current = (entry[field] as string[]) || [];
    handleUpdate(field, current.filter((_, i) => i !== index));
  };

  return (
    <div className="flex-1 overflow-y-auto p-6 bg-white">
      <div className="max-w-3xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <span className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded capitalize">
              {entry.entry_type.replace('_', ' ')}
            </span>
          </div>
          <div className="flex gap-2">
            <button
              onClick={onSave}
              disabled={!entry.title.trim() || !entry.summary.trim()}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Save & Close
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
            <label className="block text-sm font-medium text-gray-700 mb-1">Canonical Facts</label>
            <div className="space-y-2">
              {entry.canonical_facts.map((fact, index) => (
                <div key={index} className="flex gap-2">
                  <input
                    type="text"
                    value={fact}
                    onChange={(e) => handleArrayChange('canonical_facts', index, e.target.value)}
                    placeholder="Canonical fact"
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <button
                    onClick={() => handleRemoveArrayItem('canonical_facts', index)}
                    className="px-3 py-2 text-red-600 hover:bg-red-50 rounded-lg"
                  >
                    Remove
                  </button>
                </div>
              ))}
              <button
                onClick={() => handleAddArrayItem('canonical_facts')}
                className="px-3 py-2 text-blue-600 hover:bg-blue-50 rounded-lg text-sm"
              >
                + Add Fact
              </button>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Continuity Warnings</label>
            <div className="space-y-2">
              {entry.continuity_warnings.map((warning, index) => (
                <div key={index} className="flex gap-2">
                  <input
                    type="text"
                    value={warning}
                    onChange={(e) => handleArrayChange('continuity_warnings', index, e.target.value)}
                    placeholder="Continuity warning"
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <button
                    onClick={() => handleRemoveArrayItem('continuity_warnings', index)}
                    className="px-3 py-2 text-red-600 hover:bg-red-50 rounded-lg"
                  >
                    Remove
                  </button>
                </div>
              ))}
              <button
                onClick={() => handleAddArrayItem('continuity_warnings')}
                className="px-3 py-2 text-blue-600 hover:bg-blue-50 rounded-lg text-sm"
              >
                + Add Warning
              </button>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Writer Notes</label>
            <textarea
              value={entry.writer_notes || ''}
              onChange={(e) => handleUpdate('writer_notes', e.target.value)}
              placeholder="Private notes about this entry..."
              className="w-full h-32 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y"
            />
          </div>
        </div>
      </div>
    </div>
  );
}
