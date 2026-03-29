/**
 * FE-027: Diff utilities
 * 
 * Utilities for computing and rendering text diffs.
 * Uses a simple LCS-based algorithm for line-level diffs.
 */

import type { DiffResult } from '../types/aids';

export interface DiffChange {
  type: 'equal' | 'insert' | 'delete' | 'replace';
  value: string;
  originalIndex?: number;
  modifiedIndex?: number;
}

/**
 * Compute a line-level diff between two texts.
 * Uses a simplified LCS algorithm optimized for readability.
 */
export function computeDiff(original: string, modified: string): DiffResult {
  const originalLines = original.split('\n');
  const modifiedLines = modified.split('\n');
  
  const lcs = computeLCS(originalLines, modifiedLines);
  const changes = buildChanges(originalLines, modifiedLines, lcs);
  
  return {
    original,
    modified,
    changes,
  };
}

/**
 * Compute Longest Common Subsequence of line indices.
 */
function computeLCS(a: string[], b: string[]): number[][] {
  const m = a.length;
  const n = b.length;
  
  // DP table for LCS lengths
  const dp = Array(m + 1).fill(0).map(() => Array(n + 1).fill(0));
  
  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      if (a[i - 1] === b[j - 1]) {
        dp[i][j] = dp[i - 1][j - 1] + 1;
      } else {
        dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
      }
    }
  }
  
  // Backtrack to find actual LCS
  const lcs: number[][] = [];
  let i = m, j = n;
  
  while (i > 0 && j > 0) {
    if (a[i - 1] === b[j - 1]) {
      lcs.unshift([i - 1, j - 1]);
      i--;
      j--;
    } else if (dp[i - 1][j] > dp[i][j - 1]) {
      i--;
    } else {
      j--;
    }
  }
  
  return lcs;
}

/**
 * Build change list from original, modified, and LCS.
 */
function buildChanges(a: string[], b: string[], lcs: number[][]): DiffChange[] {
  const changes: DiffChange[] = [];
  let aIdx = 0;
  let bIdx = 0;
  let lcsIdx = 0;
  
  while (aIdx < a.length || bIdx < b.length) {
    if (lcsIdx < lcs.length) {
      const [ai, bi] = lcs[lcsIdx];
      
      // Handle deletions before next match
      while (aIdx < ai) {
        changes.push({
          type: 'delete',
          value: a[aIdx] + '\n',
          originalIndex: aIdx,
        });
        aIdx++;
      }
      
      // Handle insertions before next match
      while (bIdx < bi) {
        changes.push({
          type: 'insert',
          value: b[bIdx] + '\n',
          modifiedIndex: bIdx,
        });
        bIdx++;
      }
      
      // Add equal segment
      changes.push({
        type: 'equal',
        value: a[ai] + '\n',
        originalIndex: ai,
        modifiedIndex: bi,
      });
      
      aIdx = ai + 1;
      bIdx = bi + 1;
      lcsIdx++;
    } else {
      // Remaining deletions
      while (aIdx < a.length) {
        changes.push({
          type: 'delete',
          value: a[aIdx] + '\n',
          originalIndex: aIdx,
        });
        aIdx++;
      }
      
      // Remaining insertions
      while (bIdx < b.length) {
        changes.push({
          type: 'insert',
          value: b[bIdx] + '\n',
          modifiedIndex: bIdx,
        });
        bIdx++;
      }
    }
  }
  
  return consolidateChanges(changes);
}

/**
 * Consolidate adjacent insert/delete pairs into replaces.
 */
function consolidateChanges(changes: DiffChange[]): DiffChange[] {
  const result: DiffChange[] = [];
  
  for (let i = 0; i < changes.length; i++) {
    const change = changes[i];
    
    // Look for delete followed by insert -> replace
    if (
      change.type === 'delete' &&
      i + 1 < changes.length &&
      changes[i + 1].type === 'insert'
    ) {
      result.push({
        type: 'replace',
        value: change.value + changes[i + 1].value,
        originalIndex: change.originalIndex,
        modifiedIndex: changes[i + 1].modifiedIndex,
      });
      i++; // Skip next change
    } else {
      result.push(change);
    }
  }
  
  return result;
}

/**
 * Format diff for display with ANSI-style markers.
 */
export function formatDiff(diff: DiffResult): string {
  return diff.changes
    .map(change => {
      if (change.type === 'delete') {
        return `-${change.value.replace(/\n$/, '')}`;
      }
      if (change.type === 'insert') {
        return `+${change.value.replace(/\n$/, '')}`;
      }
      if (change.type === 'replace') {
        const parts = change.value.split('\n');
        return parts.map(p => `~${p}`).join('\n');
      }
      return ` ${change.value.replace(/\n$/, '')}`;
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
        additions += change.value.split('\n').length - 1;
        break;
      case 'delete':
        deletions += change.value.split('\n').length - 1;
        break;
      case 'replace':
        replacements++;
        break;
      case 'equal':
        unchanged += change.value.split('\n').length - 1;
        break;
    }
  }
  
  return { additions, deletions, replacements, unchanged };
}
