/**
 * FE-026: Selection utilities
 * 
 * Utilities for managing text selections across manuscript, draft, and suggestion views.
 */

import type { SelectionRecord } from '../types/aids';

export interface SelectionRange {
  start: number;
  end: number;
  text: string;
}

/**
 * Extract selected text from a source string given start/end offsets.
 */
export function extractSelection(
  sourceText: string,
  startOffset: number,
  endOffset: number,
): string {
  const start = Math.max(0, Math.min(startOffset, sourceText.length));
  const end = Math.max(start, Math.min(endOffset, sourceText.length));
  return sourceText.slice(start, end);
}

/**
 * Create a selection record from raw selection data.
 */
export function createSelectionRecord(
  projectId: string,
  sourceType: 'MANUSCRIPT' | 'DRAFT' | 'SUGGESTION',
  sourceId: string,
  startOffset: number,
  endOffset: number,
  selectedText: string,
): SelectionRecord {
  return {
    selection_id: crypto.randomUUID(),
    project_id: projectId,
    source_type: sourceType,
    source_id: sourceId,
    start_offset: startOffset,
    end_offset: endOffset,
    selected_text: selectedText,
    created_at: new Date().toISOString(),
  };
}

/**
 * Check if two selections overlap.
 */
export function selectionsOverlap(
  a: SelectionRange,
  b: SelectionRange,
): boolean {
  return a.start < b.end && b.start < a.end;
}

/**
 * Check if a selection is within a given range.
 */
export function selectionInRange(
  selection: SelectionRange,
  rangeStart: number,
  rangeEnd: number,
): boolean {
  return selection.start >= rangeStart && selection.end <= rangeEnd;
}

/**
 * Merge overlapping selections.
 */
export function mergeSelections(selections: SelectionRange[]): SelectionRange[] {
  if (selections.length === 0) return [];
  
  const sorted = [...selections].sort((a, b) => a.start - b.start);
  const merged: SelectionRange[] = [sorted[0]];
  
  for (let i = 1; i < sorted.length; i++) {
    const current = sorted[i];
    const last = merged[merged.length - 1];
    
    if (current.start <= last.end) {
      // Overlapping - merge
      merged[merged.length - 1] = {
        start: last.start,
        end: Math.max(last.end, current.end),
        text: '', // Will be recalculated from source
      };
    } else {
      merged.push(current);
    }
  }
  
  return merged;
}

/**
 * Get character position from line/column.
 */
export function lineColToOffset(
  text: string,
  line: number,
  col: number,
): number {
  const lines = text.split('\n');
  let offset = 0;
  
  for (let i = 0; i < Math.min(line, lines.length - 1); i++) {
    offset += lines[i].length + 1; // +1 for newline
  }
  
  offset += Math.min(col, lines[line]?.length || 0);
  return offset;
}

/**
 * Get line/column from character position.
 */
export function offsetToLineCol(text: string, offset: number): { line: number; col: number } {
  const lines = text.split('\n');
  let currentOffset = 0;
  
  for (let i = 0; i < lines.length; i++) {
    const lineLength = lines[i].length + 1; // +1 for newline
    
    if (currentOffset + lineLength > offset) {
      return { line: i, col: offset - currentOffset };
    }
    
    currentOffset += lineLength;
  }
  
  return { line: lines.length - 1, col: lines[lines.length - 1].length };
}
