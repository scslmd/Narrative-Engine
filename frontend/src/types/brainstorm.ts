/**
 * Brainstorm Types
 *
 * Types for brainstorm items and promotions.
 * Backend schema: app.schemas.story_development.BrainstormItem
 */

import type { BrainstormItemType } from './braindump';

export type BrainstormItemStatus = 'keep' | 'discard' | 'park';

/**
 * Legacy uppercase alias kept for mock compatibility.
 */
export type BrainstormItemState = 'KEEP' | 'DISCARD' | 'PARK';

export interface BrainstormItem {
  item_id: string;
  project_id: string;
  content: string;
  status: BrainstormItemStatus;
  tags: string[];
  source_notes: string | null;
  state?: BrainstormItemState;
  item_type: BrainstormItemType | null;
  cluster_id?: string | null;
  promoted_to?: string | null;
  promoted_at?: string | null;
  created_at?: string;
}

export interface BrainstormPromotion {
  promotion_id: string;
  project_id: string;
  source_item_ids: string[];
  target_object_kind: string;
  target_object_id: string;
  notes: string | null;
}

export interface BrainstormItemCreateRequest {
  project_id: string;
  content: string;
  status?: BrainstormItemStatus;
  state?: BrainstormItemState;
  item_type?: BrainstormItemType | null;
  cluster_key?: string | null;
  cluster_id?: string | null;
  tags?: string[];
  source_artifact_refs?: string[];
}

export interface BrainstormItemClusterRequest {
  project_id: string;
  item_ids: string[];
  cluster_key?: string | null;
}

export interface BrainstormItemPromoteRequest {
  project_id: string;
  item_id: string;
  target_object_kind: string;
  target_object_id: string;
  notes?: string | null;
}

// Legacy type for backward compatibility
export type BrainstormClusterRequest = BrainstormItemClusterRequest;

// Response wrappers
export interface BrainstormItemListResponse {
  project_id: string;
  items: BrainstormItem[];
  meta: Record<string, string>;
}

export interface BrainstormPromotionResult {
  promoted_to: string;
  target_id: string;
}

export interface BrainstormPromotionListResponse {
  project_id: string;
  items: BrainstormPromotion[];
  meta: Record<string, string>;
}
