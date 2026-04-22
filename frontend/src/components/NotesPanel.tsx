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

  const cardBg = isDark
    ? 'bg-slate-900 border-slate-800'
    : 'bg-white border-slate-200'
  const headerBg = isDark
    ? 'border-slate-800'
    : 'border-slate-200'
  const headerColor = isDark
    ? 'text-amber-400'
    : 'text-amber-500'
  const headingColor = isDark
    ? 'text-slate-200'
    : 'text-slate-800'
  const noteCountColor = isDark
    ? 'text-slate-600'
    : 'text-slate-400'
  const addNoteBg = isDark
    ? 'bg-slate-800/50 border-slate-700/60'
    : 'bg-slate-50 border-slate-200'
  const textareaColor = isDark
    ? 'text-slate-200 placeholder-slate-600'
    : 'text-slate-800 placeholder-slate-400'
  const emptyStateColor = isDark
    ? 'text-slate-600'
    : 'text-slate-400'

  return (
    <div className={`rounded-xl border ${cardBg} shadow-card flex flex-col h-full`}>
      <PanelHeader
        color={headerColor}
        headingColor={headingColor}
        noteCount={projectNotes.length}
        noteCountColor={noteCountColor}
        headerBg={headerBg}
      />

      <AddNoteForm
        value={newNoteContent}
        onChange={setNewNoteContent}
        onAdd={handleAddNote}
        isDark={isDark}
        addNoteBg={addNoteBg}
        textareaColor={textareaColor}
      />

      <div className="flex-1 overflow-y-auto px-3 py-3 space-y-2">
        {projectNotes.length === 0 ? (
          <EmptyState color={emptyStateColor} />
        ) : (
          projectNotes.map((note) => (
            <NoteItem
              key={note.id}
              note={note}
              onUpdate={updateNote}
              onDelete={deleteNote}
              formatDate={formatDate}
              isDark={isDark}
            />
          ))
        )}
      </div>
    </div>
  );
}

interface PanelHeaderProps {
  color: string;
  headingColor: string;
  noteCount: number;
  noteCountColor: string;
  headerBg: string;
}

function PanelHeader({
  color, headingColor, noteCount, noteCountColor, headerBg,
}: PanelHeaderProps): React.ReactElement {
  return (
    <div className={`flex items-center gap-2 px-4 py-3 border-b ${headerBg}`}>
      <StickyNote className={`w-4 h-4 ${color}`} />
      <h3 className={`text-sm font-semibold ${headingColor}`}>Notes</h3>
      <span className={`ml-auto text-xs ${noteCountColor}`}>
        {noteCount}
      </span>
    </div>
  );
}

interface AddNoteFormProps {
  value: string;
  onChange: (value: string) => void;
  onAdd: () => void;
  isDark: boolean;
  addNoteBg: string;
  textareaColor: string;
}

function AddNoteForm({
  value, onChange, onAdd, isDark,
  addNoteBg, textareaColor,
}: AddNoteFormProps): React.ReactElement {
  const hasContent = value.trim().length > 0
  const disabledClass = [
    'flex items-center gap-1 px-2.5 py-1',
    'bg-gradient-to-r from-amber-500 to-amber-600',
    'text-white text-xs font-medium',
    'rounded-md',
    'hover:from-amber-600 hover:to-amber-700',
    'transition-all',
    'disabled:opacity-40 disabled:cursor-not-allowed',
  ].join(' ')

  const charCountColor = isDark
    ? 'text-slate-600'
    : 'text-slate-400'

  const textareaClass = [
    'w-full bg-transparent rounded-lg border-none',
    'text-xs px-3 py-2 resize-none',
    'focus:outline-none focus:ring-1',
    'focus:ring-amber-500/40',
    textareaColor,
  ].join(' ')

  const inputRowBorder = isDark
    ? 'border-slate-700/60'
    : 'border-slate-200'

  return (
    <div className={`mx-3 mt-3 rounded-lg border ${addNoteBg}`}>
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Add a note..."
        rows={2}
        className={textareaClass}
      />
      <div className={`flex items-center justify-between px-3 py-1.5 border-t ${inputRowBorder}`}>
        <span className={`text-xs ${charCountColor}`}>
          {hasContent && `${value.length} chars`}
        </span>
        <button
          onClick={onAdd}
          disabled={!hasContent}
          className={disabledClass}
        >
          <Plus className="w-3 h-3" />
          Add
        </button>
      </div>
    </div>
  );
}

interface EmptyStateProps {
  color: string;
}

function EmptyState({ color }: EmptyStateProps): React.ReactElement {
  return (
    <div className={`flex flex-col items-center justify-center py-6 text-center ${color}`}>
      <StickyNote className="w-8 h-8 mb-2 opacity-50" />
      <p className="text-xs">No notes yet</p>
    </div>
  );
}

interface NoteItemProps {
  note: WorkspaceNote;
  onUpdate: (id: string, content: string) => void;
  onDelete: (id: string) => void;
  formatDate: (timestamp: number) => string;
  isDark: boolean;
}

