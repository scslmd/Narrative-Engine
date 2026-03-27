import type { DraftArtifact } from '../../types/drafting';

const MOCK_DELAY = 2000;

export async function getDraftArtifacts(_projectId: string): Promise<DraftArtifact[]> {
  await new Promise((resolve) => setTimeout(resolve, MOCK_DELAY / 2));
  
  return [
    {
      artifact_id: 'draft-001',
      project_id: 'project-1',
      title: 'Chapter 1 - The Beginning',
      content: 'The sun rose over the horizon, casting golden light across the valley. It was a new day, and with it came new possibilities...',
      source_plan_ids: [],
      source_context: [],
      provenance_note: null,
      status: 'DRAFT',
    },
    {
      artifact_id: 'draft-002',
      project_id: 'project-1',
      title: 'Chapter 2 - The Journey Begins',
      content: 'She packed her bags with care, each item chosen deliberately. This journey would change everything...',
      source_plan_ids: [],
      source_context: [],
      provenance_note: null,
      status: 'PROPOSED',
    },
  ];
}

export interface PromotedManuscript {
  document_id: string;
  title: string;
  content: string;
  provenance: {
    artifact_id: string;
    provider?: string;
    model?: string;
  };
}

export async function promoteDraft(artifactId: string): Promise<PromotedManuscript> {
  await new Promise((resolve) => setTimeout(resolve, MOCK_DELAY));
  
  const artifacts = await getDraftArtifacts('project-1');
  const artifact = artifacts.find((a) => a.artifact_id === artifactId);
  
  if (!artifact) {
    throw new Error(`Artifact ${artifactId} not found`);
  }

  return {
    document_id: `doc-${Date.now()}`,
    title: `${artifact.title} (Promoted)`,
    content: artifact.content,
    provenance: {
      artifact_id: artifact.artifact_id,
    },
  };
}
