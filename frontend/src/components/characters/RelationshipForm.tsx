import { useState, useMemo } from 'react';
import { Plus, X, AlertCircle } from 'lucide-react';
import type { CharacterProfile, RelationshipEdgeCreateRequest } from '../../types/characters';

interface RelationshipFormProps {
  characters: CharacterProfile[];
  onSubmit: (data: RelationshipEdgeCreateRequest) => Promise<void>;
  onCancel: () => void;
  isSubmitting: boolean;
  isDark?: boolean;
}

const RELATION_KINDS = [
  'ALLY',
  'ENEMY',
  'FRIEND',
  'LOVER',
  'MENTOR',
  'FAMILY',
  'RIVAL',
  'MERCENARY',
  'GUARDIAN',
  'SUBORDINATE',
  'SIBLING',
  'PARENT',
  'CHILD',
  'PARTNER',
  'TEACHER',
  'RELATIVE',
  'FOE',
  'COMPETITOR',
  'PROTECTOR',
];

export function RelationshipForm({
  characters,
  onSubmit,
  onCancel,
  isSubmitting,
  isDark = false,
}: RelationshipFormProps) {
  const [sourceId, setSourceId] = useState('');
  const [targetId, setTargetId] = useState('');
  const [relationKind, setRelationKind] = useState('FRIEND');
  const [summary, setSummary] = useState('');
  const [tension, setTension] = useState('');
  const [notes, setNotes] = useState('');
  const [error, setError] = useState<string | null>(null);

  const characterOptions = useMemo(
    () => characters
      .map((c) => ({ value: c.character_id, label: c.display_name }))
      .sort((a, b) => a.label.localeCompare(b.label)),
    [characters],
  );

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!sourceId || !targetId) {
      setError('Both characters must be selected');
      return;
    }
    if (sourceId === targetId) {
      setError('Characters must be different');
      return;
    }
    if (!summary.trim()) {
      setError('Summary is required');
      return;
    }

    try {
      await onSubmit({
        project_id: characters[0]?.project_id || '',
        source_character_id: sourceId,
        target_character_id: targetId,
        relation_kind: relationKind,
        summary: summary.trim(),
        tension: tension.trim() || null,
        notes: notes.trim() || null,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create relationship');
    }
  };

  const bg = isDark ? 'bg-slate-900' : 'bg-white';
  const borderColor = isDark ? 'border-slate-700' : 'border-gray-200';
  const textPrimary = isDark ? 'text-slate-100' : 'text-slate-900';
  const textMuted = isDark ? 'text-slate-400' : 'text-gray-500';
  const inputBg = isDark ? 'bg-slate-800 border-slate-600 text-slate-100' : 'bg-white border-gray-300 text-slate-900';

  return (
    <form onSubmit={handleSubmit} className={`${bg} rounded-xl border ${borderColor} p-4 space-y-3`}>
      <div className="flex items-center justify-between">
        <h3 className={`text-sm font-semibold ${textPrimary}`}>New Relationship</h3>
        <button
          type="button"
          onClick={onCancel}
          className={`p-1 rounded ${isDark ? 'hover:bg-slate-700' : 'hover:bg-gray-100'} ${textMuted}`}
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {error && (
        <div className={`flex items-center gap-1.5 text-xs ${isDark ? 'text-red-400' : 'text-red-600'}`}>
          <AlertCircle className="w-3.5 h-3.5 shrink-0" />
          {error}
        </div>
      )}

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className={`block text-xs font-medium mb-1 ${textMuted}`}>From</label>
          <select
            value={sourceId}
            onChange={(e) => setSourceId(e.target.value)}
            className={`w-full rounded-lg border px-2.5 py-1.5 text-sm ${inputBg}`}
          >
            <option value="">Select character...</option>
            {characterOptions.map((opt) => (
              <option key={opt.value} value={opt.value} disabled={opt.value === targetId}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className={`block text-xs font-medium mb-1 ${textMuted}`}>To</label>
          <select
            value={targetId}
            onChange={(e) => setTargetId(e.target.value)}
            className={`w-full rounded-lg border px-2.5 py-1.5 text-sm ${inputBg}`}
          >
            <option value="">Select character...</option>
            {characterOptions.map((opt) => (
              <option key={opt.value} value={opt.value} disabled={opt.value === sourceId}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div>
        <label className={`block text-xs font-medium mb-1 ${textMuted}`}>Relationship Type</label>
        <select
          value={relationKind}
          onChange={(e) => setRelationKind(e.target.value)}
          className={`w-full rounded-lg border px-2.5 py-1.5 text-sm ${inputBg}`}
        >
          {RELATION_KINDS.map((kind) => (
            <option key={kind} value={kind}>{kind}</option>
          ))}
        </select>
      </div>

      <div>
        <label className={`block text-xs font-medium mb-1 ${textMuted}`}>
          Summary <span className="text-red-500">*</span>
        </label>
        <textarea
          value={summary}
          onChange={(e) => setSummary(e.target.value)}
          rows={2}
          placeholder="Describe the relationship..."
          className={`w-full rounded-lg border px-2.5 py-1.5 text-sm resize-none ${inputBg}`}
        />
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className={`block text-xs font-medium mb-1 ${textMuted}`}>Tension</label>
          <input
            type="text"
            value={tension}
            onChange={(e) => setTension(e.target.value)}
            placeholder="Conflict or friction..."
            className={`w-full rounded-lg border px-2.5 py-1.5 text-sm ${inputBg}`}
          />
        </div>

        <div>
          <label className={`block text-xs font-medium mb-1 ${textMuted}`}>Notes</label>
          <input
            type="text"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Additional context..."
            className={`w-full rounded-lg border px-2.5 py-1.5 text-sm ${inputBg}`}
          />
        </div>
      </div>

      <div className="flex items-center justify-end gap-2 pt-1">
        <button
          type="button"
          onClick={onCancel}
          className={`px-3 py-1.5 text-xs font-medium rounded-lg ${isDark ? 'text-slate-300 hover:bg-slate-700' : 'text-gray-600 hover:bg-gray-100'}`}
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={isSubmitting}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-cyan-600 text-white hover:bg-cyan-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Plus className="w-3.5 h-3.5" />
          {isSubmitting ? 'Creating...' : 'Create Relationship'}
        </button>
      </div>
    </form>
  );
}
