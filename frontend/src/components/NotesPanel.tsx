import { useState } from 'react';
import { useNotesStore, WorkspaceNote } from '../stores/notesStore';

interface Props {
  projectId: string;
}

export function NotesPanel({ projectId }: Props): React.ReactElement {
  const { addNote, updateNote, deleteNote, getNotesForProject } = useNotesStore();
  const projectNotes = getNotesForProject(projectId);
  const [newNoteContent, setNewNoteContent] = useState('');

  const handleAddNote = (): void => {
    if (newNoteContent.trim()) {
      addNote(projectId, newNoteContent.trim());
      setNewNoteContent('');
    }
  };

  const formatDate = (timestamp: number): string => {
    return new Date(timestamp).toLocaleString();
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 h-full flex flex-col">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Notes</h3>

      <div className="mb-4 space-y-2">
        <textarea
          value={newNoteContent}
          onChange={(e) => setNewNoteContent(e.target.value)}
          placeholder="Add a note..."
          rows={3}
          className="w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm px-3 py-2"
        />
        <button
          onClick={handleAddNote}
          disabled={!newNoteContent.trim()}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-1.5 px-4 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Add Note
        </button>
      </div>

      <div className="flex-1 overflow-y-auto space-y-3">
        {projectNotes.length === 0 ? (
          <p className="text-gray-500 dark:text-gray-400 text-sm text-center py-4">
            No notes yet. Add one above!
          </p>
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
    <div className="border border-gray-200 dark:border-gray-700 rounded-md p-3 space-y-2">
      {isEditing ? (
        <>
          <textarea
            value={editContent}
            onChange={(e) => setEditContent(e.target.value)}
            rows={Math.min(6, editContent.split('\n').length + 1)}
            className="w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm px-2 py-1"
          />
          <div className="flex gap-2">
            <button
              onClick={handleSave}
              className="flex-1 bg-green-600 hover:bg-green-700 text-white font-medium py-1 px-3 rounded-md text-sm transition-colors"
            >
              Save
            </button>
            <button
              onClick={handleCancel}
              className="flex-1 bg-gray-400 hover:bg-gray-500 text-white font-medium py-1 px-3 rounded-md text-sm transition-colors"
            >
              Cancel
            </button>
          </div>
        </>
      ) : (
        <>
          <p className="text-sm text-gray-800 dark:text-gray-200 whitespace-pre-wrap">{note.content}</p>
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-500 dark:text-gray-400">
              {formatDate(note.updatedAt)}
            </span>
            <div className="flex gap-2">
              <button
                onClick={() => setIsEditing(true)}
                className="text-blue-600 dark:text-blue-400 hover:underline text-xs"
              >
                Edit
              </button>
              <button
                onClick={() => onDelete(note.id)}
                className="text-red-600 dark:text-red-400 hover:underline text-xs"
              >
                Delete
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
