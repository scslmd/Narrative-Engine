/**
 * FE-026: Selection store
 * 
 * Zustand store for managing text selections across the application.
 */

import { create } from 'zustand';
import type { SelectionRecord } from '../types/aids';

interface SelectionState {
  // Current active selection
  activeSelection: SelectionRecord | null;
  
  // History of selections for this session
  selectionHistory: SelectionRecord[];
  
  // Actions
  setActiveSelection: (selection: SelectionRecord | null) => void;
  addSelectionToHistory: (selection: SelectionRecord) => void;
  clearSelections: () => void;
  getSelectionById: (id: string) => SelectionRecord | undefined;
  removeSelectionFromHistory: (id: string) => void;
}

export const useSelectionStore = create<SelectionState>((set, get) => ({
  activeSelection: null,
  selectionHistory: [],
  
  setActiveSelection: (selection) => set({ activeSelection: selection }),
  
  addSelectionToHistory: (selection) => {
    const { selectionHistory } = get();
    // Remove duplicate if exists
    const filtered = selectionHistory.filter(
      s => s.selection_id !== selection.selection_id,
    );
    set({ selectionHistory: [selection, ...filtered].slice(0, 50) }); // Keep last 50
  },
  
  clearSelections: () => set({ activeSelection: null, selectionHistory: [] }),
  
  getSelectionById: (id) => {
    const { selectionHistory } = get();
    return selectionHistory.find(s => s.selection_id === id);
  },
  
  removeSelectionFromHistory: (id) => {
    const { selectionHistory, activeSelection } = get();
    const filtered = selectionHistory.filter(s => s.selection_id !== id);
    
    // Clear active if it was removed
    const newActive = activeSelection?.selection_id === id ? null : activeSelection;
    
    set({ selectionHistory: filtered, activeSelection: newActive });
  },
}));
