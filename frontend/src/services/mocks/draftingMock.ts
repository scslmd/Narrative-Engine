import type { DraftArtifact, PromotedManuscript } from '../types/drafting';

const MOCK_DELAY = 2000;

export async function getDraftArtifacts(projectId: string): Promise<DraftArtifact[]> {
  await new Promise((resolve) => setTimeout(resolve, MOCK_DELAY / 2));
  
  return [
    {
      id: 'draft-001',
      title: 'Chapter 1 - The Beginning',
      state: 'DRAFT',
      provider: 'openai',
      model: 'gpt-4-turbo',
      content: 'The sun rose over the horizon, casting golden light across the valley. It was a new day, and with it came new possibilities...',
      created_at: new Date().toISOString(),
    },
    {
      id: 'draft-002',
      title: 'Chapter 2 - The Journey Begins',
      state: 'REVIEW',
      provider: 'anthropic',
      model: 'claude-3-opus',
      content: 'She packed her bags with care, each item chosen deliberately. This journey would change everything...',
      created_at: new Date(Date.now() - 86400000).toISOString(),
    },
  ];
}

export async function promoteDraft(artifactId: string): Promise<PromotedManuscript> {
  await new Promise((resolve) => setTimeout(resolve, MOCK_DELAY));
  
  const artifact = (await getDraftArtifacts('project-1')).find((a) => a.id === artifactId);
  
  if (!artifact) {
    throw new Error(`Artifact ${artifactId} not found`);
  }

  return {
    document_id: `doc-${Date.now()}`,
    title: `${artifact.title} (Promoted)`,
    content: artifact.content,
    provenance: {
      artifact_id: artifact.id,
      provider: artifact.provider,
      model: artifact.model,
    },
  };
}
