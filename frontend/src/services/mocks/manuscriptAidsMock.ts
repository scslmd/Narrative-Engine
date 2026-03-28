import type { RevisionSuggestion } from '../../types/drafting';

const MOCK_DELAY = 2000;

export interface ManuscriptAidRequest {
  project_id: string;
  target_document_id: string;
  source_text: string;
  action: 'rewrite' | 'summarize' | 'expand' | 'clarify' | 'tone-adjust';
  guidance?: string;
}

export async function requestManuscriptAid(
  request: ManuscriptAidRequest,
): Promise<RevisionSuggestion> {
  await new Promise((resolve) => setTimeout(resolve, MOCK_DELAY));

  const { project_id, target_document_id, source_text, action } = request;

  const actionPrefixes: Record<string, string> = {
    rewrite: 'Rewritten version that improves clarity and flow:',
    summarize: 'Concise summary capturing the key points:',
    expand: 'Expanded version with additional detail and context:',
    clarify: 'Clarified version with improved precision:',
    'tone-adjust': 'Adjusted tone while preserving meaning:',
  };

  const prefix = actionPrefixes[action] || 'Suggested revision:';

  return {
    suggestion_id: crypto.randomUUID(),
    project_id,
    target_document_id,
    source_text,
    proposed_text: `${prefix} ${source_text} [mock ${action} result]`,
    rationale: `Automated suggestion for ${action} action`,
    source_context: [],
    status: 'REQUESTED',
  };
}
