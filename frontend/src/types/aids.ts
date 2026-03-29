/**
 * FE-025/026/027/028: Shared types for manuscript aids
 * 
 * Types used across aids panel, selection, diff viewer, and suggestion history.
 */

export interface RevisionSuggestion {
  suggestion_id: string;
  project_id: string;
  manuscript_id: string;
  draft_id: string | null;
  suggestion_type: 'INSERT' | 'REPLACE' | 'DELETE';
  anchor_position: number;
  anchor_text: string;
  proposed_text: string;
  rationale: string;
  state: 'PENDING' | 'ACCEPTED' | 'REJECTED';
  created_at: string;
}

export interface SelectionRecord {
  selection_id: string;
  project_id: string;
  source_type: 'MANUSCRIPT' | 'DRAFT' | 'SUGGESTION';
  source_id: string;
  start_offset: number;
  end_offset: number;
  selected_text: string;
  created_at: string;
}

export interface DiffResult {
  original: string;
  modified: string;
  changes: Array<{
    type: 'equal' | 'insert' | 'delete' | 'replace';
    value: string;
    original_index?: number;
    modified_index?: number;
  }>;
}

export interface AidsPanelState {
  activeTab: 'suggestions' | 'diff' | 'history';
  selectedSuggestionId: string | null;
  selectedSelectionId: string | null;
  isComparing: boolean;
  comparisonOriginalId: string | null;
  comparisonModifiedId: string | null;
}
