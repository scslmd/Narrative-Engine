# v1 Gap Checklist

## Existing Canonical Routes (verified)

| # | legacy_method | legacy_path | v1_method | v1_path | status |
|---|---|---|---|---|---|
| 1 | DELETE | `/story-development/arcs/selections/{selection_id}` | DELETE | `/v1/story-development/arcs/selections/{selection_id}` | exists |
| 2 | DELETE | `/story-development/braindump/sessions/{session_id}` | DELETE | `/v1/story-development/braindump/sessions/{session_id}` | exists |
| 3 | DELETE | `/story-development/flow/stages/{stage_id}` | DELETE | `/v1/story-development/flow/stages/{stage_id}` | exists |
| 4 | DELETE | `/story-development/relationships/{edge_id}` | DELETE | `/v1/story-development/relationships/{edge_id}` | exists |
| 5 | DELETE | `/story-development/storyboard/cards/{card_id}` | DELETE | `/v1/story-development/storyboard/cards/{card_id}` | exists |
| 6 | GET | `/jobs/{job_id}/attempts` | GET | `/v1/jobs/{job_id}/attempts` | exists |
| 7 | GET | `/jobs/{job_id}/lineage` | GET | `/v1/jobs/{job_id}/lineage` | exists |
| 8 | GET | `/jobs/{job_id}/logs` | GET | `/v1/jobs/{job_id}/logs` | exists |
| 9 | GET | `/jobs/{job_id}/status` | GET | `/v1/jobs/{job_id}/status` | exists |
| 10 | GET | `/jobs/{job_id}/steps` | GET | `/v1/jobs/{job_id}/steps` | exists |
| 11 | GET | `/models` | GET | `/v1/models` | exists |
| 12 | GET | `/role-model-checker/{run_id}/attempts` | GET | `/v1/role-model-checker/{run_id}/attempts` | exists |
| 13 | GET | `/role-model-checker/{run_id}/lineage` | GET | `/v1/role-model-checker/{run_id}/lineage` | exists |
| 14 | GET | `/role-model-checker/{run_id}/status` | GET | `/v1/role-model-checker/{run_id}/status` | exists |
| 15 | GET | `/role-model-checker/{run_id}/steps` | GET | `/v1/role-model-checker/{run_id}/steps` | exists |
| 16 | GET | `/story-development/arcs/candidates` | GET | `/v1/story-development/arcs/candidates` | exists |
| 17 | GET | `/story-development/arcs/comparisons` | GET | `/v1/story-development/arcs/comparisons` | exists |
| 18 | GET | `/story-development/arcs/selections` | GET | `/v1/story-development/arcs/selections` | exists |
| 19 | GET | `/story-development/arcs/stage-maps` | GET | `/v1/story-development/arcs/stage-maps` | exists |
| 20 | GET | `/story-development/braindump/sessions` | GET | `/v1/story-development/braindump/sessions` | exists |
| 21 | GET | `/story-development/braindump/sessions/{session_id}` | GET | `/v1/story-development/braindump/sessions/{session_id}` | exists |
| 22 | GET | `/story-development/brainstorm/items` | GET | `/v1/story-development/brainstorm/items` | exists |
| 23 | GET | `/story-development/brainstorm/promotions` | GET | `/v1/story-development/brainstorm/promotions` | exists |
| 24 | GET | `/story-development/branches` | GET | `/v1/story-development/branches` | exists |
| 25 | GET | `/story-development/branches/active` | GET | `/v1/story-development/branches/active` | exists |
| 26 | GET | `/story-development/branches/comparisons` | GET | `/v1/story-development/branches/comparisons` | exists |
| 27 | GET | `/story-development/branches/comparisons/{comparison_id}` | GET | `/v1/story-development/branches/comparisons/{comparison_id}` | exists |
| 28 | GET | `/story-development/branches/merge-decisions` | GET | `/v1/story-development/branches/merge-decisions` | exists |
| 29 | GET | `/story-development/branches/merge-decisions/{merge_decision_id}` | GET | `/v1/story-development/branches/merge-decisions/{merge_decision_id}` | exists |
| 30 | GET | `/story-development/branches/{branch_id}` | GET | `/v1/story-development/branches/{branch_id}` | exists |
| 31 | GET | `/story-development/branches/{branch_id}/state-refs` | GET | `/v1/story-development/branches/{branch_id}/state-refs` | exists |
| 32 | GET | `/story-development/characters` | GET | `/v1/story-development/characters` | exists |
| 33 | GET | `/story-development/characters/{character_id}` | GET | `/v1/story-development/characters/{character_id}` | exists |
| 34 | GET | `/story-development/characters/{character_id}/relationships` | GET | `/v1/story-development/characters/{character_id}/relationships` | exists |
| 35 | GET | `/story-development/decisions` | GET | `/v1/story-development/decisions` | exists |
| 36 | GET | `/story-development/decisions/{node_id}` | GET | `/v1/story-development/decisions/{node_id}` | exists |
| 37 | GET | `/story-development/decisions/{node_id}/path` | GET | `/v1/story-development/decisions/{node_id}/path` | exists |
| 38 | GET | `/story-development/drafting/draft-artifacts` | GET | `/v1/story-development/drafting/draft-artifacts` | exists |
| 39 | GET | `/story-development/drafting/draft-artifacts/{artifact_id}` | GET | `/v1/story-development/drafting/draft-artifacts/{artifact_id}` | exists |
| 40 | GET | `/story-development/drafting/manuscript-documents` | GET | `/v1/story-development/drafting/manuscript-documents` | exists |
| 41 | GET | `/story-development/drafting/manuscript-documents/{document_id}` | GET | `/v1/story-development/drafting/manuscript-documents/{document_id}` | exists |
| 42 | GET | `/story-development/drafting/revision-suggestions` | GET | `/v1/story-development/drafting/revision-suggestions` | exists |
| 43 | GET | `/story-development/drafting/revision-suggestions/{suggestion_id}` | GET | `/v1/story-development/drafting/revision-suggestions/{suggestion_id}` | exists |
| 44 | GET | `/story-development/flow/stages` | GET | `/v1/story-development/flow/stages` | exists |
| 45 | GET | `/story-development/foundation` | GET | `/v1/story-development/foundation` | exists |
| 46 | GET | `/story-development/foundation/review-cues` | GET | `/v1/story-development/foundation/review-cues` | exists |
| 47 | GET | `/story-development/foundation/revisions` | GET | `/v1/story-development/foundation/revisions` | exists |
| 48 | GET | `/story-development/planning/beat-plans` | GET | `/v1/story-development/planning/beat-plans` | exists |
| 49 | GET | `/story-development/planning/beat-plans/{beat_id}` | GET | `/v1/story-development/planning/beat-plans/{beat_id}` | exists |
| 50 | GET | `/story-development/planning/chapter-packets` | GET | `/v1/story-development/planning/chapter-packets` | exists |
| 51 | GET | `/story-development/planning/chapter-packets/{packet_id}` | GET | `/v1/story-development/planning/chapter-packets/{packet_id}` | exists |
| 52 | GET | `/story-development/planning/chapter-plans` | GET | `/v1/story-development/planning/chapter-plans` | exists |
| 53 | GET | `/story-development/planning/chapter-plans/{chapter_id}` | GET | `/v1/story-development/planning/chapter-plans/{chapter_id}` | exists |
| 54 | GET | `/story-development/planning/dependencies` | GET | `/v1/story-development/planning/dependencies` | exists |
| 55 | GET | `/story-development/planning/dependencies/{dependency_id}` | GET | `/v1/story-development/planning/dependencies/{dependency_id}` | exists |
| 56 | GET | `/story-development/planning/scene-plans` | GET | `/v1/story-development/planning/scene-plans` | exists |
| 57 | GET | `/story-development/planning/scene-plans/{scene_id}` | GET | `/v1/story-development/planning/scene-plans/{scene_id}` | exists |
| 58 | GET | `/story-development/planning/sequence-plans` | GET | `/v1/story-development/planning/sequence-plans` | exists |
| 59 | GET | `/story-development/planning/sequence-plans/{sequence_id}` | GET | `/v1/story-development/planning/sequence-plans/{sequence_id}` | exists |
| 60 | GET | `/story-development/relationships` | GET | `/v1/story-development/relationships` | exists |
| 61 | GET | `/story-development/review/decisions` | GET | `/v1/story-development/review/decisions` | exists |
| 62 | GET | `/story-development/review/decisions/{decision_id}` | GET | `/v1/story-development/review/decisions/{decision_id}` | exists |
| 63 | GET | `/story-development/review/findings` | GET | `/v1/story-development/review/findings` | exists |
| 64 | GET | `/story-development/review/findings/{finding_id}` | GET | `/v1/story-development/review/findings/{finding_id}` | exists |
| 65 | GET | `/story-development/review/inspect-links` | GET | `/v1/story-development/review/inspect-links` | exists |
| 66 | GET | `/story-development/review/inspect-links/{link_id}` | GET | `/v1/story-development/review/inspect-links/{link_id}` | exists |
| 67 | GET | `/story-development/storyboard/cards` | GET | `/v1/story-development/storyboard/cards` | exists |
| 68 | GET | `/story-development/storyboard/cards/{card_id}` | GET | `/v1/story-development/storyboard/cards/{card_id}` | exists |
| 69 | GET | `/story-development/world-bible` | GET | `/v1/story-development/world-bible` | exists |
| 70 | GET | `/story-development/world-bible/{entry_type}/{title}` | GET | `/v1/story-development/world-bible/{entry_type}/{title}` | exists |
| 71 | PATCH | `/story-development/arcs/selections/{selection_id}` | PATCH | `/v1/story-development/arcs/selections/{selection_id}` | exists |
| 72 | PATCH | `/story-development/braindump/sessions/{session_id}` | PATCH | `/v1/story-development/braindump/sessions/{session_id}` | exists |
| 73 | PATCH | `/story-development/characters/{character_id}` | PATCH | `/v1/story-development/characters/{character_id}` | exists |
| 74 | PATCH | `/story-development/drafting/manuscript-documents/{document_id}` | PATCH | `/v1/story-development/drafting/manuscript-documents/{document_id}` | exists |
| 75 | PATCH | `/story-development/flow/stages/{stage_id}` | PATCH | `/v1/story-development/flow/stages/{stage_id}` | exists |
| 76 | PATCH | `/story-development/foundation` | PATCH | `/v1/story-development/foundation` | exists |
| 77 | PATCH | `/story-development/planning/beat-plans/{beat_id}` | PATCH | `/v1/story-development/planning/beat-plans/{beat_id}` | exists |
| 78 | PATCH | `/story-development/planning/chapter-packets/{packet_id}` | PATCH | `/v1/story-development/planning/chapter-packets/{packet_id}` | exists |
| 79 | PATCH | `/story-development/planning/chapter-plans/{chapter_id}` | PATCH | `/v1/story-development/planning/chapter-plans/{chapter_id}` | exists |
| 80 | PATCH | `/story-development/planning/scene-plans/{scene_id}` | PATCH | `/v1/story-development/planning/scene-plans/{scene_id}` | exists |
| 81 | PATCH | `/story-development/planning/sequence-plans/{sequence_id}` | PATCH | `/v1/story-development/planning/sequence-plans/{sequence_id}` | exists |
| 82 | PATCH | `/story-development/relationships/{edge_id}` | PATCH | `/v1/story-development/relationships/{edge_id}` | exists |
| 83 | PATCH | `/story-development/storyboard/cards/{card_id}` | PATCH | `/v1/story-development/storyboard/cards/{card_id}` | exists |
| 84 | PATCH | `/story-development/world-bible/{entry_type}/{title}` | PATCH | `/v1/story-development/world-bible/{entry_type}/{title}` | exists |
| 85 | POST | `/jobs/create` | POST | `/v1/jobs/create` | exists |
| 86 | POST | `/jobs/{job_id}/retry` | POST | `/v1/jobs/{job_id}/retry` | exists |
| 87 | POST | `/role-model-checker/run` | POST | `/v1/role-model-checker/run` | exists |
| 88 | POST | `/role-model-checker/start` | POST | `/v1/role-model-checker/start` | exists |
| 89 | POST | `/role-model-checker/{run_id}/retry` | POST | `/v1/role-model-checker/{run_id}/retry` | exists |
| 90 | POST | `/story-development/arcs/candidates` | POST | `/v1/story-development/arcs/candidates` | exists |
| 91 | POST | `/story-development/arcs/comparisons` | POST | `/v1/story-development/arcs/comparisons` | exists |
| 92 | POST | `/story-development/arcs/selections` | POST | `/v1/story-development/arcs/selections` | exists |
| 93 | POST | `/story-development/arcs/stage-maps` | POST | `/v1/story-development/arcs/stage-maps` | exists |
| 94 | POST | `/story-development/braindump/sessions` | POST | `/v1/story-development/braindump/sessions` | exists |
| 95 | POST | `/story-development/braindump/sessions/{session_id}/organize` | POST | `/v1/story-development/braindump/sessions/{session_id}/organize` | exists |
| 96 | POST | `/story-development/brainstorm/items` | POST | `/v1/story-development/brainstorm/items` | exists |
| 97 | POST | `/story-development/brainstorm/items/cluster` | POST | `/v1/story-development/brainstorm/items/cluster` | exists |
| 98 | POST | `/story-development/brainstorm/items/promote` | POST | `/v1/story-development/brainstorm/items/promote` | exists |
| 99 | POST | `/story-development/branches` | POST | `/v1/story-development/branches` | exists |
| 100 | POST | `/story-development/branches/active` | POST | `/v1/story-development/branches/active` | exists |
| 101 | POST | `/story-development/branches/comparisons` | POST | `/v1/story-development/branches/comparisons` | exists |
| 102 | POST | `/story-development/branches/merge-decisions` | POST | `/v1/story-development/branches/merge-decisions` | exists |
| 103 | POST | `/story-development/characters` | POST | `/v1/story-development/characters` | exists |
| 104 | POST | `/story-development/drafting/draft-artifacts` | POST | `/v1/story-development/drafting/draft-artifacts` | exists |
| 105 | POST | `/story-development/drafting/draft-artifacts/alternate-variant` | POST | `/v1/story-development/drafting/draft-artifacts/alternate-variant` | exists |
| 106 | POST | `/story-development/drafting/draft-artifacts/continue` | POST | `/v1/story-development/drafting/draft-artifacts/continue` | exists |
| 107 | POST | `/story-development/drafting/manuscript-documents` | POST | `/v1/story-development/drafting/manuscript-documents` | exists |
| 108 | POST | `/story-development/drafting/manuscript-documents/{document_id}/review` | POST | `/v1/story-development/drafting/manuscript-documents/{document_id}/review` | exists |
| 109 | POST | `/story-development/drafting/promote-draft` | POST | `/v1/story-development/drafting/promote-draft` | exists |
| 110 | POST | `/story-development/drafting/revision-suggestions` | POST | `/v1/story-development/drafting/revision-suggestions` | exists |
| 111 | POST | `/story-development/flow/stages` | POST | `/v1/story-development/flow/stages` | exists |
| 112 | POST | `/story-development/flow/stages/init` | POST | `/v1/story-development/flow/stages/init` | exists |
| 113 | POST | `/story-development/flow/stages/reorder` | POST | `/v1/story-development/flow/stages/reorder` | exists |
| 114 | POST | `/story-development/foundation` | POST | `/v1/story-development/foundation` | exists |
| 115 | POST | `/story-development/planning/beat-plans` | POST | `/v1/story-development/planning/beat-plans` | exists |
| 116 | POST | `/story-development/planning/chapter-packets` | POST | `/v1/story-development/planning/chapter-packets` | exists |
| 117 | POST | `/story-development/planning/chapter-plans` | POST | `/v1/story-development/planning/chapter-plans` | exists |
| 118 | POST | `/story-development/planning/reorder` | POST | `/v1/story-development/planning/reorder` | exists |
| 119 | POST | `/story-development/planning/scene-plans` | POST | `/v1/story-development/planning/scene-plans` | exists |
| 120 | POST | `/story-development/planning/sequence-plans` | POST | `/v1/story-development/planning/sequence-plans` | exists |
| 121 | POST | `/story-development/relationships` | POST | `/v1/story-development/relationships` | exists |
| 122 | POST | `/story-development/review/decisions` | POST | `/v1/story-development/review/decisions` | exists |
| 123 | POST | `/story-development/review/inspect-links` | POST | `/v1/story-development/review/inspect-links` | exists |
| 124 | POST | `/story-development/storyboard/cards` | POST | `/v1/story-development/storyboard/cards` | exists |
| 125 | POST | `/story-development/world-bible` | POST | `/v1/story-development/world-bible` | exists |
| 126 | PUT | `/story-development/storyboard/cards/{card_id}` | PUT | `/v1/story-development/storyboard/cards/{card_id}` | exists |
| 127 | PUT | `/story-development/storyboard/cards/{column_id}/reindex` | PUT | `/v1/story-development/storyboard/cards/{column_id}/reindex` | exists |

