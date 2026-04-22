import { useState } from 'react';
import { useNotesStore, WorkspaceNote } from '../stores/notesStore';
import { useThemeStore } from '../stores/themeStore';
import { Plus, Pencil, Trash2, Clock, StickyNote } from 'lucide-react';

interface Props {
  projectId: string;
}

export function NotesPanel({ projectId }: Props): React.ReactElement {
  const { addNote, updateNote, deleteNote, getNotesForProject } = useNotesStore();
  const projectNotes = getNotesForProject(projectId);
  const [newNoteContent, setNewNoteContent] = useState('');
  const { mode } = useThemeStore();
  const isDark = ['dark', 'midnight', 'forest', 'ocean'].includes(mode);

  const handleAddNote = (): void => {
    if (newNoteContent.trim()) {
      addNote(projectId, newNoteContent.trim());
      setNewNoteContent('');
    }
  };

  const formatDate = (timestamp: number): string => {
    return new Date(timestamp).toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className={`rounded-xl border ${isDark ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'} shadow-card flex flex-col h-full`}>
      <div className={`flex items-center gap-2 px-4 py-3 border-b ${isDark ? 'border-slate-800' : 'border-slate-200'}`}>
        <StickyNote className={`w-4 h-4 ${isDark ? 'text-amber-400' : 'text-amber-500'}`} />
        <h3 className={`text-sm font-semibold ${isDark ? 'text-slate-200' : 'text-slate-800'}`}>Notes</h3>
        <span className={`ml-auto text-xs ${isDark ? 'text-slate-600' : 'text-slate-400'}`}>
          {projectNotes.length}
        </span>
      </div>

      <div className={`mx-3 mt-3 rounded-lg border ${isDark ? 'bg-slate-800/50 border-slate-700/60' : 'bg-slate-50 border-slate-200'}`}>
        <textarea
          value={newNoteContent}
          onChange={(e) => setNewNoteContent(e.target.value)}
          placeholder="Add a note..."
          rows={2}
          className={`w-full bg-transparent rounded-lg border-none text-xs px-3 py-2 resize-none focus:outline-none focus:ring-1 focus:ring-amber-500/40 ${isDark ? 'text-slate-200 placeholder-slate-600' : 'text-slate-800 placeholder-slate-400'}`}
        />
        <div className={`flex items-center justify-between px-3 py-1.5 border-t ${isDark ? 'border-slate-700/60' : 'border-slate-200'}`}>
          <span className={`text-xs ${isDark ? 'text-slate-600' : 'text-slate-400'}`}>
            {newNoteContent.length > 0 && `${newNoteContent.length} chars`}
          </span>
          <button
            onClick={handleAddNote}
            disabled={!newNoteContent.trim()}
            className="flex items-center gap-1 px-2.5 py-1 bg-gradient-to-r from-amber-500 to-amber-600 text-white text-xs font-medium rounded-md hover:from-amber-600 hover:to-amber-700 transition-all disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <Plus className="w-3 h-3" />
            Add
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-3 py-3 space-y-2">
        {projectNotes.length === 0 ? (
          <div className={`flex flex-col items-center justify-center py-6 text-center ${isDark ? 'text-slate-600' : 'text-slate-400'}`}>
            <StickyNote className="w-8 h-8 mb-2 opacity-50" />
            <p className="text-xs">No notes yet</p>
          </div>
        ) : (
          projectNotes.map((note) => <NoteItem key={note.id} note={note} onUpdate={updateNote} onDelete={deleteNote} formatDate={formatDate} />)
        )}
      </div>
    </div>
  );
}

interface NoteItemProps {
  note: WorkspaceNote;
  onUpdate: (id: string, content: string) => void;
  onDelete: (id: string) => void;
  formatDate: (timestamp: number) => string;
}

function NoteItem({ note, onUpdate, onDelete, formatDate }: NoteItemProps): React.ReactElement {
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState(note.content);
  const { mode } = useThemeStore();
  const isDark = ['dark', 'midnight', 'forest', 'ocean'].includes(mode);

  const handleSave = (): void => {
    if (editContent.trim()) {
      onUpdate(note.id, editContent.trim());
      setIsEditing(false);
    }
  };

  const handleCancel = (): void => {
    setEditContent(note.content);
    setIsEditing(false);
  };

  return (
    <div className={`rounded-lg border ${isDark ? 'bg-slate-800/40 border-slate-700/50' : 'bg-slate-50 border-slate-200'} transition-all`}>
      {isEditing ? (
        <div className="p-2.5 space-y-2">
          <textarea
            value={editContent}
            onChange={(e) => setEditContent(e.target.value)}
            rows={3}
            className={`w-full rounded-md border text-xs px-2 py-1.5 resize-none focus:outline-none focus:ring-1 focus:ring-amber-500/40 ${isDark ? 'bg-slate-800 border-slate-600 text-slate-200' : 'bg-white border-slate-300 text-slate-800'}`}
          />
          <div className="flex gap-1.5">
            <button
              onClick={handleSave}
              className="flex-1 px-2 py-1 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-medium rounded transition-colors"
            >
              Save
            </button>
            <button
              onClick={handleCancel}
              className={`flex-1 px-2 py-1 text-xs font-medium rounded transition-colors ${isDark ? 'bg-slate-700 text-slate-300 hover:bg-slate-600' : 'bg-slate-200 text-slate-600 hover:bg-slate-300'}`}
            >
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <div className="p-2.5 space-y-1.5">
          <p className={`text-xs whitespace-pre-wrap leading-relaxed ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>
            {note.content.length > 120 ? note.content.slice(0, 120) + '...' : note.content}
          </p>
          <div className="flex items-center justify-between">
            <span className={`flex items-center gap-1 text-xs ${isDark ? 'text-slate-600' : 'text-slate-400'}`}>
              <Clock className="w-3 h-3" />
              {formatDate(note.updatedAt)}
            </span>
            <div className="flex gap-1">
              <button
                onClick={() => setIsEditing(true)}
                className={`p-1 rounded transition-colors ${isDark ? 'text-slate-500 hover:text-amber-400 hover:bg-slate-700/50' : 'text-slate-400 hover:text-amber-600 hover:bg-amber-50'}`}
              >
                <Pencil className="w-3 h-3" />
              </button>
              <button
                onClick={() => onDelete(note.id)}
                className={`p-1 rounded transition-colors ${isDark ? 'text-slate-500 hover:text-red-400 hover:bg-slate-700/50' : 'text-slate-400 hover:text-red-600 hover:bg-red-50'}`}
              >
                <Trash2 className="w-3 h-3" />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
