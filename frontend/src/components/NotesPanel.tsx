import { useState } from 'react';
import { useNotesStore, WorkspaceNote } from '../stores/notesStore';
import { useThemeStore } from '../stores/themeStore';
import { Plus, Pencil, Trash2, Clock, StickyNote } from 'lucide-react';

interface Props {
  projectId: string;
}

function formatDate(timestamp: number): string {
  return new Date(timestamp).toLocaleDateString(undefined, {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  });
}

export function NotesPanel({ projectId }: Props): React.ReactElement {
  const { addNote, updateNote, deleteNote, getNotesForProject } = useNotesStore();
  const projectNotes = getNotesForProject(projectId);
  const [newNoteContent, setNewNoteContent] = useState('');
  const { mode } = useThemeStore();
  const isDark = ['dark', 'midnight', 'forest', 'ocean'].includes(mode);
  const styles = useNotesPanelStyles(isDark);

  return (
    <div className={`rounded-xl border ${styles.cardBg} shadow-card flex flex-col h-full`}>
      <PanelHeader color={styles.headerColor} headingColor={styles.headingColor} noteCountColor={styles.noteCountColor} headerBg={styles.headerBg} noteCount={projectNotes.length} />
      <AddNoteForm value={newNoteContent} onChange={setNewNoteContent} onAdd={() => { if (newNoteContent.trim()) { addNote(projectId, newNoteContent.trim()); setNewNoteContent(''); } }} isDark={isDark} styles={styles} />
      <div className="flex-1 overflow-y-auto px-3 py-3 space-y-2">
        {projectNotes.length === 0 ? (
          <EmptyState color={styles.emptyStateColor} />
        ) : (
          projectNotes.map((note) => <NoteItem key={note.id} note={note} onUpdate={updateNote} onDelete={deleteNote} formatDate={formatDate} isDark={isDark} />)
        )}
      </div>
    </div>
  );
}

function useNotesPanelStyles(isDark: boolean) {
  return {
    cardBg: isDark ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200',
    headerBg: isDark ? 'border-slate-800' : 'border-slate-200',
    headerColor: isDark ? 'text-amber-400' : 'text-amber-500',
    headingColor: isDark ? 'text-slate-200' : 'text-slate-800',
    noteCountColor: isDark ? 'text-slate-600' : 'text-slate-400',
    addNoteBg: isDark ? 'bg-slate-800/50 border-slate-700/60' : 'bg-slate-50 border-slate-200',
    textareaColor: isDark ? 'text-slate-200 placeholder-slate-600' : 'text-slate-800 placeholder-slate-400',
    emptyStateColor: isDark ? 'text-slate-600' : 'text-slate-400',
  };
}

interface PanelHeaderProps {
  color: string; headingColor: string; noteCount: number; noteCountColor: string; headerBg: string;
}

function PanelHeader({ color, headingColor, noteCount, noteCountColor, headerBg }: PanelHeaderProps): React.ReactElement {
  return (
    <div className={`flex items-center gap-2 px-4 py-3 border-b ${headerBg}`}>
      <StickyNote className={`w-4 h-4 ${color}`} />
      <h3 className={`text-sm font-semibold ${headingColor}`}>Notes</h3>
      <span className={`ml-auto text-xs ${noteCountColor}`}>{noteCount}</span>
    </div>
  );
}

interface AddNoteFormProps {
  value: string; onChange: (v: string) => void; onAdd: () => void;
  isDark: boolean;
  styles: { addNoteBg: string; textareaColor: string };
}

function AddNoteForm({ value, onChange, onAdd, isDark, styles }: AddNoteFormProps): React.ReactElement {
  const hasContent = value.trim().length > 0;
  const disabledClass = ['flex items-center gap-1 px-2.5 py-1', 'bg-gradient-to-r from-amber-500 to-amber-600', 'text-white text-xs font-medium rounded-md', 'hover:from-amber-600 hover:to-amber-700 transition-all', 'disabled:opacity-40 disabled:cursor-not-allowed'].join(' ');
  const charCountColor = isDark ? 'text-slate-600' : 'text-slate-400';
  const textareaClass = ['w-full bg-transparent rounded-lg border-none text-xs px-3 py-2 resize-none', 'focus:outline-none focus:ring-1 focus:ring-amber-500/40', styles.textareaColor].join(' ');
  const inputRowBorder = isDark ? 'border-slate-700/60' : 'border-slate-200';

  return (
    <div className={`mx-3 mt-3 rounded-lg border ${styles.addNoteBg}`}>
      <textarea value={value} onChange={(e) => onChange(e.target.value)} placeholder="Add a note..." rows={2} className={textareaClass} />
      <div className={`flex items-center justify-between px-3 py-1.5 border-t ${inputRowBorder}`}>
        <span className={`text-xs ${charCountColor}`}>{hasContent && `${value.length} chars`}</span>
        <button onClick={onAdd} disabled={!hasContent} className={disabledClass}><Plus className="w-3 h-3" /> Add</button>
      </div>
    </div>
  );
}

interface EmptyStateProps { color: string; }

