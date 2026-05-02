import type { CanonGenerationPacket, CanonPolicy, CanonScope, GenerationMode } from './storyGeneration';

export type CanonTargetKind =
  | 'character'
  | 'relationship'
  | 'world_bible'
  | 'mythos'
  | 'pattern'
  | 'continuity'
  | 'foundation';

export type CanonAnnotationKind =
  | 'locked'
  | 'soft_guidance'
  | 'mutable'
  | 'forbidden_contradiction'
  | 'generation_note';

export type CanonProfileStatus = 'draft' | 'active' | 'archived';

export interface CanonAnnotation {
  annotation_id: string;
  project_id: string;
  target_kind: CanonTargetKind;
  target_id: string;
  field_path: string;
  annotation_kind: CanonAnnotationKind;
  note: string;
  applies_to_modes: string[];
  created_at?: string | null;
  updated_at?: string | null;
}

export interface CanonAnnotationCreateRequest {
  project_id: string;
  target_kind: CanonTargetKind;
  target_id: string;
  field_path: string;
  annotation_kind: CanonAnnotationKind;
  note?: string;
  applies_to_modes?: string[];
}

export interface CanonCustomizationProfile {
  profile_id: string;
  project_id: string;
  name: string;
  description: string;
  default_generation_mode: GenerationMode;
  canon_scope: CanonScope;
  canon_policy: CanonPolicy;
  generation_brief_template: string;
  selected_annotation_ids: string[];
  status: CanonProfileStatus;
}

export interface CanonCustomizationProfileCreateRequest {
  project_id: string;
  name: string;
  description?: string;
  default_generation_mode?: GenerationMode;
  canon_scope: CanonScope;
  canon_policy?: CanonPolicy;
  generation_brief_template?: string;
  selected_annotation_ids?: string[];
  status?: CanonProfileStatus;
}

export interface CanonCustomizationProfileUpdateRequest {
  name?: string;
  description?: string;
  default_generation_mode?: GenerationMode;
  canon_scope?: CanonScope;
  canon_policy?: CanonPolicy;
  generation_brief_template?: string;
  selected_annotation_ids?: string[];
  status?: CanonProfileStatus;
}

export interface CanonAnnotationFilters {
  target_kind?: CanonTargetKind;
  target_id?: string;
}

export interface CanonProfilePacketPreview {
  profile: CanonCustomizationProfile;
  packet: CanonGenerationPacket;
}
