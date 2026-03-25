import { create } from 'zustand';
import type { WorkspaceNotes } from '../types/workspace';
import { getStorageKey, getItem, setItem } from '../lib/storage';

interface WorkspaceStore {
  currentProjectId: string | null;
  notes: string;
  lastUpdated: string | null;
  
  setCurrentProjectId: (projectId: string | null) => void;
  updateNotes: (notes: string) => void;
  loadNotesForProject: (projectId: string) => void;
  clearCurrentProject: () => void;
}

const DEBOUNCE_DELAY = 1000;

export const useWorkspaceStore = create<WorkspaceStore>((set, get) => ({
  currentProjectId: null,
  notes: '',
  lastUpdated: null,

  setCurrentProjectId: (projectId) => {
    if (projectId && projectId !== get().currentProjectId) {
      get().loadNotesForProject(projectId);
    }
    set({ currentProjectId: projectId });
  },

  updateNotes: (notes) => {
    const state = get();
    if (!state.currentProjectId) return;

    set({ notes, lastUpdated: new Date().toISOString() });

    const key = getStorageKey(state.currentProjectId, 'workspace');
    const data: WorkspaceNotes = {
      projectId: state.currentProjectId,
      notes,
      lastUpdated: new Date().toISOString(),
    };

    setTimeout(() => {
      setItem(key, JSON.stringify(data));
    }, DEBOUNCE_DELAY);
  },

  loadNotesForProject: (projectId) => {
    const key = getStorageKey(projectId, 'workspace');
    const stored = getItem(key);

    if (stored) {
      try {
        const data: WorkspaceNotes = JSON.parse(stored);
        set({ notes: data.notes, lastUpdated: data.lastUpdated });
      } catch {
        set({ notes: '', lastUpdated: null });
      }
    } else {
      set({ notes: '', lastUpdated: null });
    }
  },

  clearCurrentProject: () => {
    set({ currentProjectId: null, notes: '', lastUpdated: null });
  },
}));
