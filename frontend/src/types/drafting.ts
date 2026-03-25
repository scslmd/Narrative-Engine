export interface DraftArtifact {
  id: string;
  title: string;
  state: 'DRAFT' | 'REVIEW' | 'APPROVED';
  provider: string;
  model: string;
  content: string;
  created_at: string;
}

export interface PromotedManuscript {
  document_id: string;
  title: string;
  content: string;
  provenance: {
    artifact_id: string;
    provider: string;
    model: string;
  };
}
