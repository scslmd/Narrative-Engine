/**
 * FE-025/026/027/028: Shared types for manuscript aids
 *
 * Types used across aids panel, selection, diff viewer, and suggestion history.
 */

export type SuggestionStatus = 'REQUESTED' | 'PENDING' | 'ACCEPTED' | 'REJECTED' | 'SUPERSEDED';

export interface RevisionSuggestion {
  suggestion_id: string;
  project_id: string;
  target_document_id: string;
  source_text: string;
  proposed_text: string;
  rationale: string;
  source_context: string[];
  status: SuggestionStatus;
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

export interface DiffChange {
  type: 'equal' | 'insert' | 'delete' | 'replace';
  originalText: string;
  modifiedText: string;
  originalIndex?: number;
  modifiedIndex?: number;
}

export interface DiffResult {
  original: string;
  modified: string;
  changes: DiffChange[];
}

export interface AidsPanelState {
  activeTab: 'suggestions' | 'diff' | 'history';
  selectedSuggestionId: string | null;
  selectedSelectionId: string | null;
  isComparing: boolean;
  comparisonOriginalId: string | null;
  comparisonModifiedId: string | null;
}
