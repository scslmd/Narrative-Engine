export type EntityTypeName = 'character' | 'relationship' | 'world_bible';
export type DedupActionType = 'new' | 'exact_merge' | 'fuzzy_merge' | 'enrich';
export type JobStatusType = 'pending' | 'chunking' | 'extracting' | 'deduplicating' | 'staging' | 'completed' | 'failed';

export interface CascadeScanRequest {
  project_id: string;
  manuscript_text: string;
  chunk_size?: number;
  include_types?: EntityTypeName[];
}

export interface CascadeJobResponse {
  job_id: string;
  status: JobStatusType;
  phase: JobStatusType;
  chunk_index: number | null;
  total_chunks: number | null;
  stage_id: string | null;
  error: string | null;
}

export interface StagedEntity {
  entity_id: string;
  entity_type: EntityTypeName;
  entity_json: Record<string, unknown>;
  confidence: number;
  source_excerpt: string | null;
  approved: boolean;
  dedup_action: DedupActionType;
}

export interface StagedEntitiesResponse {
  stage_id: string;
  project_id: string;
  characters: StagedEntity[];
  relationships: StagedEntity[];
  world_bible: StagedEntity[];
}

export interface CascadeApplyResponse {
  characters_added: number;
  relationships_added: number;
  world_bible_added: number;
  characters_enriched: number;
}

export interface EntityApprovalUpdate {
  entity_id: string;
  approved: boolean;
}
