/**
 * Arcs Service
 * 
 * Service for interacting with arcs-related API endpoints:
 * - Arc candidates
 * - Arc selections
 * - Arc stage mappings
 */

import type {
  ArcCandidate,
  ArcSelection,
  ArcStageMap,
  ArcComparisonRecord,
} from '../types/arcs';
import api from '../lib/api';

interface ArcsListResponse<T> {
  project_id: string;
  items: T[];
  meta: Record<string, string>;
}

/**
 * Get all arc candidates for a project
 */
export async function getArcCandidates(projectId: string): Promise<ArcCandidate[]> {
  const response = await api.get('/story-development/arcs/candidates', {
    params: { project_id: projectId },
  });

  if (response.status !== 200) {
    throw new Error(`Failed to fetch arc candidates: ${response.status}`);
  }

  const data: ArcsListResponse<ArcCandidate> = response.data;
  return data.items;
}

/**
 * Get all arc comparisons for a project
 */
export async function getArcComparisons(projectId: string): Promise<ArcComparisonRecord[]> {
  const response = await api.get('/story-development/arcs/comparisons', {
    params: { project_id: projectId },
  });

  if (response.status !== 200) {
    throw new Error(`Failed to fetch arc comparisons: ${response.status}`);
  }

  const data: ArcsListResponse<ArcComparisonRecord> = response.data;
  return data.items;
}

/**
 * Get all arc selections for a project
 */
export async function getArcSelections(projectId: string): Promise<ArcSelection[]> {
  const response = await api.get('/story-development/arcs/selections', {
    params: { project_id: projectId },
  });

  if (response.status !== 200) {
    throw new Error(`Failed to fetch arc selections: ${response.status}`);
  }

  const data: ArcsListResponse<ArcSelection> = response.data;
  return data.items;
}

/**
 * Get all arc stage mappings for a project
 */
export async function getArcStageMaps(projectId: string): Promise<ArcStageMap[]> {
  const response = await api.get('/story-development/arcs/stage-maps', {
    params: { project_id: projectId },
  });

  if (response.status !== 200) {
    throw new Error(`Failed to fetch arc stage maps: ${response.status}`);
  }

  const data: ArcsListResponse<ArcStageMap> = response.data;
  return data.items;
}

/**
 * Get arc stage map for a specific arc
 */
export function getStageMapForArc(
  stageMaps: ArcStageMap[],
  arcId: string,
): ArcStageMap | undefined {
  return stageMaps.find((map) => map.arc_id === arcId);
}

/**
 * Get selected arc for a project
 */
export function getSelectedArc(selections: ArcSelection[], projectId: string): ArcCandidate | null {
  const projectSelection = selections.find((s) => s.project_id === projectId);
  return projectSelection?.selected_arc || null;
}

/**
 * Check if an arc candidate has been selected
 */
export function isArcSelected(
  selections: ArcSelection[],
  arcId: string,
): boolean {
  return selections.some((s) => s.selected_arc.arc_id === arcId);
}

/**
 * Check if an arc candidate has been rejected
 */
export function isArcRejected(
  selections: ArcSelection[],
  arcId: string,
): boolean {
  return selections.some((s) => s.rejected_arc_ids.includes(arcId));
}

/**
 * Get arc candidates grouped by selection status
 */
export function groupArcsByStatus(
  candidates: ArcCandidate[],
  selections: ArcSelection[],
): {
  selected: ArcCandidate[];
  rejected: ArcCandidate[];
  pending: ArcCandidate[];
} {
  const selectedArcIds = new Set(
    selections.map((s) => s.selected_arc.arc_id),
  );
  const rejectedArcIds = new Set(
    selections.flatMap((s) => s.rejected_arc_ids),
  );

  return {
    selected: candidates.filter((c) => selectedArcIds.has(c.arc_id)),
    rejected: candidates.filter((c) => rejectedArcIds.has(c.arc_id)),
    pending: candidates.filter(
      (c) => !selectedArcIds.has(c.arc_id) && !rejectedArcIds.has(c.arc_id),
    ),
  };
}
