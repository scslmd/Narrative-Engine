# Backend API Reference

This file is the current route reference for the checked-in backend.

## Versioning Reality

The server currently exposes a mixed surface:

- Versioned routes under `/v1` for jobs, models, story-development, and role-model-checker APIs.
- Unversioned routes for projects, auth, backup, and health.
- Story Development router is mounted at both `/story-development` and `/v1/story-development`.

## Unversioned Routes

### Projects

| Method | Endpoint |
|--------|----------|
| `GET` | `/projects` |
| `POST` | `/projects/create` |
| `GET` | `/projects/{project_id}` |
| `GET` | `/projects/{project_id}/manifest` |
| `GET` | `/projects/{project_id}/sequence` |
| `GET` | `/projects/{project_id}/chapter-1` |
| `POST` | `/projects/import-story` |

### Authentication

| Method | Endpoint |
|--------|----------|
| `POST` | `/auth/keys` |
| `GET` | `/auth/keys` |
| `DELETE` | `/auth/keys/{prefix}` |

### Backup

| Method | Endpoint |
|--------|----------|
| `POST` | `/backup/create` |
| `POST` | `/backup/restore/{backup_id}` |
| `GET` | `/backup/list` |
| `GET` | `/backup/latest` |
| `DELETE` | `/backup/{backup_id}` |

### Health

| Method | Endpoint |
|--------|----------|
| `GET` | `/health/` |
| `GET` | `/health/ready` |
| `GET` | `/health/metrics` |

## Versioned Routes

### Models

| Method | Endpoint |
|--------|----------|
| `GET` | `/v1/models` |

### Jobs

| Method | Endpoint |
|--------|----------|
| `POST` | `/v1/jobs/create` |
| `GET` | `/v1/jobs/{job_id}/status` |
| `GET` | `/v1/jobs/{job_id}/logs` |
| `GET` | `/v1/jobs/{job_id}/steps` |
| `GET` | `/v1/jobs/{job_id}/lineage` |
| `GET` | `/v1/jobs/{job_id}/attempts` |
| `POST` | `/v1/jobs/{job_id}/retry` |

### Role Model Checker

| Method | Endpoint |
|--------|----------|
| `POST` | `/v1/role-model-checker/run` |
| `POST` | `/v1/role-model-checker/start` |
| `GET` | `/v1/role-model-checker/{run_id}/status` |
| `GET` | `/v1/role-model-checker/{run_id}/steps` |
| `GET` | `/v1/role-model-checker/{run_id}/lineage` |
| `GET` | `/v1/role-model-checker/{run_id}/attempts` |
| `POST` | `/v1/role-model-checker/{run_id}/retry` |

### Story Development

#### Branching

| Method | Endpoint |
|--------|----------|
| `GET` | `/v1/story-development/branches` |
| `POST` | `/v1/story-development/branches` |
| `GET` | `/v1/story-development/branches/active` |
| `POST` | `/v1/story-development/branches/active` |
| `POST` | `/v1/story-development/branches/comparisons` |
| `GET` | `/v1/story-development/branches/comparisons` |
| `GET` | `/v1/story-development/branches/comparisons/{comparison_id}` |
| `POST` | `/v1/story-development/branches/merge-decisions` |
| `GET` | `/v1/story-development/branches/merge-decisions` |
| `GET` | `/v1/story-development/branches/merge-decisions/{merge_decision_id}` |
| `GET` | `/v1/story-development/branches/{branch_id}/state-refs` |
| `GET` | `/v1/story-development/branches/{branch_id}` |

#### Flow

| Method | Endpoint |
|--------|----------|
| `POST` | `/v1/story-development/flow/stages/init` |
| `GET` | `/v1/story-development/flow/stages` |
| `POST` | `/v1/story-development/flow/stages` |
| `PATCH` | `/v1/story-development/flow/stages/{stage_id}` |
| `POST` | `/v1/story-development/flow/stages/reorder` |
| `DELETE` | `/v1/story-development/flow/stages/{stage_id}` |

#### Decisions And Review

| Method | Endpoint |
|--------|----------|
| `GET` | `/v1/story-development/decisions` |
| `GET` | `/v1/story-development/decisions/{node_id}` |
| `GET` | `/v1/story-development/decisions/{node_id}/path` |
| `GET` | `/v1/story-development/review/findings` |
| `GET` | `/v1/story-development/review/findings/{finding_id}` |
| `GET` | `/v1/story-development/review/decisions` |
| `GET` | `/v1/story-development/review/decisions/{decision_id}` |
| `POST` | `/v1/story-development/review/decisions` |
| `GET` | `/v1/story-development/review/inspect-links` |
| `GET` | `/v1/story-development/review/inspect-links/{link_id}` |

#### Planning

| Method | Endpoint |
|--------|----------|
| `GET` | `/v1/story-development/planning/sequence-plans` |
| `GET` | `/v1/story-development/planning/sequence-plans/{sequence_id}` |
| `POST` | `/v1/story-development/planning/sequence-plans` |
| `PATCH` | `/v1/story-development/planning/sequence-plans/{sequence_id}` |
| `GET` | `/v1/story-development/planning/chapter-plans` |
| `GET` | `/v1/story-development/planning/chapter-plans/{chapter_id}` |
| `POST` | `/v1/story-development/planning/chapter-plans` |
| `PATCH` | `/v1/story-development/planning/chapter-plans/{chapter_id}` |
| `GET` | `/v1/story-development/planning/scene-plans` |
| `GET` | `/v1/story-development/planning/scene-plans/{scene_id}` |
| `POST` | `/v1/story-development/planning/scene-plans` |
| `PATCH` | `/v1/story-development/planning/scene-plans/{scene_id}` |
| `GET` | `/v1/story-development/planning/beat-plans` |
| `GET` | `/v1/story-development/planning/beat-plans/{beat_id}` |
| `POST` | `/v1/story-development/planning/beat-plans` |
| `PATCH` | `/v1/story-development/planning/beat-plans/{beat_id}` |
| `GET` | `/v1/story-development/planning/dependencies` |
| `GET` | `/v1/story-development/planning/dependencies/{dependency_id}` |
| `GET` | `/v1/story-development/planning/chapter-packets` |
| `GET` | `/v1/story-development/planning/chapter-packets/{packet_id}` |
| `POST` | `/v1/story-development/planning/chapter-packets` |
| `PATCH` | `/v1/story-development/planning/chapter-packets/{packet_id}` |
| `POST` | `/v1/story-development/planning/reorder` |

