import type { ReviewDecision } from '../../types/review';

export async function createMockDecision(
  decision: Omit<ReviewDecision, 'decision_id'>
): Promise<ReviewDecision> {
  await new Promise((resolve) => setTimeout(resolve, 2000));

  return {
    ...decision,
    decision_id: `mock-decision-${Date.now()}`,
  };
}
