import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface WorkspaceNote {
  id: string;
  projectId: string;
  content: string;
  createdAt: number;
  updatedAt: number;
}

interface NotesStore {
  notes: WorkspaceNote[];
  addNote: (projectId: string, content: string) => void;
  updateNote: (id: string, content: string) => void;
  deleteNote: (id: string) => void;
  getNotesForProject: (projectId: string) => WorkspaceNote[];
}

const generateId = (): string => Math.random().toString(36).substring(2, 9);

export const useNotesStore = create<NotesStore>()(
  persist(
    (set, get) => ({
      notes: [],

      addNote: (projectId, content) => {
        const note: WorkspaceNote = {
          id: generateId(),
          projectId,
          content,
          createdAt: Date.now(),
          updatedAt: Date.now(),
        };
        set((state) => ({ notes: [...state.notes, note] }));
      },

      updateNote: (id, content) => {
        set((state) => ({
          notes: state.notes.map((note) =>
            note.id === id ? { ...note, content, updatedAt: Date.now() } : note
          ),
        }));
      },

      deleteNote: (id) => {
        set((state) => ({
          notes: state.notes.filter((note) => note.id !== id),
        }));
      },

      getNotesForProject: (projectId) => {
        return get().notes.filter((note) => note.projectId === projectId);
      },
    }),
    {
      name: 'workspace-notes-storage',
    }
  )
);
