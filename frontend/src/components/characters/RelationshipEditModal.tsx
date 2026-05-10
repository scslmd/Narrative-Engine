import { useState, useMemo, useEffect } from 'react';
import { X, Trash2, AlertCircle } from 'lucide-react';
import type { CharacterProfile, RelationshipEdge } from '../../types/characters';

interface RelationshipEditModalProps {
  relationship: RelationshipEdge;
  characters: CharacterProfile[];
  onSave: (edgeId: string, data: { relation_kind?: string; summary?: string; tension?: string | null; notes?: string | null; }) => Promise<void>;
  onDelete: (edgeId: string) => Promise<void>;
  isSaving: boolean;
  isDeleting: boolean;
  isOpen: boolean;
  onClose: () => void;
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

export function RelationshipEditModal({
  relationship,
  characters,
  onSave,
  onDelete,
  isSaving,
  isDeleting,
  isOpen,
  onClose,
  isDark = false,
}: RelationshipEditModalProps) {
  const [relationKind, setRelationKind] = useState('');
  const [summary, setSummary] = useState('');
  const [tension, setTension] = useState('');
  const [notes, setNotes] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setRelationKind(relationship.relation_kind);
      setSummary(relationship.summary);
      setTension(relationship.tension || '');
      setNotes(relationship.notes || '');
      setError(null);
      setDeleteConfirm(false);
    }
  }, [isOpen, relationship]);

  const sourceName = useMemo(() => {
    return characters.find((c) => c.character_id === relationship.source_character_id)?.display_name || relationship.source_character_id;
  }, [characters, relationship.source_character_id]);

  const targetName = useMemo(() => {
    return characters.find((c) => c.character_id === relationship.target_character_id)?.display_name || relationship.target_character_id;
  }, [characters, relationship.target_character_id]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!summary.trim()) {
      setError('Summary is required');
      return;
    }

    try {
      await onSave(relationship.edge_id, {
        relation_kind: relationKind,
        summary: summary.trim(),
        tension: tension.trim() || null,
        notes: notes.trim() || null,
      });
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save relationship');
    }
  };

  const handleDelete = async () => {
    if (deleteConfirm) {
      await onDelete(relationship.edge_id);
      onClose();
    } else {
      setDeleteConfirm(true);
    }
  };

  if (!isOpen) return null;

  const bg = isDark ? 'bg-slate-900' : 'bg-white';
  const borderColor = isDark ? 'border-slate-700' : 'border-gray-200';
  const textPrimary = isDark ? 'text-slate-100' : 'text-slate-900';
  const textMuted = isDark ? 'text-slate-400' : 'text-gray-500';
  const inputBg = isDark ? 'bg-slate-800 border-slate-600 text-slate-100' : 'bg-white border-gray-300 text-slate-900';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className={`relative ${bg} rounded-xl border ${borderColor} w-full max-w-lg p-5 space-y-4`}>
        <div className="flex items-center justify-between">
          <h2 className={`text-base font-semibold ${textPrimary}`}>Edit Relationship</h2>
          <button
            type="button"
            onClick={onClose}
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

        <form onSubmit={handleSave} className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className={`block text-xs font-medium mb-1 ${textMuted}`}>From</label>
              <input
                type="text"
                value={sourceName}
                disabled
                className={`w-full rounded-lg border px-2.5 py-1.5 text-sm ${isDark ? 'bg-slate-700 border-slate-600 text-slate-300' : 'bg-gray-50 border-gray-200 text-gray-500'} cursor-not-allowed`}
              />
            </div>
            <div>
              <label className={`block text-xs font-medium mb-1 ${textMuted}`}>To</label>
              <input
                type="text"
                value={targetName}
                disabled
                className={`w-full rounded-lg border px-2.5 py-1.5 text-sm ${isDark ? 'bg-slate-700 border-slate-600 text-slate-300' : 'bg-gray-50 border-gray-200 text-gray-500'} cursor-not-allowed`}
              />
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

          <div className="flex items-center justify-between pt-1">
            <button
              type="button"
              onClick={handleDelete}
              disabled={isDeleting}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg ${deleteConfirm ? (isDark ? 'bg-red-600 text-white' : 'bg-red-100 text-red-700') : (isDark ? 'text-slate-300 hover:bg-slate-700' : 'text-gray-600 hover:bg-gray-100')} disabled:opacity-50 disabled:cursor-not-allowed`}
            >
              <Trash2 className="w-3.5 h-3.5" />
              {isDeleting ? 'Deleting...' : deleteConfirm ? 'Confirm Delete' : 'Delete'}
            </button>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={onClose}
                className={`px-3 py-1.5 text-xs font-medium rounded-lg ${isDark ? 'text-slate-300 hover:bg-slate-700' : 'text-gray-600 hover:bg-gray-100'}`}
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSaving}
                className="px-3 py-1.5 text-xs font-medium rounded-lg bg-cyan-600 text-white hover:bg-cyan-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSaving ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
