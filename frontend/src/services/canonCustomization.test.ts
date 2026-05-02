import { describe, expect, it } from 'vitest';
import { http, HttpResponse } from 'msw';
import { server } from '../__tests__/setup';
import {
  createCanonAnnotation,
  createCanonProfile,
  deleteCanonAnnotation,
  deleteCanonProfile,
  getCanonAnnotations,
  getCanonProfiles,
  previewCanonProfilePacket,
  updateCanonProfile,
} from './canonCustomization';

describe('canonCustomization service', () => {
  it('supports annotation and profile CRUD plus preview', async () => {
    server.use(
      http.get('/v1/canon/annotations', () => HttpResponse.json([])),
      http.post('/v1/canon/annotations', () =>
        HttpResponse.json(
          {
            annotation_id: 'ann-1',
            project_id: 'project-1',
            target_kind: 'character',
            target_id: 'char-1',
            field_path: 'voice_notes',
            annotation_kind: 'locked',
            note: '',
            applies_to_modes: [],
          },
          { status: 201 },
        ),
      ),
      http.delete('/v1/canon/annotations/ann-1', () => new HttpResponse(null, { status: 200 })),
      http.get('/v1/canon/profiles', () => HttpResponse.json([])),
      http.post('/v1/canon/profiles', () =>
        HttpResponse.json(
          {
            profile_id: 'profile-1',
            project_id: 'project-1',
            name: 'Default',
            description: '',
            default_generation_mode: 'same_project_side_story',
            canon_scope: {
              source_project_id: 'project-1',
              scope_mode: 'selected',
              character_ids: ['char-1'],
              world_bible_refs: [],
              continuity_thread_ids: [],
              arc_ids: [],
              mythos_ids: [],
              pattern_ids: [],
              include_relationships: true,
              include_unresolved_questions: true,
              include_contradictions_as_forbidden: true,
            },
            canon_policy: {
              locked_character_fields: [],
              locked_world_fields: [],
              allowed_character_changes: [],
              allowed_world_changes: [],
              forbidden_contradictions: [],
              continuity_strictness: 'repair_once',
            },
            generation_brief_template: 'brief',
            selected_annotation_ids: [],
            status: 'draft',
          },
          { status: 201 },
        ),
      ),
      http.patch('/v1/canon/profiles/profile-1', () =>
        HttpResponse.json(
          {
            profile_id: 'profile-1',
            project_id: 'project-1',
            name: 'Updated',
            description: '',
            default_generation_mode: 'same_project_side_story',
            canon_scope: {
              source_project_id: 'project-1',
              scope_mode: 'selected',
              character_ids: ['char-1'],
              world_bible_refs: [],
              continuity_thread_ids: [],
              arc_ids: [],
              mythos_ids: [],
              pattern_ids: [],
              include_relationships: true,
              include_unresolved_questions: true,
              include_contradictions_as_forbidden: true,
            },
            canon_policy: {
              locked_character_fields: [],
              locked_world_fields: [],
              allowed_character_changes: [],
              allowed_world_changes: [],
              forbidden_contradictions: [],
              continuity_strictness: 'repair_once',
            },
            generation_brief_template: 'brief',
            selected_annotation_ids: [],
            status: 'draft',
          },
        ),
      ),
      http.delete('/v1/canon/profiles/profile-1', () => new HttpResponse(null, { status: 200 })),
      http.post('/v1/canon/profiles/profile-1/packet-preview', () =>
        HttpResponse.json({ packet_id: 'packet-1' }),
      ),
    );

    expect((await getCanonAnnotations('project-1')).length).toBe(0);
    expect((await createCanonAnnotation({
      project_id: 'project-1',
      target_kind: 'character',
      target_id: 'char-1',
      field_path: 'voice_notes',
      annotation_kind: 'locked',
    })).annotation_id).toBe('ann-1');
    await deleteCanonAnnotation('project-1', 'ann-1');
    expect((await getCanonProfiles('project-1')).length).toBe(0);
    expect((await createCanonProfile({
      project_id: 'project-1',
      name: 'Default',
      canon_scope: {
        source_project_id: 'project-1',
        scope_mode: 'selected',
        character_ids: ['char-1'],
        world_bible_refs: [],
        continuity_thread_ids: [],
        arc_ids: [],
        mythos_ids: [],
        pattern_ids: [],
        include_relationships: true,
        include_unresolved_questions: true,
        include_contradictions_as_forbidden: true,
      },
    })).profile_id).toBe('profile-1');
    expect((await updateCanonProfile('profile-1', 'project-1', { name: 'Updated' })).name).toBe('Updated');
    await deleteCanonProfile('project-1', 'profile-1');
    expect((await previewCanonProfilePacket('project-1', 'profile-1')).packet_id).toBe('packet-1');
  });
});
