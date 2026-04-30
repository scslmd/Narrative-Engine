import { describe, it, expect } from 'vitest';
import { server } from '../__tests__/setup';
import { http, HttpResponse } from 'msw';
import { getBranches, setActiveBranch, createBranchComparison, createMergeDecision } from './branches';

const mockBranch = {
  branch_id: 'branch-1',
  project_id: 'proj-1',
  parent_branch_id: null,
  state: 'active' as const,
};

describe('branches service', () => {
  describe('getBranches', () => {
    it('returns list of branches for a project', async () => {
      server.use(
        http.get('/story-development/branches', ({ request }) => {
          const url = new URL(request.url);
          expect(url.searchParams.get('project_id')).toBe('proj-1');
          return HttpResponse.json({
            project_id: 'proj-1',
            items: [mockBranch],
            meta: {},
          });
        }),
      );

      const result = await getBranches('proj-1');

      expect(result).toHaveLength(1);
      expect(result[0].branch_id).toBe('branch-1');
    });

    it('throws on error response', async () => {
      server.use(
        http.get('/story-development/branches', () => {
          return HttpResponse.json({ detail: 'Not found' }, { status: 404 });
        }),
      );

      await expect(getBranches('proj-missing')).rejects.toThrow();
    });
  });

  describe('setActiveBranch', () => {
    it('sets the active branch (200)', async () => {
      server.use(
        http.post('/story-development/branches/active', () => {
          return HttpResponse.json({ ...mockBranch, branch_id: 'branch-2' });
        }),
      );

      const result = await setActiveBranch('proj-1', 'branch-2');

      expect(result.branch_id).toBe('branch-2');
    });

    it('throws on error response', async () => {
      server.use(
        http.post('/story-development/branches/active', () => {
          return HttpResponse.json({ detail: 'Bad request' }, { status: 400 });
        }),
      );

      await expect(setActiveBranch('proj-1', 'branch-bad')).rejects.toThrow();
    });
  });

  describe('createBranchComparison', () => {
    it('creates a branch comparison (201)', async () => {
      server.use(
        http.post('/story-development/branches/comparisons', () => {
          return HttpResponse.json({
            comparison_id: 'comp-1',
            source_branch_id: 'branch-a',
            target_branch_id: 'branch-b',
          }, { status: 201 });
        }),
      );

      const result = await createBranchComparison('proj-1', 'branch-a', 'branch-b');

      expect(result.source_branch_id).toBe('branch-a');
    });

    it('throws on error response', async () => {
      server.use(
        http.post('/story-development/branches/comparisons', () => {
          return HttpResponse.json({ detail: 'Conflict' }, { status: 409 });
        }),
      );

      await expect(createBranchComparison('proj-1', 'branch-a', 'branch-b')).rejects.toThrow();
    });
  });

  describe('createMergeDecision', () => {
    it('creates a merge decision (201)', async () => {
      server.use(
        http.post('/story-development/branches/merge-decisions', () => {
          return HttpResponse.json({
            merge_decision_id: 'merge-1',
            merge_rationale: 'because',
          }, { status: 201 });
        }),
      );

      const result = await createMergeDecision('proj-1', 'branch-a', 'branch-b', 'because');

      expect(result.merge_rationale).toBe('because');
    });

    it('throws on error response', async () => {
      server.use(
        http.post('/story-development/branches/merge-decisions', () => {
          return HttpResponse.json({ detail: 'Conflict' }, { status: 409 });
        }),
      );

      await expect(createMergeDecision('proj-1', 'branch-a', 'branch-b', 'because')).rejects.toThrow();
    });
  });
});