function EmptyState({ color }: EmptyStateProps): React.ReactElement {
  return (
    <div className={`flex flex-col items-center justify-center py-6 text-center ${color}`}>
      <StickyNote className="w-8 h-8 mb-2 opacity-50" />
      <p className="text-xs">No notes yet</p>
    </div>
  );
}

interface NoteItemProps {
  note: WorkspaceNote; onUpdate: (id: string, content: string) => void;
  onDelete: (id: string) => void; formatDate: (ts: number) => string; isDark: boolean;
}

function NoteItem({ note, onUpdate, onDelete, formatDate, isDark }: NoteItemProps): React.ReactElement {
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState(note.content);
  const itemStyles = useNoteItemStyles(isDark);

  return (
    <div className={`rounded-lg border ${itemStyles.itemBg} transition-all`}>
      {isEditing ? (
        <NoteEditMode value={editContent} onChange={setEditContent} onSave={() => editContent.trim() && (onUpdate(note.id, editContent.trim()), setIsEditing(false))} onCancel={() => { setEditContent(note.content); setIsEditing(false); }} editTextareaBg={itemStyles.editTextareaBg} cancelBtnBg={itemStyles.cancelBtnBg} />
      ) : (
        <NoteViewMode content={note.content} formattedDate={formatDate(note.updatedAt)} textColor={itemStyles.textColor} timestampColor={itemStyles.timestampColor} onEdit={() => setIsEditing(true)} onDelete={() => onDelete(note.id)} editBtnColor={itemStyles.editBtnColor} deleteBtnColor={itemStyles.deleteBtnColor} />
      )}
    </div>
  );
}

function useNoteItemStyles(isDark: boolean) {
  return {
    itemBg: isDark ? 'bg-slate-800/40 border-slate-700/50' : 'bg-slate-50 border-slate-200',
    textColor: isDark ? 'text-slate-300' : 'text-slate-700',
    timestampColor: isDark ? 'text-slate-600' : 'text-slate-400',
    editTextareaBg: isDark ? 'bg-slate-800 border-slate-600 text-slate-200' : 'bg-white border-slate-300 text-slate-800',
    cancelBtnBg: isDark ? 'bg-slate-700 text-slate-300 hover:bg-slate-600' : 'bg-slate-200 text-slate-600 hover:bg-slate-300',
    editBtnColor: isDark ? 'text-slate-500 hover:text-amber-400 hover:bg-slate-700/50' : 'text-slate-400 hover:text-amber-600 hover:bg-amber-50',
    deleteBtnColor: isDark ? 'text-slate-500 hover:text-red-400 hover:bg-slate-700/50' : 'text-slate-400 hover:text-red-600 hover:bg-red-50',
  };
}

interface NoteEditModeProps {
  value: string; onChange: (v: string) => void; onSave: () => void; onCancel: () => void;
  editTextareaBg: string; cancelBtnBg: string;
}

function NoteEditMode({ value, onChange, onSave, onCancel, editTextareaBg, cancelBtnBg }: NoteEditModeProps): React.ReactElement {
  const saveBtnClass = ['flex-1 px-2 py-1', 'bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-medium rounded transition-colors'].join(' ');

  return (
    <div className="p-2.5 space-y-2">
      <textarea value={value} onChange={(e) => onChange(e.target.value)} rows={3} className={`w-full rounded-md border text-xs px-2 py-1.5 resize-none focus:outline-none focus:ring-1 focus:ring-amber-500/40 ${editTextareaBg}`} />
      <div className="flex gap-1.5">
        <button onClick={onSave} className={saveBtnClass}>Save</button>
        <button onClick={onCancel} className={cancelBtnBg} style={{ flex: 1, padding: '4px 8px', fontSize: '12px', fontWeight: 600, borderRadius: 4, transition: 'background-color 0.15s' }}>Cancel</button>
      </div>
    </div>
  );
}

interface NoteViewModeProps {
  content: string; formattedDate: string; textColor: string; timestampColor: string;
  onEdit: () => void; onDelete: () => void; editBtnColor: string; deleteBtnColor: string;
}

function NoteViewMode({ content, formattedDate, textColor, timestampColor, onEdit, onDelete, editBtnColor, deleteBtnColor }: NoteViewModeProps): React.ReactElement {
  const truncated = content.length > 120 ? content.slice(0, 120) + '...' : content;

  return (
    <div className="p-2.5 space-y-1.5">
      <p className={`text-xs whitespace-pre-wrap leading-relaxed ${textColor}`}>{truncated}</p>
      <div className="flex items-center justify-between">
        <span className={`flex items-center gap-1 text-xs ${timestampColor}`}><Clock className="w-3 h-3" />{formattedDate}</span>
        <div className="flex gap-1">
          <button onClick={onEdit} className={`p-1 rounded transition-colors ${editBtnColor}`}><Pencil className="w-3 h-3" /></button>
          <button onClick={onDelete} className={`p-1 rounded transition-colors ${deleteBtnColor}`}><Trash2 className="w-3 h-3" /></button>
        </div>
      </div>
    </div>
  );
}