## Missing Canonical Routes (implementation required)

| # | legacy_method | legacy_path | required_v1_method | required_v1_path | status |
|---|---|---|---|---|---|
| 1 | DELETE | `/auth/keys/{prefix}` | DELETE | `/v1/auth/keys/{prefix}` | missing - requires implementation |
| 2 | DELETE | `/backup/{backup_id}` | DELETE | `/v1/backup/{backup_id}` | missing - requires implementation |
| 3 | DELETE | `/projects/maintenance/projects/{project_id}` | DELETE | `/v1/projects/maintenance/projects/{project_id}` | missing - requires implementation |
| 4 | DELETE | `/projects/{project_id}` | DELETE | `/v1/projects/{project_id}` | missing - requires implementation |
| 5 | GET | `/auth/keys` | GET | `/v1/auth/keys` | missing - requires implementation |
| 6 | GET | `/backup/latest` | GET | `/v1/backup/latest` | missing - requires implementation |
| 7 | GET | `/backup/list` | GET | `/v1/backup/list` | missing - requires implementation |
| 8 | GET | `/projects` | GET | `/v1/projects` | missing - requires implementation |
| 9 | GET | `/projects` | GET | `/v1/projects` | missing - requires implementation |
| 10 | GET | `/projects/export/{import_id}` | GET | `/v1/projects/export/{import_id}` | missing - requires implementation |
| 11 | GET | `/projects/extraction/{extraction_id}` | GET | `/v1/projects/extraction/{extraction_id}` | missing - requires implementation |
| 12 | GET | `/projects/import/{import_id}` | GET | `/v1/projects/import/{import_id}` | missing - requires implementation |
| 13 | GET | `/projects/{project_id}` | GET | `/v1/projects/{project_id}` | missing - requires implementation |
| 14 | GET | `/projects/{project_id}` | GET | `/v1/projects/{project_id}` | missing - requires implementation |
| 15 | GET | `/projects/{project_id}/chapter-1` | GET | `/v1/projects/{project_id}/chapter-1` | missing - requires implementation |
| 16 | GET | `/projects/{project_id}/chapter-1` | GET | `/v1/projects/{project_id}/chapter-1` | missing - requires implementation |
| 17 | GET | `/projects/{project_id}/manifest` | GET | `/v1/projects/{project_id}/manifest` | missing - requires implementation |
| 18 | GET | `/projects/{project_id}/sequence` | GET | `/v1/projects/{project_id}/sequence` | missing - requires implementation |
| 19 | GET | `/projects/{project_id}/sequence` | GET | `/v1/projects/{project_id}/sequence` | missing - requires implementation |
| 20 | POST | `/auth/keys` | POST | `/v1/auth/keys` | missing - requires implementation |
| 21 | POST | `/backup/create` | POST | `/v1/backup/create` | missing - requires implementation |
| 22 | POST | `/backup/restore/{backup_id}` | POST | `/v1/backup/restore/{backup_id}` | missing - requires implementation |
| 23 | POST | `/projects/create` | POST | `/v1/projects/create` | missing - requires implementation |
| 24 | POST | `/projects/guided-setup/analyze` | POST | `/v1/projects/guided-setup/analyze` | missing - requires implementation |
| 25 | POST | `/projects/guided-setup/create` | POST | `/v1/projects/guided-setup/create` | missing - requires implementation |
| 26 | POST | `/projects/import-export` | POST | `/v1/projects/import-export` | missing - requires implementation |
| 27 | POST | `/projects/import-mythos` | POST | `/v1/projects/import-mythos` | missing - requires implementation |
| 28 | POST | `/projects/import-patterns` | POST | `/v1/projects/import-patterns` | missing - requires implementation |
| 29 | POST | `/projects/import-story` | POST | `/v1/projects/import-story` | missing - requires implementation |
| 30 | POST | `/projects/maintenance/audit-log/truncate` | POST | `/v1/projects/maintenance/audit-log/truncate` | missing - requires implementation |
| 31 | POST | `/projects/maintenance/cleanup` | POST | `/v1/projects/maintenance/cleanup` | missing - requires implementation |
| 32 | POST | `/projects/maintenance/database/compact` | POST | `/v1/projects/maintenance/database/compact` | missing - requires implementation |
| 33 | POST | `/projects/maintenance/scan` | POST | `/v1/projects/maintenance/scan` | missing - requires implementation |
| 34 | POST | `/projects/{project_id}/export` | POST | `/v1/projects/{project_id}/export` | missing - requires implementation |
| 35 | POST | `/projects/{project_id}/extract-patterns` | POST | `/v1/projects/{project_id}/extract-patterns` | missing - requires implementation |
| 36 | POST | `/projects/{project_id}/generate-description` | POST | `/v1/projects/{project_id}/generate-description` | missing - requires implementation |

