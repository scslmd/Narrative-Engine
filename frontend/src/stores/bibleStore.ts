import { create } from 'zustand';
import type { BibleEntry } from '../types/bible';
import { getStorageKey, getItem, setItem } from '../lib/storage';

const MAX_PINNED_PER_TYPE = 10;

interface BibleStore {
  currentProjectId: string | null;
  pinnedEntries: BibleEntry[];
  
  setCurrentProjectId: (projectId: string | null) => void;
  pinEntry: (entry: BibleEntry) => boolean;
  unpinEntry: (entryId: string) => void;
  loadPinnedEntries: (projectId: string) => void;
  clearCurrentProject: () => void;
}

export const useBibleStore = create<BibleStore>((set, get) => ({
  currentProjectId: null,
  pinnedEntries: [],

  setCurrentProjectId: (projectId) => {
    if (projectId && projectId !== get().currentProjectId) {
      get().loadPinnedEntries(projectId);
    }
    set({ currentProjectId: projectId });
  },

  pinEntry: (entry) => {
    const state = get();
    
    if (!state.currentProjectId) return false;
    
    if (state.pinnedEntries.some((e) => e.id === entry.id)) {
      return false;
    }
    
    const countOfType = state.pinnedEntries.filter(
      (e) => e.type === entry.type
    ).length;
    
    if (countOfType >= MAX_PINNED_PER_TYPE) {
      console.warn(`Limit reached for ${entry.type} entries`);
      return false;
    }

    const updated = [...state.pinnedEntries, entry];
    set({ pinnedEntries: updated });

    const key = getStorageKey(state.currentProjectId, 'pinnedBible');
    setItem(key, JSON.stringify(updated));

    return true;
  },

  unpinEntry: (entryId) => {
    const state = get();
    
    if (!state.currentProjectId) return;

    const updated = state.pinnedEntries.filter((e) => e.id !== entryId);
    set({ pinnedEntries: updated });

    const key = getStorageKey(state.currentProjectId, 'pinnedBible');
    setItem(key, JSON.stringify(updated));
  },

  loadPinnedEntries: (projectId) => {
    const key = getStorageKey(projectId, 'pinnedBible');
    const stored = getItem(key);

    if (stored) {
      try {
        const entries: BibleEntry[] = JSON.parse(stored);
        set({ pinnedEntries: entries });
      } catch {
        set({ pinnedEntries: [] });
      }
    } else {
      set({ pinnedEntries: [] });
    }
  },

  clearCurrentProject: () => {
    set({ currentProjectId: null, pinnedEntries: [] });
  },
}));
