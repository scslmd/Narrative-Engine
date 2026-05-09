# Legacy-to-v1 Endpoint Mapping Spec

Generated from `route_classification.csv`.

| legacy_method | legacy_path | v1_method | v1_path | status_parity | schema_parity_notes |
|---|---|---|---|---|---|
| DELETE | `/auth/keys/{prefix}` | DELETE | `/v1/auth/keys/{prefix}` | missing | No /v1 counterpart exists; see `v1_gap_checklist.md` |
| DELETE | `/backup/{backup_id}` | DELETE | `/v1/backup/{backup_id}` | missing | No /v1 counterpart exists; see `v1_gap_checklist.md` |
| DELETE | `/projects/maintenance/projects/{project_id}` | DELETE | `/v1/projects/maintenance/projects/{project_id}` | missing | No /v1 counterpart exists; see `v1_gap_checklist.md` |
| DELETE | `/projects/{project_id}` | DELETE | `/v1/projects/{project_id}` | missing | No /v1 counterpart exists; see `v1_gap_checklist.md` |
| DELETE | `/story-development/arcs/selections/{selection_id}` | DELETE | `/v1/story-development/arcs/selections/{selection_id}` | exact | Identical handler or equivalent canonical route exists |
| DELETE | `/story-development/braindump/sessions/{session_id}` | DELETE | `/v1/story-development/braindump/sessions/{session_id}` | exact | Identical handler or equivalent canonical route exists |
| DELETE | `/story-development/flow/stages/{stage_id}` | DELETE | `/v1/story-development/flow/stages/{stage_id}` | exact | Identical handler or equivalent canonical route exists |
| DELETE | `/story-development/relationships/{edge_id}` | DELETE | `/v1/story-development/relationships/{edge_id}` | exact | Identical handler or equivalent canonical route exists |
| DELETE | `/story-development/storyboard/cards/{card_id}` | DELETE | `/v1/story-development/storyboard/cards/{card_id}` | exact | Identical handler or equivalent canonical route exists |
| GET | `/auth/keys` | GET | `/v1/auth/keys` | missing | No /v1 counterpart exists; see `v1_gap_checklist.md` |
| GET | `/backup/latest` | GET | `/v1/backup/latest` | missing | No /v1 counterpart exists; see `v1_gap_checklist.md` |
| GET | `/backup/list` | GET | `/v1/backup/list` | missing | No /v1 counterpart exists; see `v1_gap_checklist.md` |
| GET | `/jobs/{job_id}/attempts` | GET | `/v1/jobs/{job_id}/attempts` | exact | Identical handler or equivalent canonical route exists |
| GET | `/jobs/{job_id}/lineage` | GET | `/v1/jobs/{job_id}/lineage` | exact | Identical handler or equivalent canonical route exists |
| GET | `/jobs/{job_id}/logs` | GET | `/v1/jobs/{job_id}/logs` | exact | Identical handler or equivalent canonical route exists |
| GET | `/jobs/{job_id}/status` | GET | `/v1/jobs/{job_id}/status` | exact | Identical handler or equivalent canonical route exists |
| GET | `/jobs/{job_id}/steps` | GET | `/v1/jobs/{job_id}/steps` | exact | Identical handler or equivalent canonical route exists |
| GET | `/models` | GET | `/v1/models` | exact | Identical handler or equivalent canonical route exists |
| GET | `/projects` | GET | `/v1/projects` | missing | No /v1 counterpart exists; see `v1_gap_checklist.md` |
| GET | `/projects` | GET | `/v1/projects` | missing | No /v1 counterpart exists; see `v1_gap_checklist.md` |
| GET | `/projects/export/{import_id}` | GET | `/v1/projects/export/{import_id}` | missing | No /v1 counterpart exists; see `v1_gap_checklist.md` |
| GET | `/projects/extraction/{extraction_id}` | GET | `/v1/projects/extraction/{extraction_id}` | missing | No /v1 counterpart exists; see `v1_gap_checklist.md` |
| GET | `/projects/import/{import_id}` | GET | `/v1/projects/import/{import_id}` | missing | No /v1 counterpart exists; see `v1_gap_checklist.md` |
| GET | `/projects/{project_id}` | GET | `/v1/projects/{project_id}` | missing | No /v1 counterpart exists; see `v1_gap_checklist.md` |
| GET | `/projects/{project_id}` | GET | `/v1/projects/{project_id}` | missing | No /v1 counterpart exists; see `v1_gap_checklist.md` |
| GET | `/projects/{project_id}/chapter-1` | GET | `/v1/projects/{project_id}/chapter-1` | missing | No /v1 counterpart exists; see `v1_gap_checklist.md` |
| GET | `/projects/{project_id}/chapter-1` | GET | `/v1/projects/{project_id}/chapter-1` | missing | No /v1 counterpart exists; see `v1_gap_checklist.md` |
| GET | `/projects/{project_id}/manifest` | GET | `/v1/projects/{project_id}/manifest` | missing | No /v1 counterpart exists; see `v1_gap_checklist.md` |
| GET | `/projects/{project_id}/sequence` | GET | `/v1/projects/{project_id}/sequence` | missing | No /v1 counterpart exists; see `v1_gap_checklist.md` |
| GET | `/projects/{project_id}/sequence` | GET | `/v1/projects/{project_id}/sequence` | missing | No /v1 counterpart exists; see `v1_gap_checklist.md` |
| GET | `/role-model-checker/{run_id}/attempts` | GET | `/v1/role-model-checker/{run_id}/attempts` | exact | Identical handler or equivalent canonical route exists |
| GET | `/role-model-checker/{run_id}/lineage` | GET | `/v1/role-model-checker/{run_id}/lineage` | exact | Identical handler or equivalent canonical route exists |
| GET | `/role-model-checker/{run_id}/status` | GET | `/v1/role-model-checker/{run_id}/status` | exact | Identical handler or equivalent canonical route exists |
| GET | `/role-model-checker/{run_id}/steps` | GET | `/v1/role-model-checker/{run_id}/steps` | exact | Identical handler or equivalent canonical route exists |
| GET | `/story-development/arcs/candidates` | GET | `/v1/story-development/arcs/candidates` | exact | Identical handler or equivalent canonical route exists |
| GET | `/story-development/arcs/comparisons` | GET | `/v1/story-development/arcs/comparisons` | exact | Identical handler or equivalent canonical route exists |
| GET | `/story-development/arcs/selections` | GET | `/v1/story-development/arcs/selections` | exact | Identical handler or equivalent canonical route exists |
| GET | `/story-development/arcs/stage-maps` | GET | `/v1/story-development/arcs/stage-maps` | exact | Identical handler or equivalent canonical route exists |
| GET | `/story-development/braindump/sessions` | GET | `/v1/story-development/braindump/sessions` | exact | Identical handler or equivalent canonical route exists |
| GET | `/story-development/braindump/sessions/{session_id}` | GET | `/v1/story-development/braindump/sessions/{session_id}` | exact | Identical handler or equivalent canonical route exists |
| GET | `/story-development/brainstorm/items` | GET | `/v1/story-development/brainstorm/items` | exact | Identical handler or equivalent canonical route exists |
| GET | `/story-development/brainstorm/promotions` | GET | `/v1/story-development/brainstorm/promotions` | exact | Identical handler or equivalent canonical route exists |
| GET | `/story-development/branches` | GET | `/v1/story-development/branches` | exact | Identical handler or equivalent canonical route exists |
| GET | `/story-development/branches/active` | GET | `/v1/story-development/branches/active` | exact | Identical handler or equivalent canonical route exists |
| GET | `/story-development/branches/comparisons` | GET | `/v1/story-development/branches/comparisons` | exact | Identical handler or equivalent canonical route exists |
| GET | `/story-development/branches/comparisons/{comparison_id}` | GET | `/v1/story-development/branches/comparisons/{comparison_id}` | exact | Identical handler or equivalent canonical route exists |
| GET | `/story-development/branches/merge-decisions` | GET | `/v1/story-development/branches/merge-decisions` | exact | Identical handler or equivalent canonical route exists |
| GET | `/story-development/branches/merge-decisions/{merge_decision_id}` | GET | `/v1/story-development/branches/merge-decisions/{merge_decision_id}` | exact | Identical handler or equivalent canonical route exists |
| GET | `/story-development/branches/{branch_id}` | GET | `/v1/story-development/branches/{branch_id}` | exact | Identical handler or equivalent canonical route exists |
| GET | `/story-development/branches/{branch_id}/state-refs` | GET | `/v1/story-development/branches/{branch_id}/state-refs` | exact | Identical handler or equivalent canonical route exists |
| GET | `/story-development/characters` | GET | `/v1/story-development/characters` | exact | Identical handler or equivalent canonical route exists |
| GET | `/story-development/characters/{character_id}` | GET | `/v1/story-development/characters/{character_id}` | exact | Identical handler or equivalent canonical route exists |
| GET | `/story-development/characters/{character_id}/relationships` | GET | `/v1/story-development/characters/{character_id}/relationships` | exact | Identical handler or equivalent canonical route exists |
| GET | `/story-development/decisions` | GET | `/v1/story-development/decisions` | exact | Identical handler or equivalent canonical route exists |
| GET | `/story-development/decisions/{node_id}` | GET | `/v1/story-development/decisions/{node_id}` | exact | Identical handler or equivalent canonical route exists |
| GET | `/story-development/decisions/{node_id}/path` | GET | `/v1/story-development/decisions/{node_id}/path` | exact | Identical handler or equivalent canonical route exists |
| GET | `/story-development/drafting/draft-artifacts` | GET | `/v1/story-development/drafting/draft-artifacts` | exact | Identical handler or equivalent canonical route exists |
| GET | `/story-development/drafting/draft-artifacts/{artifact_id}` | GET | `/v1/story-development/drafting/draft-artifacts/{artifact_id}` | exact | Identical handler or equivalent canonical route exists |
| GET | `/story-development/drafting/manuscript-documents` | GET | `/v1/story-development/drafting/manuscript-documents` | exact | Identical handler or equivalent canonical route exists |
| GET | `/story-development/drafting/manuscript-documents/{document_id}` | GET | `/v1/story-development/drafting/manuscript-documents/{document_id}` | exact | Identical handler or equivalent canonical route exists |
| GET | `/story-development/drafting/revision-suggestions` | GET | `/v1/story-development/drafting/revision-suggestions` | exact | Identical handler or equivalent canonical route exists |
| GET | `/story-development/drafting/revision-suggestions/{suggestion_id}` | GET | `/v1/story-development/drafting/revision-suggestions/{suggestion_id}` | exact | Identical handler or equivalent canonical route exists |
| GET | `/story-development/flow/stages` | GET | `/v1/story-development/flow/stages` | exact | Identical handler or equivalent canonical route exists |
| GET | `/story-development/foundation` | GET | `/v1/story-development/foundation` | exact | Identical handler or equivalent canonical route exists |
| GET | `/story-development/foundation/review-cues` | GET | `/v1/story-development/foundation/review-cues` | exact | Identical handler or equivalent canonical route exists |
| GET | `/story-development/foundation/revisions` | GET | `/v1/story-development/foundation/revisions` | exact | Identical handler or equivalent canonical route exists |
| GET | `/story-development/planning/beat-plans` | GET | `/v1/story-development/planning/beat-plans` | exact | Identical handler or equivalent canonical route exists |
| GET | `/story-development/planning/beat-plans/{beat_id}` | GET | `/v1/story-development/planning/beat-plans/{beat_id}` | exact | Identical handler or equivalent canonical route exists |
| GET | `/story-development/planning/chapter-packets` | GET | `/v1/story-development/planning/chapter-packets` | exact | Identical handler or equivalent canonical route exists |
| GET | `/story-development/planning/chapter-packets/{packet_id}` | GET | `/v1/story-development/planning/chapter-packets/{packet_id}` | exact | Identical handler or equivalent canonical route exists |
| GET | `/story-development/planning/chapter-plans` | GET | `/v1/story-development/planning/chapter-plans` | exact | Identical handler or equivalent canonical route exists |
| GET | `/story-development/planning/chapter-plans/{chapter_id}` | GET | `/v1/story-development/planning/chapter-plans/{chapter_id}` | exact | Identical handler or equivalent canonical route exists |
| GET | `/story-development/planning/dependencies` | GET | `/v1/story-development/planning/dependencies` | exact | Identical handler or equivalent canonical route exists |
| GET | `/story-development/planning/dependencies/{dependency_id}` | GET | `/v1/story-development/planning/dependencies/{dependency_id}` | exact | Identical handler or equivalent canonical route exists |
| GET | `/story-development/planning/scene-plans` | GET | `/v1/story-development/planning/scene-plans` | exact | Identical handler or equivalent canonical route exists |
| GET | `/story-development/planning/scene-plans/{scene_id}` | GET | `/v1/story-development/planning/scene-plans/{scene_id}` | exact | Identical handler or equivalent canonical route exists |
| GET | `/story-development/planning/sequence-plans` | GET | `/v1/story-development/planning/sequence-plans` | exact | Identical handler or equivalent canonical route exists |
| GET | `/story-development/planning/sequence-plans/{sequence_id}` | GET | `/v1/story-development/planning/sequence-plans/{sequence_id}` | exact | Identical handler or equivalent canonical route exists |
| GET | `/story-development/relationships` | GET | `/v1/story-development/relationships` | exact | Identical handler or equivalent canonical route exists |
| GET | `/story-development/review/decisions` | GET | `/v1/story-development/review/decisions` | exact | Identical handler or equivalent canonical route exists |
| GET | `/story-development/review/decisions/{decision_id}` | GET | `/v1/story-development/review/decisions/{decision_id}` | exact | Identical handler or equivalent canonical route exists |
| GET | `/story-development/review/findings` | GET | `/v1/story-development/review/findings` | exact | Identical handler or equivalent canonical route exists |
| GET | `/story-development/review/findings/{finding_id}` | GET | `/v1/story-development/review/findings/{finding_id}` | exact | Identical handler or equivalent canonical route exists |
| GET | `/story-development/review/inspect-links` | GET | `/v1/story-development/review/inspect-links` | exact | Identical handler or equivalent canonical route exists |
| GET | `/story-development/review/inspect-links/{link_id}` | GET | `/v1/story-development/review/inspect-links/{link_id}` | exact | Identical handler or equivalent canonical route exists |
| GET | `/story-development/storyboard/cards` | GET | `/v1/story-development/storyboard/cards` | exact | Identical handler or equivalent canonical route exists |
| GET | `/story-development/storyboard/cards/{card_id}` | GET | `/v1/story-development/storyboard/cards/{card_id}` | exact | Identical handler or equivalent canonical route exists |
| GET | `/story-development/world-bible` | GET | `/v1/story-development/world-bible` | exact | Identical handler or equivalent canonical route exists |
| GET | `/story-development/world-bible/{entry_type}/{title}` | GET | `/v1/story-development/world-bible/{entry_type}/{title}` | exact | Identical handler or equivalent canonical route exists |
| PATCH | `/story-development/arcs/selections/{selection_id}` | PATCH | `/v1/story-development/arcs/selections/{selection_id}` | exact | Identical handler or equivalent canonical route exists |
| PATCH | `/story-development/braindump/sessions/{session_id}` | PATCH | `/v1/story-development/braindump/sessions/{session_id}` | exact | Identical handler or equivalent canonical route exists |
| PATCH | `/story-development/characters/{character_id}` | PATCH | `/v1/story-development/characters/{character_id}` | exact | Identical handler or equivalent canonical route exists |
| PATCH | `/story-development/drafting/manuscript-documents/{document_id}` | PATCH | `/v1/story-development/drafting/manuscript-documents/{document_id}` | exact | Identical handler or equivalent canonical route exists |
| PATCH | `/story-development/flow/stages/{stage_id}` | PATCH | `/v1/story-development/flow/stages/{stage_id}` | exact | Identical handler or equivalent canonical route exists |
| PATCH | `/story-development/foundation` | PATCH | `/v1/story-development/foundation` | exact | Identical handler or equivalent canonical route exists |
| PATCH | `/story-development/planning/beat-plans/{beat_id}` | PATCH | `/v1/story-development/planning/beat-plans/{beat_id}` | exact | Identical handler or equivalent canonical route exists |
| PATCH | `/story-development/planning/chapter-packets/{packet_id}` | PATCH | `/v1/story-development/planning/chapter-packets/{packet_id}` | exact | Identical handler or equivalent canonical route exists |
| PATCH | `/story-development/planning/chapter-plans/{chapter_id}` | PATCH | `/v1/story-development/planning/chapter-plans/{chapter_id}` | exact | Identical handler or equivalent canonical route exists |
| PATCH | `/story-development/planning/scene-plans/{scene_id}` | PATCH | `/v1/story-development/planning/scene-plans/{scene_id}` | exact | Identical handler or equivalent canonical route exists |
| PATCH | `/story-development/planning/sequence-plans/{sequence_id}` | PATCH | `/v1/story-development/planning/sequence-plans/{sequence_id}` | exact | Identical handler or equivalent canonical route exists |
| PATCH | `/story-development/relationships/{edge_id}` | PATCH | `/v1/story-development/relationships/{edge_id}` | exact | Identical handler or equivalent canonical route exists |
| PATCH | `/story-development/storyboard/cards/{card_id}` | PATCH | `/v1/story-development/storyboard/cards/{card_id}` | exact | Identical handler or equivalent canonical route exists |
| PATCH | `/story-development/world-bible/{entry_type}/{title}` | PATCH | `/v1/story-development/world-bible/{entry_type}/{title}` | exact | Identical handler or equivalent canonical route exists |
| POST | `/auth/keys` | POST | `/v1/auth/keys` | missing | No /v1 counterpart exists; see `v1_gap_checklist.md` |
| POST | `/backup/create` | POST | `/v1/backup/create` | missing | No /v1 counterpart exists; see `v1_gap_checklist.md` |
| POST | `/backup/restore/{backup_id}` | POST | `/v1/backup/restore/{backup_id}` | missing | No /v1 counterpart exists; see `v1_gap_checklist.md` |
| POST | `/jobs/create` | POST | `/v1/jobs/create` | exact | Identical handler or equivalent canonical route exists |
| POST | `/jobs/{job_id}/retry` | POST | `/v1/jobs/{job_id}/retry` | exact | Identical handler or equivalent canonical route exists |
| POST | `/projects/create` | POST | `/v1/projects/create` | missing | No /v1 counterpart exists; see `v1_gap_checklist.md` |
| POST | `/projects/guided-setup/analyze` | POST | `/v1/projects/guided-setup/analyze` | missing | No /v1 counterpart exists; see `v1_gap_checklist.md` |
| POST | `/projects/guided-setup/create` | POST | `/v1/projects/guided-setup/create` | missing | No /v1 counterpart exists; see `v1_gap_checklist.md` |
| POST | `/projects/import-export` | POST | `/v1/projects/import-export` | missing | No /v1 counterpart exists; see `v1_gap_checklist.md` |
| POST | `/projects/import-mythos` | POST | `/v1/projects/import-mythos` | missing | No /v1 counterpart exists; see `v1_gap_checklist.md` |
| POST | `/projects/import-patterns` | POST | `/v1/projects/import-patterns` | missing | No /v1 counterpart exists; see `v1_gap_checklist.md` |
| POST | `/projects/import-story` | POST | `/v1/projects/import-story` | missing | No /v1 counterpart exists; see `v1_gap_checklist.md` |
| POST | `/projects/maintenance/audit-log/truncate` | POST | `/v1/projects/maintenance/audit-log/truncate` | missing | No /v1 counterpart exists; see `v1_gap_checklist.md` |
| POST | `/projects/maintenance/cleanup` | POST | `/v1/projects/maintenance/cleanup` | missing | No /v1 counterpart exists; see `v1_gap_checklist.md` |
| POST | `/projects/maintenance/database/compact` | POST | `/v1/projects/maintenance/database/compact` | missing | No /v1 counterpart exists; see `v1_gap_checklist.md` |
| POST | `/projects/maintenance/scan` | POST | `/v1/projects/maintenance/scan` | missing | No /v1 counterpart exists; see `v1_gap_checklist.md` |
| POST | `/projects/{project_id}/export` | POST | `/v1/projects/{project_id}/export` | missing | No /v1 counterpart exists; see `v1_gap_checklist.md` |
| POST | `/projects/{project_id}/extract-patterns` | POST | `/v1/projects/{project_id}/extract-patterns` | missing | No /v1 counterpart exists; see `v1_gap_checklist.md` |
| POST | `/projects/{project_id}/generate-description` | POST | `/v1/projects/{project_id}/generate-description` | missing | No /v1 counterpart exists; see `v1_gap_checklist.md` |
| POST | `/role-model-checker/run` | POST | `/v1/role-model-checker/run` | exact | Identical handler or equivalent canonical route exists |
| POST | `/role-model-checker/start` | POST | `/v1/role-model-checker/start` | exact | Identical handler or equivalent canonical route exists |
| POST | `/role-model-checker/{run_id}/retry` | POST | `/v1/role-model-checker/{run_id}/retry` | exact | Identical handler or equivalent canonical route exists |
| POST | `/story-development/arcs/candidates` | POST | `/v1/story-development/arcs/candidates` | exact | Identical handler or equivalent canonical route exists |
| POST | `/story-development/arcs/comparisons` | POST | `/v1/story-development/arcs/comparisons` | exact | Identical handler or equivalent canonical route exists |
| POST | `/story-development/arcs/selections` | POST | `/v1/story-development/arcs/selections` | exact | Identical handler or equivalent canonical route exists |
| POST | `/story-development/arcs/stage-maps` | POST | `/v1/story-development/arcs/stage-maps` | exact | Identical handler or equivalent canonical route exists |
| POST | `/story-development/braindump/sessions` | POST | `/v1/story-development/braindump/sessions` | exact | Identical handler or equivalent canonical route exists |
| POST | `/story-development/braindump/sessions/{session_id}/organize` | POST | `/v1/story-development/braindump/sessions/{session_id}/organize` | exact | Identical handler or equivalent canonical route exists |
| POST | `/story-development/brainstorm/items` | POST | `/v1/story-development/brainstorm/items` | exact | Identical handler or equivalent canonical route exists |
| POST | `/story-development/brainstorm/items/cluster` | POST | `/v1/story-development/brainstorm/items/cluster` | exact | Identical handler or equivalent canonical route exists |
| POST | `/story-development/brainstorm/items/promote` | POST | `/v1/story-development/brainstorm/items/promote` | exact | Identical handler or equivalent canonical route exists |
| POST | `/story-development/branches` | POST | `/v1/story-development/branches` | exact | Identical handler or equivalent canonical route exists |
| POST | `/story-development/branches/active` | POST | `/v1/story-development/branches/active` | exact | Identical handler or equivalent canonical route exists |
| POST | `/story-development/branches/comparisons` | POST | `/v1/story-development/branches/comparisons` | exact | Identical handler or equivalent canonical route exists |
| POST | `/story-development/branches/merge-decisions` | POST | `/v1/story-development/branches/merge-decisions` | exact | Identical handler or equivalent canonical route exists |
| POST | `/story-development/characters` | POST | `/v1/story-development/characters` | exact | Identical handler or equivalent canonical route exists |
| POST | `/story-development/drafting/draft-artifacts` | POST | `/v1/story-development/drafting/draft-artifacts` | exact | Identical handler or equivalent canonical route exists |
| POST | `/story-development/drafting/draft-artifacts/alternate-variant` | POST | `/v1/story-development/drafting/draft-artifacts/alternate-variant` | exact | Identical handler or equivalent canonical route exists |
| POST | `/story-development/drafting/draft-artifacts/continue` | POST | `/v1/story-development/drafting/draft-artifacts/continue` | exact | Identical handler or equivalent canonical route exists |
| POST | `/story-development/drafting/manuscript-documents` | POST | `/v1/story-development/drafting/manuscript-documents` | exact | Identical handler or equivalent canonical route exists |
| POST | `/story-development/drafting/manuscript-documents/{document_id}/review` | POST | `/v1/story-development/drafting/manuscript-documents/{document_id}/review` | exact | Identical handler or equivalent canonical route exists |
| POST | `/story-development/drafting/promote-draft` | POST | `/v1/story-development/drafting/promote-draft` | exact | Identical handler or equivalent canonical route exists |
| POST | `/story-development/drafting/revision-suggestions` | POST | `/v1/story-development/drafting/revision-suggestions` | exact | Identical handler or equivalent canonical route exists |
| POST | `/story-development/flow/stages` | POST | `/v1/story-development/flow/stages` | exact | Identical handler or equivalent canonical route exists |
| POST | `/story-development/flow/stages/init` | POST | `/v1/story-development/flow/stages/init` | exact | Identical handler or equivalent canonical route exists |
| POST | `/story-development/flow/stages/reorder` | POST | `/v1/story-development/flow/stages/reorder` | exact | Identical handler or equivalent canonical route exists |
| POST | `/story-development/foundation` | POST | `/v1/story-development/foundation` | exact | Identical handler or equivalent canonical route exists |
| POST | `/story-development/planning/beat-plans` | POST | `/v1/story-development/planning/beat-plans` | exact | Identical handler or equivalent canonical route exists |
| POST | `/story-development/planning/chapter-packets` | POST | `/v1/story-development/planning/chapter-packets` | exact | Identical handler or equivalent canonical route exists |
| POST | `/story-development/planning/chapter-plans` | POST | `/v1/story-development/planning/chapter-plans` | exact | Identical handler or equivalent canonical route exists |
| POST | `/story-development/planning/reorder` | POST | `/v1/story-development/planning/reorder` | exact | Identical handler or equivalent canonical route exists |
| POST | `/story-development/planning/scene-plans` | POST | `/v1/story-development/planning/scene-plans` | exact | Identical handler or equivalent canonical route exists |
| POST | `/story-development/planning/sequence-plans` | POST | `/v1/story-development/planning/sequence-plans` | exact | Identical handler or equivalent canonical route exists |
| POST | `/story-development/relationships` | POST | `/v1/story-development/relationships` | exact | Identical handler or equivalent canonical route exists |
| POST | `/story-development/review/decisions` | POST | `/v1/story-development/review/decisions` | exact | Identical handler or equivalent canonical route exists |
| POST | `/story-development/review/inspect-links` | POST | `/v1/story-development/review/inspect-links` | exact | Identical handler or equivalent canonical route exists |
| POST | `/story-development/storyboard/cards` | POST | `/v1/story-development/storyboard/cards` | exact | Identical handler or equivalent canonical route exists |
| POST | `/story-development/world-bible` | POST | `/v1/story-development/world-bible` | exact | Identical handler or equivalent canonical route exists |
| PUT | `/story-development/storyboard/cards/{card_id}` | PUT | `/v1/story-development/storyboard/cards/{card_id}` | exact | Identical handler or equivalent canonical route exists |
| PUT | `/story-development/storyboard/cards/{column_id}/reindex` | PUT | `/v1/story-development/storyboard/cards/{column_id}/reindex` | exact | Identical handler or equivalent canonical route exists |
