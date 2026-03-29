/**
 * FE-027: Diff utilities
 *
 * Utilities for computing and rendering text diffs.
 * Uses a linear prefix/middle/suffix comparison so large manuscripts do not pay
 * the quadratic cost of a full LCS matrix.
 */

import type { DiffChange, DiffResult } from '../types/aids';

/**
 * Compute a line-level diff between two texts.
 *
 * The diff is intentionally conservative: it preserves common prefixes and
 * suffixes, then treats the changed middle as one replace / insert / delete
 * block. That keeps the output honest without pretending to have a fine-grained
 * edit script when we are not paying for one.
 */
export function computeDiff(original: string, modified: string): DiffResult {
  const originalLines = splitLines(original);
  const modifiedLines = splitLines(modified);
  const changes: DiffChange[] = [];

  const prefixLength = findCommonPrefixLength(originalLines, modifiedLines);
  const suffixLength = findCommonSuffixLength(originalLines, modifiedLines, prefixLength);

  if (prefixLength > 0) {
    changes.push(createChange('equal', originalLines.slice(0, prefixLength), originalLines.slice(0, prefixLength)));
  }

  const originalMiddle = originalLines.slice(prefixLength, originalLines.length - suffixLength);
  const modifiedMiddle = modifiedLines.slice(prefixLength, modifiedLines.length - suffixLength);

  if (originalMiddle.length > 0 || modifiedMiddle.length > 0) {
    if (originalMiddle.length > 0 && modifiedMiddle.length > 0) {
      changes.push(createChange('replace', originalMiddle, modifiedMiddle));
    } else if (originalMiddle.length > 0) {
      changes.push(createChange('delete', originalMiddle, []));
    } else {
      changes.push(createChange('insert', [], modifiedMiddle));
    }
  }

  if (suffixLength > 0) {
    const suffixStartOriginal = originalLines.length - suffixLength;
    const suffixLines = originalLines.slice(suffixStartOriginal);
    changes.push(createChange('equal', suffixLines, suffixLines, suffixStartOriginal, modifiedLines.length - suffixLength));
  }

  return {
    original,
    modified,
    changes,
  };
}

function splitLines(text: string): string[] {
  return text.length === 0 ? [] : text.split('\n');
}

function findCommonPrefixLength(a: string[], b: string[]): number {
  const limit = Math.min(a.length, b.length);
  let index = 0;

  while (index < limit && a[index] === b[index]) {
    index++;
  }

  return index;
}

function findCommonSuffixLength(a: string[], b: string[], prefixLength: number): number {
  const maxSuffix = Math.min(a.length - prefixLength, b.length - prefixLength);
  let suffixLength = 0;

  while (
    suffixLength < maxSuffix &&
    a[a.length - 1 - suffixLength] === b[b.length - 1 - suffixLength]
  ) {
    suffixLength++;
  }

  return suffixLength;
}

function createChange(
  type: DiffChange['type'],
  originalLines: string[],
  modifiedLines: string[],
  originalIndex?: number,
  modifiedIndex?: number,
): DiffChange {
  return {
    type,
    originalText: originalLines.join('\n'),
    modifiedText: modifiedLines.join('\n'),
    originalIndex,
    modifiedIndex,
  };
}

/**
 * Format diff for display with ANSI-style markers.
 */
export function formatDiff(diff: DiffResult): string {
  return diff.changes
    .flatMap((change) => {
      switch (change.type) {
        case 'equal':
          return prefixLines(change.originalText, ' ');
        case 'insert':
          return prefixLines(change.modifiedText, '+');
        case 'delete':
          return prefixLines(change.originalText, '-');
        case 'replace':
          return [
            ...prefixLines(change.originalText, '-'),
            ...prefixLines(change.modifiedText, '+'),
          ];
      }
    })
    .join('\n');
}

/**
 * Get summary statistics for a diff.
 */
export function getDiffSummary(diff: DiffResult): {
  additions: number;
  deletions: number;
  replacements: number;
  unchanged: number;
} {
  let additions = 0;
  let deletions = 0;
  let replacements = 0;
  let unchanged = 0;

  for (const change of diff.changes) {
    switch (change.type) {
      case 'insert':
        additions += countLines(change.modifiedText);
        break;
      case 'delete':
        deletions += countLines(change.originalText);
        break;
      case 'replace':
        additions += countLines(change.modifiedText);
        deletions += countLines(change.originalText);
        replacements += 1;
        break;
      case 'equal':
        unchanged += countLines(change.originalText);
        break;
    }
  }

  return { additions, deletions, replacements, unchanged };
}

function countLines(text: string): number {
  return text.length === 0 ? 0 : text.split('\n').length;
}

function prefixLines(text: string, marker: string): string[] {
  if (!text) {
    return [marker];
  }

  return text.split('\n').map((line) => `${marker}${line}`);
}