#### Drafting

| Method | Endpoint |
|--------|----------|
| `GET` | `/v1/story-development/drafting/draft-artifacts` |
| `GET` | `/v1/story-development/drafting/draft-artifacts/{artifact_id}` |
| `POST` | `/v1/story-development/drafting/draft-artifacts/continue` |
| `POST` | `/v1/story-development/drafting/draft-artifacts/alternate-variant` |
| `GET` | `/v1/story-development/drafting/manuscript-documents` |
| `GET` | `/v1/story-development/drafting/manuscript-documents/{document_id}` |
| `POST` | `/v1/story-development/drafting/manuscript-documents` |
| `PATCH` | `/v1/story-development/drafting/manuscript-documents/{document_id}` |
| `POST` | `/v1/story-development/drafting/manuscript-documents/{document_id}/review` |
| `GET` | `/v1/story-development/drafting/revision-suggestions` |
| `GET` | `/v1/story-development/drafting/revision-suggestions/{suggestion_id}` |
| `POST` | `/v1/story-development/drafting/revision-suggestions` |
| `POST` | `/v1/story-development/drafting/promote-draft` |

#### Brainstorm

| Method | Endpoint |
|--------|----------|
| `GET` | `/v1/story-development/brainstorm/items` |
| `POST` | `/v1/story-development/brainstorm/items` |
| `POST` | `/v1/story-development/brainstorm/items/cluster` |
| `POST` | `/v1/story-development/brainstorm/items/promote` |
| `GET` | `/v1/story-development/brainstorm/promotions` |

#### Braindump

| Method | Endpoint |
|--------|----------|
| `POST` | `/v1/story-development/braindump/sessions` |
| `GET` | `/v1/story-development/braindump/sessions` |
| `GET` | `/v1/story-development/braindump/sessions/{session_id}` |
| `PATCH` | `/v1/story-development/braindump/sessions/{session_id}` |
| `DELETE` | `/v1/story-development/braindump/sessions/{session_id}` |
| `POST` | `/v1/story-development/braindump/sessions/{session_id}/organize` |

#### Foundation

| Method | Endpoint |
|--------|----------|
| `GET` | `/v1/story-development/foundation` |
| `POST` | `/v1/story-development/foundation` |
| `PATCH` | `/v1/story-development/foundation` |
| `GET` | `/v1/story-development/foundation/revisions` |
| `GET` | `/v1/story-development/foundation/review-cues` |

#### Characters

| Method | Endpoint |
|--------|----------|
| `GET` | `/v1/story-development/characters` |
| `GET` | `/v1/story-development/characters/{character_id}` |
| `POST` | `/v1/story-development/characters` |
| `PATCH` | `/v1/story-development/characters/{character_id}` |
| `GET` | `/v1/story-development/characters/{character_id}/relationships` |
| `POST` | `/v1/story-development/relationships` |
| `GET` | `/v1/story-development/relationships` |
| `PATCH` | `/v1/story-development/relationships/{edge_id}` |
| `DELETE` | `/v1/story-development/relationships/{edge_id}` |

#### World Bible And Arcs

| Method | Endpoint |
|--------|----------|
| `GET` | `/v1/story-development/world-bible` |
| `GET` | `/v1/story-development/world-bible/{entry_type}/{title}` |
| `POST` | `/v1/story-development/world-bible` |
| `PATCH` | `/v1/story-development/world-bible/{entry_type}/{title}` |
| `GET` | `/v1/story-development/arcs/candidates` |
| `POST` | `/v1/story-development/arcs/candidates` |
| `GET` | `/v1/story-development/arcs/selections` |
| `POST` | `/v1/story-development/arcs/selections` |
| `PATCH` | `/v1/story-development/arcs/selections/{selection_id}` |
| `DELETE` | `/v1/story-development/arcs/selections/{selection_id}` |
| `GET` | `/v1/story-development/arcs/stage-maps` |
| `POST` | `/v1/story-development/arcs/stage-maps` |
| `POST` | `/v1/story-development/arcs/comparisons` |

#### Storyboard Cards

| Method | Endpoint |
|--------|----------|
| `GET` | `/v1/story-development/storyboard/cards` |
| `GET` | `/v1/story-development/storyboard/cards/{card_id}` |
| `POST` | `/v1/story-development/storyboard/cards` |
| `PATCH` | `/v1/story-development/storyboard/cards/{card_id}` |
| `PUT` | `/v1/story-development/storyboard/cards/{card_id}` |
| `DELETE` | `/v1/story-development/storyboard/cards/{card_id}` |
| `PUT` | `/v1/story-development/storyboard/cards/{column_id}/reindex` |

## Source Of Truth

If this file and the code disagree, verify the current handlers in:

- `app/main.py`
- `app/api/projects.py`
- `app/api/jobs.py`
- `app/api/models.py`
- `app/api/role_model_checker.py`
- `app/api/story_development.py`
- `app/api/auth.py`
- `app/api/backup.py`
- `app/api/health.py`
