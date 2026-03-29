/**
 * Brainstorm Types
 * 
 * Types for brainstorm items and promotions.
 * Backend schema: app.schemas.story_development.BrainstormItem
 * 
 * Note: The backend uses 'status' but frontend components expect 'state' and 'item_type'.
 * These are mapped for compatibility.
 */

export type BrainstormItemType = 'IDEA' | 'CHARACTER' | 'SETTING' | 'PLOT_POINT' | 'THEME' | 'QUESTION';
export type BrainstormItemState = 'KEEP' | 'DISCARD' | 'PARK';

export interface BrainstormItem {
  item_id: string;
  project_id: string;
  content: string;
  status: string; // Backend field - maps to 'state' in frontend
  state: BrainstormItemState; // Frontend alias for 'status'
  item_type: BrainstormItemType; // Frontend field for categorization
  tags: string[];
  cluster_id: string | null;
  promoted_to: string | null;
  promoted_at: string | null;
  created_at: string;
  source_notes: string | null;
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
  status?: string;
  state?: BrainstormItemState;
  item_type?: BrainstormItemType;
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

export interface BrainstormPromotionListResponse {
  project_id: string;
  items: BrainstormPromotion[];
  meta: Record<string, string>;
}
