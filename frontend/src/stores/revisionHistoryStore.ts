import { create } from 'zustand';

export interface RevisionEntry {
  documentId: string;
  version: number;
  content: string;
  timestamp: number;
}

interface RevisionHistoryState {
  history: Map<string, RevisionEntry[]>;
  addEntry: (entry: RevisionEntry) => void;
  getHistory: (documentId: string) => RevisionEntry[];
  getPreviousVersion: (documentId: string, currentVersion: number) => string | null;
  clearHistory: (documentId: string) => void;
  clearAll: () => void;
}

const MAX_HISTORY = 50;

export const useRevisionHistoryStore = create<RevisionHistoryState>((set, get) => ({
  history: new Map(),

  addEntry: (entry) => set((state) => {
    const next = new Map(state.history);
    const entries = next.get(entry.documentId) ?? [];
    const updated = [entry, ...entries].slice(0, MAX_HISTORY);
    next.set(entry.documentId, updated);
    return { history: next };
  }),

  getHistory: (_documentId) => {
    const state = get();
    return state.history.get(_documentId) ?? [];
  },

  getPreviousVersion: (documentId, currentVersion) => {
    const state = get();
    const entries = state.history.get(documentId) ?? [];
    const prev = entries.find((e) => e.version < currentVersion);
    return prev?.content ?? null;
  },

  clearHistory: (documentId) => set((state) => {
    const next = new Map(state.history);
    next.delete(documentId);
    return { history: next };
  }),

  clearAll: () => set({ history: new Map() }),
}));