function NoteItem({
  note, onUpdate, onDelete, formatDate, isDark,
}: NoteItemProps): React.ReactElement {
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState(note.content);

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

  const itemBg = isDark
    ? 'bg-slate-800/40 border-slate-700/50'
    : 'bg-slate-50 border-slate-200'
  const textColor = isDark
    ? 'text-slate-300'
    : 'text-slate-700'
  const timestampColor = isDark
    ? 'text-slate-600'
    : 'text-slate-400'
  const editTextareaBg = isDark
    ? 'bg-slate-800 border-slate-600 text-slate-200'
    : 'bg-white border-slate-300 text-slate-800'
  const cancelBtnBg = isDark
    ? 'bg-slate-700 text-slate-300 hover:bg-slate-600'
    : 'bg-slate-200 text-slate-600 hover:bg-slate-300'
  const editBtnColor = isDark
    ? 'text-slate-500 hover:text-amber-400 hover:bg-slate-700/50'
    : 'text-slate-400 hover:text-amber-600 hover:bg-amber-50'
  const deleteBtnColor = isDark
    ? 'text-slate-500 hover:text-red-400 hover:bg-slate-700/50'
    : 'text-slate-400 hover:text-red-600 hover:bg-red-50'

  return (
    <div className={`rounded-lg border ${itemBg} transition-all`}>
      {isEditing ? (
        <NoteEditMode
          value={editContent}
          onChange={setEditContent}
          onSave={handleSave}
          onCancel={handleCancel}
          editTextareaBg={editTextareaBg}
          cancelBtnBg={cancelBtnBg}
        />
      ) : (
        <NoteViewMode
          content={note.content}
          formattedDate={formatDate(note.updatedAt)}
          textColor={textColor}
          timestampColor={timestampColor}
          onEdit={() => setIsEditing(true)}
          onDelete={() => onDelete(note.id)}
          editBtnColor={editBtnColor}
          deleteBtnColor={deleteBtnColor}
        />
      )}
    </div>
  );
}

interface NoteEditModeProps {
  value: string;
  onChange: (value: string) => void;
  onSave: () => void;
  onCancel: () => void;
  editTextareaBg: string;
  cancelBtnBg: string;
}

function NoteEditMode({
  value, onChange, onSave, onCancel,
  editTextareaBg, cancelBtnBg,
}: NoteEditModeProps): React.ReactElement {
  const saveBtnClass = [
    'flex-1 px-2 py-1',
    'bg-emerald-600 hover:bg-emerald-700',
    'text-white text-xs font-medium',
    'rounded transition-colors',
  ].join(' ')

  const saveBtn = (
    <button onClick={onSave} className={saveBtnClass}>
      Save
    </button>
  )

  const cancelBtn = (
    <button onClick={onCancel} className={cancelBtnBg}
      style={{
        flex: 1,
        padding: '4px 8px',
        fontSize: '12px',
        fontWeight: 600,
        borderRadius: 4,
        transition: 'background-color 0.15s',
      }}
    >
      Cancel
    </button>
  )

  return (
    <div className="p-2.5 space-y-2">
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        rows={3}
        className={`w-full rounded-md border text-xs px-2 py-1.5 resize-none focus:outline-none focus:ring-1 focus:ring-amber-500/40 ${
          editTextareaBg
        }`}
      />
      <div className="flex gap-1.5">
        {saveBtn}
        {cancelBtn}
      </div>
    </div>
  );
}

interface NoteViewModeProps {
  content: string;
  formattedDate: string;
  textColor: string;
  timestampColor: string;
  onEdit: () => void;
  onDelete: () => void;
  editBtnColor: string;
  deleteBtnColor: string;
}

function NoteViewMode({
  content, formattedDate, textColor, timestampColor,
  onEdit, onDelete, editBtnColor, deleteBtnColor,
}: NoteViewModeProps): React.ReactElement {
  const truncated = content.length > 120
    ? content.slice(0, 120) + '...'
    : content

  const editBtn = (
    <button
      onClick={onEdit}
      className={`p-1 rounded transition-colors ${editBtnColor}`}
    >
      <Pencil className="w-3 h-3" />
    </button>
  )

  const deleteBtn = (
    <button
      onClick={onDelete}
      className={`p-1 rounded transition-colors ${deleteBtnColor}`}
    >
      <Trash2 className="w-3 h-3" />
    </button>
  )

  return (
    <div className="p-2.5 space-y-1.5">
      <p className={`text-xs whitespace-pre-wrap leading-relaxed ${textColor}`}>
        {truncated}
      </p>
      <div className="flex items-center justify-between">
        <span className={`flex items-center gap-1 text-xs ${timestampColor}`}>
          <Clock className="w-3 h-3" />
          {formattedDate}
        </span>
        <div className="flex gap-1">
          {editBtn}
          {deleteBtn}
        </div>
      </div>
    </div>
  );
}