**Summary:** 127 existing, 36 missing. Total: 163.

## Action Items

The following routes require `/v1` implementation (assign to PR-B):
- `DELETE /auth/keys/{prefix}` -> `DELETE /v1/auth/keys/{prefix}`
- `DELETE /backup/{backup_id}` -> `DELETE /v1/backup/{backup_id}`
- `DELETE /projects/maintenance/projects/{project_id}` -> `DELETE /v1/projects/maintenance/projects/{project_id}`
- `DELETE /projects/{project_id}` -> `DELETE /v1/projects/{project_id}`
- `GET /auth/keys` -> `GET /v1/auth/keys`
- `GET /backup/latest` -> `GET /v1/backup/latest`
- `GET /backup/list` -> `GET /v1/backup/list`
- `GET /projects` -> `GET /v1/projects`
- `GET /projects` -> `GET /v1/projects`
- `GET /projects/export/{import_id}` -> `GET /v1/projects/export/{import_id}`
- `GET /projects/extraction/{extraction_id}` -> `GET /v1/projects/extraction/{extraction_id}`
- `GET /projects/import/{import_id}` -> `GET /v1/projects/import/{import_id}`
- `GET /projects/{project_id}` -> `GET /v1/projects/{project_id}`
- `GET /projects/{project_id}` -> `GET /v1/projects/{project_id}`
- `GET /projects/{project_id}/chapter-1` -> `GET /v1/projects/{project_id}/chapter-1`
- `GET /projects/{project_id}/chapter-1` -> `GET /v1/projects/{project_id}/chapter-1`
- `GET /projects/{project_id}/manifest` -> `GET /v1/projects/{project_id}/manifest`
- `GET /projects/{project_id}/sequence` -> `GET /v1/projects/{project_id}/sequence`
- `GET /projects/{project_id}/sequence` -> `GET /v1/projects/{project_id}/sequence`
- `POST /auth/keys` -> `POST /v1/auth/keys`
- `POST /backup/create` -> `POST /v1/backup/create`
- `POST /backup/restore/{backup_id}` -> `POST /v1/backup/restore/{backup_id}`
- `POST /projects/create` -> `POST /v1/projects/create`
- `POST /projects/guided-setup/analyze` -> `POST /v1/projects/guided-setup/analyze`
- `POST /projects/guided-setup/create` -> `POST /v1/projects/guided-setup/create`
- `POST /projects/import-export` -> `POST /v1/projects/import-export`
- `POST /projects/import-mythos` -> `POST /v1/projects/import-mythos`
- `POST /projects/import-patterns` -> `POST /v1/projects/import-patterns`
- `POST /projects/import-story` -> `POST /v1/projects/import-story`
- `POST /projects/maintenance/audit-log/truncate` -> `POST /v1/projects/maintenance/audit-log/truncate`
- `POST /projects/maintenance/cleanup` -> `POST /v1/projects/maintenance/cleanup`
- `POST /projects/maintenance/database/compact` -> `POST /v1/projects/maintenance/database/compact`
- `POST /projects/maintenance/scan` -> `POST /v1/projects/maintenance/scan`
- `POST /projects/{project_id}/export` -> `POST /v1/projects/{project_id}/export`
- `POST /projects/{project_id}/extract-patterns` -> `POST /v1/projects/{project_id}/extract-patterns`
- `POST /projects/{project_id}/generate-description` -> `POST /v1/projects/{project_id}/generate-description`
