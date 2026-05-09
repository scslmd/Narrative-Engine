import { describe, it, expect } from 'vitest';
import { server } from '../__tests__/setup';
import { http, HttpResponse } from 'msw';
import {
  getCharacters,
  createCharacter,
  updateCharacter,
  getCharacter,
  getCharacterRelationships,
} from './characters';

const mockCharacter = {
  character_id: 'char-1',
  project_id: 'proj-1',
  display_name: 'Test Character',
  role_in_story: 'protagonist',
  archetype: 'hero',
  external_goal: 'Save the world',
  internal_need: 'Find self-worth',
  misbelief_or_wound: 'I am not enough',
  core_fear: 'Abandonment',
  primary_strength: 'Courage',
  fatal_flaw_or_limitation: 'Pride',
  contradictions: [],
  backstory_summary: 'A test backstory',
  voice_notes: 'Test voice',
  relationship_edges: [],
  secrets: [],
  values: [],
  taboos: [],
  change_axis: 'growth',
  arc_stage_notes: [],
  continuity_facts: [],
  writer_notes: null,
};

describe('characters service', () => {
  describe('getCharacters', () => {
    it('returns list of characters for a project', async () => {
      server.use(
        http.get('/v1/story-development/characters', ({ request }) => {
          const url = new URL(request.url);
          expect(url.searchParams.get('project_id')).toBe('proj-1');
          return HttpResponse.json({
            project_id: 'proj-1',
            items: [mockCharacter],
            meta: {},
          });
        }),
      );

      const result = await getCharacters('proj-1');

      expect(result).toHaveLength(1);
      expect(result[0].character_id).toBe('char-1');
    });

    it('throws on error response', async () => {
      server.use(
        http.get('/v1/story-development/characters', () => {
          return HttpResponse.json({ detail: 'Not found' }, { status: 404 });
        }),
      );

      await expect(getCharacters('proj-missing')).rejects.toThrow();
    });
  });

  describe('createCharacter', () => {
    it('creates a character profile (201)', async () => {
      server.use(
        http.post('/v1/story-development/characters', () => {
          return HttpResponse.json({ ...mockCharacter, display_name: 'New Character' }, { status: 201 });
        }),
      );

      const result = await createCharacter({
        project_id: 'proj-1',
        character_id: 'char-new',
        display_name: 'New Character',
        role_in_story: 'antagonist',
        archetype: 'villain',
        external_goal: 'Destroy the world',
        internal_need: 'Find purpose',
        misbelief_or_wound: 'I am powerless',
        core_fear: 'Irrelevance',
        primary_strength: 'Intelligence',
        fatal_flaw_or_limitation: 'Arrogance',
        backstory_summary: 'A villain backstory',
        voice_notes: 'Cold and calculated',
        change_axis: 'decline',
      });

      expect(result.display_name).toBe('New Character');
    });

    it('throws on error response', async () => {
      server.use(
        http.post('/v1/story-development/characters', () => {
          return HttpResponse.json({ detail: 'Bad request' }, { status: 400 });
        }),
      );

      await expect(createCharacter({
        project_id: 'proj-1',
        character_id: 'char-bad',
        display_name: '',
        role_in_story: '',
        archetype: '',
        external_goal: '',
        internal_need: '',
        misbelief_or_wound: '',
        core_fear: '',
        primary_strength: '',
        fatal_flaw_or_limitation: '',
        backstory_summary: '',
        voice_notes: '',
        change_axis: '',
      })).rejects.toThrow();
    });
  });

  describe('updateCharacter', () => {
    it('updates a character profile (200)', async () => {
      server.use(
        http.patch('/v1/story-development/characters/char-1', () => {
          return HttpResponse.json({ ...mockCharacter, display_name: 'Updated Name' });
        }),
      );

      const result = await updateCharacter('char-1', 'proj-1', { display_name: 'Updated Name' });

      expect(result.display_name).toBe('Updated Name');
    });

    it('throws on error response', async () => {
      server.use(
        http.patch('/v1/story-development/characters/char-missing', () => {
          return HttpResponse.json({ detail: 'Not found' }, { status: 404 });
        }),
      );

      await expect(updateCharacter('char-missing', 'proj-1', {})).rejects.toThrow();
    });
  });

  describe('getCharacter', () => {
    it('returns a single character profile by id', async () => {
      server.use(
        http.get('/v1/story-development/characters/char-1', ({ request }) => {
          const url = new URL(request.url);
          expect(url.searchParams.get('project_id')).toBe('proj-1');
          return HttpResponse.json(mockCharacter);
        }),
      );

      const result = await getCharacter('char-1', 'proj-1');

      expect(result.character_id).toBe('char-1');
      expect(result.display_name).toBe('Test Character');
    });

    it('throws on error response', async () => {
      server.use(
        http.get('/v1/story-development/characters/char-missing', () => {
          return HttpResponse.json({ detail: 'Not found' }, { status: 404 });
        }),
      );

      await expect(getCharacter('char-missing', 'proj-1')).rejects.toThrow();
    });
  });

  describe('getCharacterRelationships', () => {
    it('returns relationships for a character', async () => {
      const mockEdges = [
        {
          edge_id: 'edge-1',
          source_character_id: 'char-1',
          target_character_id: 'char-2',
          relation_kind: 'rivalry',
          summary: 'Long-standing rivalry',
          tension: 'high',
          notes: null,
        },
        {
          edge_id: 'edge-2',
          source_character_id: 'char-1',
          target_character_id: 'char-3',
          relation_kind: 'mentorship',
          summary: 'Mentor-student bond',
          tension: null,
          notes: 'Developed in chapter 3',
        },
      ];

      server.use(
        http.get('/v1/story-development/characters/char-1/relationships', ({ request }) => {
          const url = new URL(request.url);
          expect(url.searchParams.get('project_id')).toBe('proj-1');
          return HttpResponse.json({
            project_id: 'proj-1',
            items: mockEdges,
            meta: {},
          });
        }),
      );

      const result = await getCharacterRelationships('char-1', 'proj-1');

      expect(result).toHaveLength(2);
      expect(result[0].edge_id).toBe('edge-1');
      expect(result[0].relation_kind).toBe('rivalry');
      expect(result[1].edge_id).toBe('edge-2');
      expect(result[1].notes).toBe('Developed in chapter 3');
    });

    it('returns empty array when character has no relationships', async () => {
      server.use(
        http.get('/v1/story-development/characters/char-solo/relationships', ({ request }) => {
          const url = new URL(request.url);
          expect(url.searchParams.get('project_id')).toBe('proj-1');
          return HttpResponse.json({
            project_id: 'proj-1',
            items: [],
            meta: {},
          });
        }),
      );

      const result = await getCharacterRelationships('char-solo', 'proj-1');

      expect(result).toHaveLength(0);
    });

    it('throws on error response', async () => {
      server.use(
        http.get('/v1/story-development/characters/char-missing/relationships', () => {
          return HttpResponse.json({ detail: 'Not found' }, { status: 404 });
        }),
      );

      await expect(getCharacterRelationships('char-missing', 'proj-1')).rejects.toThrow();
    });
  });
});

