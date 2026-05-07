# Narrative Engine Database Schema

Auto-generated schema reference. Extracted from `app/persistence/sqlite.py`.

**Regenerate:** `python scripts/generate_schema_doc.py`

## Overview

| Database | Path | Tables |
|----------|------|--------|
| Operations DB | `data/state/narrative_ops.db` | 61 |
| Project DB | `data/projects/{project_id}/bible.db` | 2 |

Operations DB is created on first startup via `ensure_operations_db()`. Project DBs are created per-project.

---

### Operations Database

61 tables

#### `projects`

| Column | Type | Notes |
|--------|------|-------|
| `project_id` | `TEXT PRIMARY KEY` | PK |
| `project_name` | `TEXT NOT NULL` | not null |
| `manifest_path` | `TEXT NOT NULL` | not null |
| `db_path` | `TEXT NOT NULL` | not null |
| `created_at` | `TEXT NOT NULL` | not null |
| `updated_at` | `TEXT NOT NULL` | not null |

#### `project_artifacts`

| Column | Type | Notes |
|--------|------|-------|
| `artifact_id` | `INTEGER PRIMARY KEY AUTOINCREMENT` | PK, autoincrement |
| `project_id` | `TEXT NOT NULL` | not null |
| `artifact_type` | `TEXT NOT NULL` | not null |
| `path` | `TEXT NOT NULL` | not null |
| `content_hash` | `TEXT` | - |
| `size_bytes` | `INTEGER` | - |
| `created_at` | `TEXT NOT NULL` | not null |
| `updated_at` | `TEXT NOT NULL` | not null |

**Foreign Keys:**

- FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE

#### `jobs`

| Column | Type | Notes |
|--------|------|-------|
| `job_id` | `TEXT PRIMARY KEY` | PK |
| `logical_run_id` | `TEXT NOT NULL` | not null |
| `attempt_number` | `INTEGER NOT NULL DEFAULT` | not null, default: 1 |
| `project_id` | `TEXT` | - |
| `phase` | `TEXT NOT NULL` | not null |
| `status` | `TEXT NOT NULL` | not null |
| `payload_json` | `TEXT NOT NULL` | not null |
| `request_json` | `TEXT NOT NULL DEFAULT` | not null, default: '{}' |
| `idempotency_key` | `TEXT` | - |
| `request_hash` | `TEXT NOT NULL DEFAULT` | not null, default: '' |
| `request_scope` | `TEXT NOT NULL DEFAULT` | not null, default: '' |
| `current_phase` | `TEXT` | - |
| `current_step` | `TEXT` | - |
| `detail` | `TEXT` | - |
| `progress_current` | `INTEGER` | - |
| `progress_total` | `INTEGER` | - |
| `heartbeat_at` | `TEXT` | - |
| `lease_owner` | `TEXT` | - |
| `lease_expires_at` | `TEXT` | - |
| `claimed_at` | `TEXT` | - |
| `error` | `TEXT` | - |
| `created_at` | `TEXT NOT NULL` | not null |
| `updated_at` | `TEXT NOT NULL` | not null |

**Foreign Keys:**

- FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE SET NULL

#### `job_logs`

| Column | Type | Notes |
|--------|------|-------|
| `log_id` | `INTEGER PRIMARY KEY AUTOINCREMENT` | PK, autoincrement |
| `job_id` | `TEXT NOT NULL` | not null |
| `timestamp` | `TEXT NOT NULL` | not null |
| `level` | `TEXT NOT NULL` | not null |
| `message` | `TEXT NOT NULL` | not null |

**Foreign Keys:**

- FOREIGN KEY(job_id) REFERENCES jobs(job_id) ON DELETE CASCADE

#### `job_attempts`

| Column | Type | Notes |
|--------|------|-------|
| `attempt_id` | `INTEGER PRIMARY KEY AUTOINCREMENT` | PK, autoincrement |
| `job_id` | `TEXT NOT NULL` | not null |
| `logical_run_id` | `TEXT NOT NULL` | not null |
| `attempt_number` | `INTEGER NOT NULL` | not null |
| `status` | `TEXT NOT NULL` | not null |
| `executor_name` | `TEXT` | - |
| `executor_instance_id` | `TEXT` | - |
| `queue_delay_ms` | `INTEGER` | - |
| `lease_owner` | `TEXT` | - |
| `lease_expires_at` | `TEXT` | - |
| `claimed_at` | `TEXT` | - |
| `started_at` | `TEXT` | - |
| `finished_at` | `TEXT` | - |
| `last_heartbeat_at` | `TEXT` | - |
| `finish_reason` | `TEXT` | - |
| `failure_stage` | `TEXT` | - |
| `retryable` | `INTEGER` | - |
| `retry_reason` | `TEXT` | - |
| `error_code` | `TEXT` | - |
| `error_category` | `TEXT` | - |
| `created_at` | `TEXT NOT NULL` | not null |
| `updated_at` | `TEXT NOT NULL` | not null |

**Foreign Keys:**

- FOREIGN KEY(job_id) REFERENCES jobs(job_id) ON DELETE CASCADE

#### `job_events`

| Column | Type | Notes |
|--------|------|-------|
| `event_id` | `INTEGER PRIMARY KEY AUTOINCREMENT` | PK, autoincrement |
| `job_id` | `TEXT NOT NULL` | not null |
| `logical_run_id` | `TEXT NOT NULL` | not null |
| `attempt_number` | `INTEGER NOT NULL DEFAULT` | not null, default: 1 |
| `event_type` | `TEXT NOT NULL` | not null |
| `from_state` | `TEXT` | - |
| `to_state` | `TEXT` | - |
| `occurred_at` | `TEXT NOT NULL` | not null |
| `payload_json` | `TEXT NOT NULL DEFAULT` | not null, default: '{}' |

**Foreign Keys:**

- FOREIGN KEY(job_id) REFERENCES jobs(job_id) ON DELETE CASCADE

#### `checker_runs`

| Column | Type | Notes |
|--------|------|-------|
| `run_id` | `TEXT PRIMARY KEY` | PK |
| `logical_run_id` | `TEXT NOT NULL` | not null |
| `attempt_number` | `INTEGER NOT NULL DEFAULT` | not null, default: 1 |
| `project_id` | `TEXT` | - |
| `status` | `TEXT NOT NULL` | not null |
| `request_json` | `TEXT NOT NULL DEFAULT` | not null, default: '{}' |
| `idempotency_key` | `TEXT` | - |
| `request_hash` | `TEXT NOT NULL DEFAULT` | not null, default: '' |
| `request_scope` | `TEXT NOT NULL DEFAULT` | not null, default: '' |
| `current_role` | `TEXT` | - |
| `detail` | `TEXT` | - |
| `heartbeat_at` | `TEXT` | - |
| `lease_owner` | `TEXT` | - |
| `lease_expires_at` | `TEXT` | - |
| `claimed_at` | `TEXT` | - |
| `report_path` | `TEXT` | - |
| `created_at` | `TEXT NOT NULL` | not null |
| `updated_at` | `TEXT NOT NULL` | not null |

**Foreign Keys:**

- FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE SET NULL

#### `checker_results`

| Column | Type | Notes |
|--------|------|-------|
| `result_id` | `INTEGER PRIMARY KEY AUTOINCREMENT` | PK, autoincrement |
| `run_id` | `TEXT NOT NULL` | not null |
| `role` | `TEXT NOT NULL` | not null |
| `passed` | `INTEGER NOT NULL` | not null |
| `duration_seconds` | `REAL NOT NULL` | not null |
| `findings_json` | `TEXT NOT NULL` | not null |
| `warnings_json` | `TEXT NOT NULL` | not null |
| `preview` | `TEXT` | - |
| `metadata_json` | `TEXT NOT NULL` | not null |

**Foreign Keys:**

- FOREIGN KEY(run_id) REFERENCES checker_runs(run_id) ON DELETE CASCADE

#### `checker_run_attempts`

| Column | Type | Notes |
|--------|------|-------|
| `attempt_id` | `INTEGER PRIMARY KEY AUTOINCREMENT` | PK, autoincrement |
| `run_id` | `TEXT NOT NULL` | not null |
| `logical_run_id` | `TEXT NOT NULL` | not null |
| `attempt_number` | `INTEGER NOT NULL` | not null |
| `status` | `TEXT NOT NULL` | not null |
| `executor_name` | `TEXT` | - |
| `executor_instance_id` | `TEXT` | - |
| `queue_delay_ms` | `INTEGER` | - |
| `lease_owner` | `TEXT` | - |
| `lease_expires_at` | `TEXT` | - |
| `claimed_at` | `TEXT` | - |
| `started_at` | `TEXT` | - |
| `finished_at` | `TEXT` | - |
| `last_heartbeat_at` | `TEXT` | - |
| `finish_reason` | `TEXT` | - |
| `failure_stage` | `TEXT` | - |
| `retryable` | `INTEGER` | - |
| `retry_reason` | `TEXT` | - |
| `error_code` | `TEXT` | - |
| `error_category` | `TEXT` | - |
| `created_at` | `TEXT NOT NULL` | not null |
| `updated_at` | `TEXT NOT NULL` | not null |

**Foreign Keys:**

- FOREIGN KEY(run_id) REFERENCES checker_runs(run_id) ON DELETE CASCADE

#### `checker_run_events`

| Column | Type | Notes |
|--------|------|-------|
| `event_id` | `INTEGER PRIMARY KEY AUTOINCREMENT` | PK, autoincrement |
| `run_id` | `TEXT NOT NULL` | not null |
| `logical_run_id` | `TEXT NOT NULL` | not null |
| `attempt_number` | `INTEGER NOT NULL DEFAULT` | not null, default: 1 |
| `event_type` | `TEXT NOT NULL` | not null |
| `from_state` | `TEXT` | - |
| `to_state` | `TEXT` | - |
| `occurred_at` | `TEXT NOT NULL` | not null |
| `payload_json` | `TEXT NOT NULL DEFAULT` | not null, default: '{}' |

**Foreign Keys:**

- FOREIGN KEY(run_id) REFERENCES checker_runs(run_id) ON DELETE CASCADE

#### `step_records`

| Column | Type | Notes |
|--------|------|-------|
| `step_record_id` | `INTEGER PRIMARY KEY AUTOINCREMENT` | PK, autoincrement |
| `logical_run_id` | `TEXT NOT NULL` | not null |
| `run_id` | `TEXT NOT NULL` | not null |
| `run_kind` | `TEXT NOT NULL` | not null |
| `attempt_number` | `INTEGER NOT NULL` | not null |
| `step_name` | `TEXT NOT NULL` | not null |
| `step_index` | `INTEGER NOT NULL` | not null |
| `state` | `TEXT NOT NULL` | not null |
| `project_id` | `TEXT` | - |
| `model_id` | `TEXT` | - |
| `critic_profile` | `TEXT` | - |
| `backend_name` | `TEXT` | - |
| `backend_version` | `TEXT` | - |
| `input_hash` | `TEXT` | - |
| `output_hash` | `TEXT` | - |
| `prompt_hash` | `TEXT` | - |
| `input_artifact_refs_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `output_artifact_refs_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `started_at` | `TEXT` | - |
| `finished_at` | `TEXT` | - |
| `duration_seconds` | `REAL` | - |
| `finish_reason` | `TEXT` | - |
| `error_code` | `TEXT` | - |
| `error_category` | `TEXT` | - |
| `executor_id` | `TEXT` | - |
| `lease_owner` | `TEXT` | - |
| `created_at` | `TEXT NOT NULL` | not null |
| `updated_at` | `TEXT NOT NULL` | not null |

#### `artifact_lineage`

| Column | Type | Notes |
|--------|------|-------|
| `artifact_lineage_id` | `INTEGER PRIMARY KEY AUTOINCREMENT` | PK, autoincrement |
| `logical_run_id` | `TEXT NOT NULL` | not null |
| `run_id` | `TEXT NOT NULL` | not null |
| `run_kind` | `TEXT NOT NULL` | not null |
| `attempt_number` | `INTEGER NOT NULL` | not null |
| `step_name` | `TEXT NOT NULL` | not null |
| `project_id` | `TEXT` | - |
| `artifact_role` | `TEXT NOT NULL` | not null |
| `artifact_kind` | `TEXT NOT NULL` | not null |
| `path` | `TEXT NOT NULL` | not null |
| `content_hash` | `TEXT` | - |
| `status` | `TEXT NOT NULL` | not null |
| `validation_state` | `TEXT NOT NULL` | not null |
| `produced_at` | `TEXT NOT NULL` | not null |
| `registered_at` | `TEXT` | - |
| `supersedes_artifact_lineage_id` | `INTEGER` | - |
| `source_artifact_refs_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `source_content_hashes_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `output_of_step_record_id` | `INTEGER NOT NULL` | not null |

**Foreign Keys:**

- FOREIGN KEY(supersedes_artifact_lineage_id) REFERENCES artifact_lineage(artifact_lineage_id) ON DELETE SET NULL
- FOREIGN KEY(output_of_step_record_id) REFERENCES step_records(step_record_id) ON DELETE CASCADE

#### `runtime_artifact_selections`

| Column | Type | Notes |
|--------|------|-------|
| `selection_id` | `INTEGER PRIMARY KEY AUTOINCREMENT` | PK, autoincrement |
| `logical_run_id` | `TEXT NOT NULL` | not null |
| `run_id` | `TEXT NOT NULL` | not null |
| `run_kind` | `TEXT NOT NULL` | not null |
| `attempt_number` | `INTEGER NOT NULL` | not null |
| `step_name` | `TEXT NOT NULL` | not null |
| `project_id` | `TEXT` | - |
| `artifact_role` | `TEXT NOT NULL` | not null |
| `selected_artifact_lineage_id` | `INTEGER` | - |
| `selected_path` | `TEXT` | - |
| `selected_content_hash` | `TEXT NOT NULL` | not null |
| `selected_content` | `TEXT NOT NULL` | not null |
| `selected_at` | `TEXT NOT NULL` | not null |

**Foreign Keys:**

- FOREIGN KEY(selected_artifact_lineage_id) REFERENCES artifact_lineage(artifact_lineage_id) ON DELETE SET NULL

#### `story_flow_definitions`

| Column | Type | Notes |
|--------|------|-------|
| `project_id` | `TEXT PRIMARY KEY` | PK |
| `flow_name` | `TEXT NOT NULL` | not null |
| `flow_notes` | `TEXT` | - |
| `created_at` | `TEXT NOT NULL` | not null |
| `updated_at` | `TEXT NOT NULL` | not null |

**Foreign Keys:**

- FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE

#### `story_flow_stages`

| Column | Type | Notes |
|--------|------|-------|
| `stage_id` | `INTEGER PRIMARY KEY AUTOINCREMENT` | PK, autoincrement |
| `project_id` | `TEXT NOT NULL` | not null |
| `stage_key` | `TEXT NOT NULL` | not null |
| `stage_kind` | `TEXT NOT NULL` | not null |
| `is_custom` | `INTEGER NOT NULL DEFAULT` | not null, default: 0 |
| `display_name` | `TEXT NOT NULL` | not null |
| `description` | `TEXT` | - |
| `position` | `INTEGER NOT NULL` | not null |
| `depends_on_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `stage_configuration_state` | `TEXT NOT NULL` | not null |
| `stage_progress_state` | `TEXT NOT NULL` | not null |
| `writer_notes` | `TEXT` | - |
| `custom_prompt_guidance` | `TEXT` | - |
| `created_at` | `TEXT NOT NULL` | not null |
| `updated_at` | `TEXT NOT NULL` | not null |

**Foreign Keys:**

- FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE

#### `brainstorm_items`

| Column | Type | Notes |
|--------|------|-------|
| `item_id` | `INTEGER PRIMARY KEY AUTOINCREMENT` | PK, autoincrement |
| `project_id` | `TEXT NOT NULL` | not null |
| `cluster_key` | `TEXT` | - |
| `content` | `TEXT NOT NULL` | not null |
| `item_state` | `TEXT NOT NULL` | not null |
| `tags_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `source_artifact_refs_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `created_at` | `TEXT NOT NULL` | not null |
| `updated_at` | `TEXT NOT NULL` | not null |

**Foreign Keys:**

- FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE

#### `brain_dump_sessions`

| Column | Type | Notes |
|--------|------|-------|
| `session_id` | `INTEGER PRIMARY KEY AUTOINCREMENT` | PK, autoincrement |
| `project_id` | `TEXT NOT NULL` | not null |
| `title` | `TEXT` | - |
| `raw_text` | `TEXT NOT NULL DEFAULT` | not null, default: '' |
| `state` | `TEXT NOT NULL DEFAULT` | not null, default: 'active' |
| `created_at` | `TEXT NOT NULL` | not null |
| `updated_at` | `TEXT NOT NULL` | not null |

**Foreign Keys:**

- FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE

#### `foundation_profiles`

| Column | Type | Notes |
|--------|------|-------|
| `project_id` | `TEXT PRIMARY KEY` | PK |
| `current_revision_id` | `INTEGER` | - |
| `created_at` | `TEXT NOT NULL` | not null |
| `updated_at` | `TEXT NOT NULL` | not null |

**Foreign Keys:**

- FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE

#### `foundation_revisions`

| Column | Type | Notes |
|--------|------|-------|
| `revision_id` | `INTEGER PRIMARY KEY AUTOINCREMENT` | PK, autoincrement |
| `project_id` | `TEXT NOT NULL` | not null |
| `revision_number` | `INTEGER NOT NULL` | not null |
| `premise` | `TEXT NOT NULL` | not null |
| `logline` | `TEXT NOT NULL` | not null |
| `thematic_spine` | `TEXT` | - |
| `emotional_promise` | `TEXT` | - |
| `tone_direction` | `TEXT` | - |
| `target_audience` | `TEXT` | - |
| `narrative_constraints_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `complexity_level` | `TEXT` | - |
| `success_definition` | `TEXT` | - |
| `created_at` | `TEXT NOT NULL` | not null |
| `updated_at` | `TEXT NOT NULL` | not null |

**Foreign Keys:**

- FOREIGN KEY(project_id) REFERENCES foundation_profiles(project_id) ON DELETE CASCADE

#### `character_profiles`

| Column | Type | Notes |
|--------|------|-------|
| `character_id` | `TEXT PRIMARY KEY` | PK |
| `project_id` | `TEXT NOT NULL` | not null |
| `display_name` | `TEXT NOT NULL` | not null |
| `role_in_story` | `TEXT` | - |
| `archetype` | `TEXT` | - |
| `external_goal` | `TEXT` | - |
| `internal_need` | `TEXT` | - |
| `misbelief_or_wound` | `TEXT` | - |
| `core_fear` | `TEXT` | - |
| `primary_strength` | `TEXT` | - |
| `fatal_flaw_or_limitation` | `TEXT` | - |
| `contradictions_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `backstory_summary` | `TEXT` | - |
| `voice_notes` | `TEXT` | - |
| `relationship_map_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `secrets_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `values_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `taboos_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `change_axis` | `TEXT` | - |
| `arc_stage_notes` | `TEXT` | - |
| `continuity_facts_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `writer_notes` | `TEXT` | - |
| `aliases_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `physical_description` | `TEXT` | - |
| `personality_traits_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `motives` | `TEXT` | - |
| `relationships_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `character_arc` | `TEXT` | - |
| `symbolic_role` | `TEXT` | - |
| `dialogue_patterns` | `TEXT` | - |
| `psychological_depth` | `TEXT` | - |
| `narrative_purpose` | `TEXT` | - |
| `thematic_significance` | `TEXT` | - |
| `impact_on_others` | `TEXT` | - |
| `first_appearance_chapter` | `TEXT` | - |
| `chapter_appearances_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `created_at` | `TEXT NOT NULL` | not null |
| `updated_at` | `TEXT NOT NULL` | not null |

**Foreign Keys:**

- FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE

#### `relationship_edges`

| Column | Type | Notes |
|--------|------|-------|
| `edge_id` | `TEXT PRIMARY KEY` | PK |
| `project_id` | `TEXT NOT NULL` | not null |
| `source_character_id` | `TEXT NOT NULL` | not null |
| `target_character_id` | `TEXT NOT NULL` | not null |
| `relation_kind` | `TEXT NOT NULL` | not null |
| `summary` | `TEXT NOT NULL` | not null |
| `tension` | `TEXT` | - |
| `notes` | `TEXT` | - |
| `created_at` | `TEXT NOT NULL` | not null |
| `updated_at` | `TEXT NOT NULL` | not null |

**Foreign Keys:**

- FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE
- FOREIGN KEY(source_character_id) REFERENCES character_profiles(character_id) ON DELETE CASCADE
- FOREIGN KEY(target_character_id) REFERENCES character_profiles(character_id) ON DELETE CASCADE

#### `world_bible_entries`

| Column | Type | Notes |
|--------|------|-------|
| `entry_id` | `INTEGER PRIMARY KEY AUTOINCREMENT` | PK, autoincrement |
| `project_id` | `TEXT NOT NULL` | not null |
| `entry_type` | `TEXT NOT NULL` | not null |
| `title` | `TEXT NOT NULL` | not null |
| `summary` | `TEXT` | - |
| `canonical_facts_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `related_character_ids_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `visibility_scope` | `TEXT NOT NULL DEFAULT` | not null, default: 'project' |
| `source_artifacts_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `continuity_warnings_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `writer_notes` | `TEXT` | - |
| `created_at` | `TEXT NOT NULL` | not null |
| `updated_at` | `TEXT NOT NULL` | not null |

**Foreign Keys:**

- FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE

#### `arc_candidates`

| Column | Type | Notes |
|--------|------|-------|
| `arc_id` | `TEXT PRIMARY KEY` | PK |
| `project_id` | `TEXT NOT NULL` | not null |
| `name` | `TEXT NOT NULL` | not null |
| `summary` | `TEXT NOT NULL` | not null |
| `stage_map_notes_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `fit_notes_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `tags_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `created_at` | `TEXT NOT NULL` | not null |
| `updated_at` | `TEXT NOT NULL` | not null |

**Foreign Keys:**

- FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE

#### `arc_stage_maps`

| Column | Type | Notes |
|--------|------|-------|
| `arc_stage_map_id` | `TEXT PRIMARY KEY` | PK |
| `project_id` | `TEXT NOT NULL` | not null |
| `arc_id` | `TEXT NOT NULL` | not null |
| `stage_kinds_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `notes` | `TEXT` | - |
| `created_at` | `TEXT NOT NULL` | not null |
| `updated_at` | `TEXT NOT NULL` | not null |

**Foreign Keys:**

- FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE
- FOREIGN KEY(arc_id) REFERENCES arc_candidates(arc_id) ON DELETE CASCADE

#### `arc_selections`

| Column | Type | Notes |
|--------|------|-------|
| `selection_id` | `TEXT PRIMARY KEY` | PK |
| `project_id` | `TEXT NOT NULL` | not null |
| `selected_arc_id` | `TEXT` | - |
| `selected_arc_json` | `TEXT NOT NULL` | not null |
| `rejected_candidate_ids_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `comparison_notes_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `stage_map_id` | `TEXT` | - |
| `created_at` | `TEXT NOT NULL` | not null |
| `updated_at` | `TEXT NOT NULL` | not null |

**Foreign Keys:**

- FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE
- FOREIGN KEY(selected_arc_id) REFERENCES arc_candidates(arc_id) ON DELETE SET NULL
- FOREIGN KEY(stage_map_id) REFERENCES arc_stage_maps(arc_stage_map_id) ON DELETE SET NULL

#### `arc_comparisons`

| Column | Type | Notes |
|--------|------|-------|
| `comparison_id` | `TEXT PRIMARY KEY` | PK |
| `project_id` | `TEXT NOT NULL` | not null |
| `candidate_ids_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `candidate_set_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `ranked_candidates_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `review_notes_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `created_at` | `TEXT NOT NULL` | not null |
| `updated_at` | `TEXT NOT NULL` | not null |

**Foreign Keys:**

- FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE

#### `arc_selection_comparisons`

| Column | Type | Notes |
|--------|------|-------|
| `selection_id` | `TEXT NOT NULL` | not null |
| `comparison_id` | `TEXT NOT NULL` | not null |
| `link_order` | `INTEGER NOT NULL` | not null |
| `created_at` | `TEXT NOT NULL` | not null |
| `updated_at` | `TEXT NOT NULL` | not null |
| `PRIMARY` | `KEY(selection_id, comparison_id)` | PK |

**Foreign Keys:**

- FOREIGN KEY(selection_id) REFERENCES arc_selections(selection_id) ON DELETE CASCADE
- FOREIGN KEY(comparison_id) REFERENCES arc_comparisons(comparison_id) ON DELETE CASCADE

#### `story_decision_nodes`

| Column | Type | Notes |
|--------|------|-------|
| `node_record_id` | `INTEGER PRIMARY KEY AUTOINCREMENT` | PK, autoincrement |
| `node_id` | `TEXT NOT NULL` | not null |
| `project_id` | `TEXT NOT NULL` | not null |
| `node_type` | `TEXT NOT NULL` | not null |
| `change_type` | `TEXT NOT NULL` | not null |
| `subject_type` | `TEXT NOT NULL` | not null |
| `subject_id` | `TEXT NOT NULL` | not null |
| `parent_node_id` | `TEXT` | - |
| `branch_id` | `TEXT` | - |
| `summary` | `TEXT NOT NULL` | not null |
| `prior_state_ref` | `TEXT` | - |
| `prior_state_summary` | `TEXT` | - |
| `new_state_ref` | `TEXT` | - |
| `new_state_summary` | `TEXT` | - |
| `reason_or_note` | `TEXT` | - |
| `decision_made_at` | `TEXT NOT NULL` | not null |
| `made_by` | `TEXT NOT NULL` | not null |
| `related_object_links_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `informing_object_links_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `created_at` | `TEXT NOT NULL` | not null |
| `updated_at` | `TEXT NOT NULL` | not null |

**Foreign Keys:**

- FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE

#### `branch_points`

| Column | Type | Notes |
|--------|------|-------|
| `branch_point_id` | `TEXT PRIMARY KEY` | PK |
| `project_id` | `TEXT NOT NULL` | not null |
| `source_node_id` | `TEXT NOT NULL` | not null |
| `created_at` | `TEXT NOT NULL` | not null |
| `updated_at` | `TEXT NOT NULL` | not null |

**Foreign Keys:**

- FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE
- FOREIGN KEY(project_id, source_node_id) REFERENCES story_decision_nodes(project_id, node_id) ON DELETE CASCADE

#### `story_branches`

| Column | Type | Notes |
|--------|------|-------|
| `branch_id` | `TEXT PRIMARY KEY` | PK |
| `project_id` | `TEXT NOT NULL` | not null |
| `branch_point_id` | `TEXT NOT NULL` | not null |
| `branch_name` | `TEXT NOT NULL` | not null |
| `branch_state` | `TEXT NOT NULL` | not null |
| `created_at` | `TEXT NOT NULL` | not null |
| `updated_at` | `TEXT NOT NULL` | not null |

**Foreign Keys:**

- FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE
- FOREIGN KEY(project_id, branch_point_id) REFERENCES branch_points(project_id, branch_point_id) ON DELETE CASCADE

#### `branch_state_refs`

| Column | Type | Notes |
|--------|------|-------|
| `branch_state_ref_id` | `TEXT PRIMARY KEY` | PK |
| `project_id` | `TEXT NOT NULL` | not null |
| `branch_id` | `TEXT NOT NULL` | not null |
| `state_object_type` | `TEXT NOT NULL` | not null |
| `state_object_id` | `TEXT NOT NULL` | not null |
| `decision_node_id` | `TEXT` | - |
| `created_at` | `TEXT NOT NULL` | not null |
| `updated_at` | `TEXT NOT NULL` | not null |

**Foreign Keys:**

- FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE
- FOREIGN KEY(project_id, branch_id) REFERENCES story_branches(project_id, branch_id) ON DELETE CASCADE
- FOREIGN KEY(project_id, decision_node_id) REFERENCES story_decision_nodes(project_id, node_id) ON DELETE SET NULL

#### `branch_comparisons`

| Column | Type | Notes |
|--------|------|-------|
| `comparison_id` | `TEXT PRIMARY KEY` | PK |
| `project_id` | `TEXT NOT NULL` | not null |
| `source_branch_id` | `TEXT NOT NULL` | not null |
| `target_branch_id` | `TEXT NOT NULL` | not null |
| `review_notes_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `created_at` | `TEXT NOT NULL` | not null |
| `updated_at` | `TEXT NOT NULL` | not null |

**Foreign Keys:**

- FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE
- FOREIGN KEY(source_branch_id) REFERENCES story_branches(branch_id) ON DELETE CASCADE
- FOREIGN KEY(target_branch_id) REFERENCES story_branches(branch_id) ON DELETE CASCADE

#### `branch_merge_decisions`

| Column | Type | Notes |
|--------|------|-------|
| `merge_decision_id` | `TEXT PRIMARY KEY` | PK |
| `project_id` | `TEXT NOT NULL` | not null |
| `source_branch_id` | `TEXT NOT NULL` | not null |
| `target_branch_id` | `TEXT NOT NULL` | not null |
| `merge_rationale` | `TEXT NOT NULL` | not null |
| `resulting_decision_node_ids_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `created_at` | `TEXT NOT NULL` | not null |
| `updated_at` | `TEXT NOT NULL` | not null |

**Foreign Keys:**

- FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE
- FOREIGN KEY(project_id, source_branch_id) REFERENCES story_branches(project_id, branch_id) ON DELETE CASCADE
- FOREIGN KEY(project_id, target_branch_id) REFERENCES story_branches(project_id, branch_id) ON DELETE CASCADE

#### `checker_findings`

| Column | Type | Notes |
|--------|------|-------|
| `finding_id` | `TEXT PRIMARY KEY` | PK |
| `project_id` | `TEXT NOT NULL` | not null |
| `source_object_id` | `TEXT NOT NULL` | not null |
| `source_object_kind` | `TEXT NOT NULL` | not null |
| `severity` | `TEXT NOT NULL` | not null |
| `summary` | `TEXT NOT NULL` | not null |
| `details` | `TEXT` | - |
| `source_context_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `created_at` | `TEXT NOT NULL` | not null |
| `updated_at` | `TEXT NOT NULL` | not null |

**Foreign Keys:**

- FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE

#### `review_decisions`

| Column | Type | Notes |
|--------|------|-------|
| `decision_id` | `TEXT PRIMARY KEY` | PK |
| `project_id` | `TEXT NOT NULL` | not null |
| `target_id` | `TEXT NOT NULL` | not null |
| `target_kind` | `TEXT NOT NULL` | not null |
| `decision` | `TEXT NOT NULL` | not null |
| `notes` | `TEXT` | - |
| `source_context_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `created_at` | `TEXT NOT NULL` | not null |
| `updated_at` | `TEXT NOT NULL` | not null |

**Foreign Keys:**

- FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE

#### `inspect_run_links`

| Column | Type | Notes |
|--------|------|-------|
| `link_id` | `TEXT PRIMARY KEY` | PK |
| `project_id` | `TEXT NOT NULL` | not null |
| `object_kind` | `TEXT NOT NULL` | not null |
| `object_id` | `TEXT NOT NULL` | not null |
| `logical_run_id` | `TEXT NOT NULL` | not null |
| `run_id` | `TEXT NOT NULL` | not null |
| `run_kind` | `TEXT NOT NULL` | not null |
| `attempt_number` | `INTEGER` | - |
| `label` | `TEXT` | - |
| `created_at` | `TEXT NOT NULL` | not null |
| `updated_at` | `TEXT NOT NULL` | not null |

**Foreign Keys:**

- FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE

#### `draft_artifacts`

| Column | Type | Notes |
|--------|------|-------|
| `artifact_id` | `TEXT PRIMARY KEY` | PK |
| `project_id` | `TEXT NOT NULL` | not null |
| `title` | `TEXT NOT NULL` | not null |
| `content` | `TEXT NOT NULL` | not null |
| `source_plan_ids_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `source_context_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `provenance_note` | `TEXT` | - |
| `status` | `TEXT NOT NULL DEFAULT` | not null, default: 'DRAFT' |
| `created_at` | `TEXT NOT NULL` | not null |
| `updated_at` | `TEXT NOT NULL` | not null |

**Foreign Keys:**

- FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE

#### `manuscript_documents`

| Column | Type | Notes |
|--------|------|-------|
| `document_id` | `TEXT PRIMARY KEY` | PK |
| `project_id` | `TEXT NOT NULL` | not null |
| `title` | `TEXT NOT NULL` | not null |
| `content` | `TEXT NOT NULL` | not null |
| `chapter_id` | `TEXT` | - |
| `scene_id` | `TEXT` | - |
| `current_draft_artifact_id` | `TEXT` | - |
| `version` | `INTEGER NOT NULL DEFAULT` | not null, default: 1 |
| `created_at` | `TEXT NOT NULL` | not null |
| `updated_at` | `TEXT NOT NULL` | not null |

**Foreign Keys:**

- FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE
- FOREIGN KEY(chapter_id) REFERENCES chapter_plans(chapter_id) ON DELETE SET NULL
- FOREIGN KEY(scene_id) REFERENCES scene_plans(scene_id) ON DELETE SET NULL
- FOREIGN KEY(current_draft_artifact_id) REFERENCES draft_artifacts(artifact_id) ON DELETE SET NULL

#### `revision_suggestions`

| Column | Type | Notes |
|--------|------|-------|
| `suggestion_id` | `TEXT PRIMARY KEY` | PK |
| `project_id` | `TEXT NOT NULL` | not null |
| `target_document_id` | `TEXT NOT NULL` | not null |
| `source_text` | `TEXT NOT NULL` | not null |
| `proposed_text` | `TEXT NOT NULL` | not null |
| `rationale` | `TEXT NOT NULL` | not null |
| `source_context_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `status` | `TEXT NOT NULL DEFAULT` | not null, default: 'REQUESTED' |
| `created_at` | `TEXT NOT NULL` | not null |
| `updated_at` | `TEXT NOT NULL` | not null |

**Foreign Keys:**

- FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE
- FOREIGN KEY(target_document_id) REFERENCES manuscript_documents(document_id) ON DELETE CASCADE

#### `beat_plans`

| Column | Type | Notes |
|--------|------|-------|
| `beat_id` | `TEXT PRIMARY KEY` | PK |
| `project_id` | `TEXT NOT NULL` | not null |
| `objective` | `TEXT NOT NULL` | not null |
| `conflict` | `TEXT NOT NULL` | not null |
| `stakes` | `TEXT NOT NULL` | not null |
| `dependency_ids_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `arc_stage` | `TEXT NOT NULL` | not null |
| `active_character_ids_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `continuity_requirements_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `unresolved_questions_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `status` | `TEXT NOT NULL DEFAULT` | not null, default: 'draft' |
| `position` | `INTEGER NOT NULL DEFAULT` | not null, default: 0 |
| `provenance_note` | `TEXT` | - |
| `confidence_score` | `REAL NOT NULL DEFAULT` | not null, default: 0.0 |
| `created_at` | `TEXT NOT NULL` | not null |
| `updated_at` | `TEXT NOT NULL` | not null |

**Foreign Keys:**

- FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE

#### `sequence_plans`

| Column | Type | Notes |
|--------|------|-------|
| `sequence_id` | `TEXT PRIMARY KEY` | PK |
| `project_id` | `TEXT NOT NULL` | not null |
| `title` | `TEXT NOT NULL` | not null |
| `summary` | `TEXT NOT NULL` | not null |
| `beat_ids_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `chapter_ids_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `status` | `TEXT NOT NULL DEFAULT` | not null, default: 'draft' |
| `position` | `INTEGER NOT NULL DEFAULT` | not null, default: 0 |
| `provenance_note` | `TEXT` | - |
| `confidence_score` | `REAL NOT NULL DEFAULT` | not null, default: 0.0 |
| `created_at` | `TEXT NOT NULL` | not null |
| `updated_at` | `TEXT NOT NULL` | not null |

**Foreign Keys:**

- FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE

#### `storyboard_cards`

| Column | Type | Notes |
|--------|------|-------|
| `card_id` | `TEXT PRIMARY KEY` | PK |
| `project_id` | `TEXT NOT NULL` | not null |
| `title` | `TEXT NOT NULL` | not null |
| `content` | `TEXT NOT NULL` | not null |
| `card_type` | `TEXT NOT NULL DEFAULT` | not null, default: 'idea' |
| `column_id` | `TEXT` | - |
| `position` | `INTEGER NOT NULL DEFAULT` | not null, default: 0 |
| `tags` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `character_ids` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `dependencies` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `metadata` | `TEXT NOT NULL DEFAULT` | not null, default: '{}' |
| `created_at` | `TEXT NOT NULL` | not null |
| `updated_at` | `TEXT NOT NULL` | not null |

#### `chapter_plans`

| Column | Type | Notes |
|--------|------|-------|
| `chapter_id` | `TEXT PRIMARY KEY` | PK |
| `project_id` | `TEXT NOT NULL` | not null |
| `sequence_id` | `TEXT` | - |
| `title` | `TEXT NOT NULL` | not null |
| `summary` | `TEXT NOT NULL` | not null |
| `objective` | `TEXT NOT NULL` | not null |
| `conflict` | `TEXT NOT NULL` | not null |
| `stakes` | `TEXT NOT NULL` | not null |
| `active_character_ids_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `continuity_requirements_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `unresolved_questions_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `status` | `TEXT NOT NULL DEFAULT` | not null, default: 'draft' |
| `position` | `INTEGER NOT NULL DEFAULT` | not null, default: 0 |
| `provenance_note` | `TEXT` | - |
| `confidence_score` | `REAL NOT NULL DEFAULT` | not null, default: 0.0 |
| `created_at` | `TEXT NOT NULL` | not null |
| `updated_at` | `TEXT NOT NULL` | not null |
| `target_word_count` | `INTEGER` | - |

**Foreign Keys:**

- FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE
- FOREIGN KEY(sequence_id) REFERENCES sequence_plans(sequence_id) ON DELETE SET NULL

#### `scene_plans`

| Column | Type | Notes |
|--------|------|-------|
| `scene_id` | `TEXT PRIMARY KEY` | PK |
| `project_id` | `TEXT NOT NULL` | not null |
| `chapter_id` | `TEXT` | - |
| `title` | `TEXT NOT NULL` | not null |
| `summary` | `TEXT NOT NULL` | not null |
| `objective` | `TEXT NOT NULL` | not null |
| `conflict` | `TEXT NOT NULL` | not null |
| `stakes` | `TEXT NOT NULL` | not null |
| `active_character_ids_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `continuity_requirements_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `unresolved_questions_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `status` | `TEXT NOT NULL DEFAULT` | not null, default: 'draft' |
| `position` | `INTEGER NOT NULL DEFAULT` | not null, default: 0 |
| `provenance_note` | `TEXT` | - |
| `confidence_score` | `REAL NOT NULL DEFAULT` | not null, default: 0.0 |
| `created_at` | `TEXT NOT NULL` | not null |
| `updated_at` | `TEXT NOT NULL` | not null |

**Foreign Keys:**

- FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE
- FOREIGN KEY(chapter_id) REFERENCES chapter_plans(chapter_id) ON DELETE SET NULL

#### `chapter_packets`

| Column | Type | Notes |
|--------|------|-------|
| `packet_id` | `TEXT PRIMARY KEY` | PK |
| `project_id` | `TEXT NOT NULL` | not null |
| `chapter_id` | `TEXT NOT NULL` | not null |
| `included_reference_ids_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `constraints_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `scene_goals_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `status` | `TEXT NOT NULL DEFAULT` | not null, default: 'draft' |
| `provenance_note` | `TEXT` | - |
| `confidence_score` | `REAL NOT NULL DEFAULT` | not null, default: 0.0 |
| `created_at` | `TEXT NOT NULL` | not null |
| `updated_at` | `TEXT NOT NULL` | not null |

**Foreign Keys:**

- FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE
- FOREIGN KEY(chapter_id) REFERENCES chapter_plans(chapter_id) ON DELETE CASCADE

#### `planning_dependencies`

| Column | Type | Notes |
|--------|------|-------|
| `dependency_id` | `TEXT PRIMARY KEY` | PK |
| `project_id` | `TEXT NOT NULL` | not null |
| `upstream_id` | `TEXT NOT NULL` | not null |
| `downstream_id` | `TEXT NOT NULL` | not null |
| `dependency_kind` | `TEXT NOT NULL` | not null |
| `reason` | `TEXT` | - |
| `created_at` | `TEXT NOT NULL` | not null |
| `updated_at` | `TEXT NOT NULL` | not null |

**Foreign Keys:**

- FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE

#### `continuity_threads`

| Column | Type | Notes |
|--------|------|-------|
| `thread_id` | `TEXT PRIMARY KEY` | PK |
| `project_id` | `TEXT NOT NULL` | not null |
| `title` | `TEXT NOT NULL` | not null |
| `summary` | `TEXT NOT NULL DEFAULT` | not null, default: '' |
| `status` | `TEXT NOT NULL DEFAULT` | not null, default: 'active' |
| `chapter_ids_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `character_ids_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `evidence_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `provenance_note` | `TEXT` | - |
| `confidence_score` | `REAL NOT NULL DEFAULT` | not null, default: 0.0 |
| `created_at` | `TEXT NOT NULL` | not null |
| `updated_at` | `TEXT NOT NULL` | not null |

**Foreign Keys:**

- FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE

#### `continuity_states`

| Column | Type | Notes |
|--------|------|-------|
| `state_id` | `TEXT PRIMARY KEY` | PK |
| `project_id` | `TEXT NOT NULL` | not null |
| `chapter_id` | `TEXT NOT NULL` | not null |
| `summary` | `TEXT NOT NULL DEFAULT` | not null, default: '' |
| `active_threads_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `resolved_threads_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `character_states_json` | `TEXT NOT NULL DEFAULT` | not null, default: '{}' |
| `world_facts_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `unresolved_questions_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `contradictions_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `status` | `TEXT NOT NULL DEFAULT` | not null, default: 'complete' |
| `provenance_note` | `TEXT` | - |
| `confidence_score` | `REAL NOT NULL DEFAULT` | not null, default: 0.0 |
| `created_at` | `TEXT NOT NULL` | not null |
| `updated_at` | `TEXT NOT NULL` | not null |

**Foreign Keys:**

- FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE

#### `continuity_findings`

| Column | Type | Notes |
|--------|------|-------|
| `finding_id` | `INTEGER PRIMARY KEY AUTOINCREMENT` | PK, autoincrement |
| `project_id` | `TEXT NOT NULL` | not null |
| `finding_key` | `TEXT` | - |
| `overall_confidence` | `REAL NOT NULL DEFAULT` | not null, default: 0.0 |
| `status` | `TEXT NOT NULL DEFAULT` | not null, default: 'complete' |
| `contradictions_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `unresolved_questions_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `provenance_note` | `TEXT` | - |
| `created_at` | `TEXT NOT NULL` | not null |
| `updated_at` | `TEXT NOT NULL` | not null |

**Foreign Keys:**

- FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE

#### `draft_briefs`

| Column | Type | Notes |
|--------|------|-------|
| `brief_id` | `TEXT PRIMARY KEY` | PK |
| `project_id` | `TEXT NOT NULL` | not null |
| `chapter_id` | `TEXT NOT NULL` | not null |
| `objective` | `TEXT NOT NULL DEFAULT` | not null, default: '' |
| `emotional_turn` | `TEXT NOT NULL DEFAULT` | not null, default: '' |
| `continuity_obligations_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `required_callbacks_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `forbidden_contradictions_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `voice_guidance` | `TEXT NOT NULL DEFAULT` | not null, default: '' |
| `status` | `TEXT NOT NULL DEFAULT` | not null, default: 'draft' |
| `provenance_note` | `TEXT` | - |
| `confidence_score` | `REAL NOT NULL DEFAULT` | not null, default: 0.0 |
| `created_at` | `TEXT NOT NULL` | not null |
| `updated_at` | `TEXT NOT NULL` | not null |

**Foreign Keys:**

- FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE

#### `drafting_context_packets`

| Column | Type | Notes |
|--------|------|-------|
| `packet_id` | `TEXT PRIMARY KEY` | PK |
| `project_id` | `TEXT NOT NULL` | not null |
| `brief_id` | `TEXT NOT NULL` | not null |
| `character_anchors_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `world_constraints_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `prior_summaries_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `pattern_guidance_json` | `TEXT NOT NULL DEFAULT` | not null, default: '{}' |
| `status` | `TEXT NOT NULL DEFAULT` | not null, default: 'draft' |
| `provenance_note` | `TEXT` | - |
| `confidence_score` | `REAL NOT NULL DEFAULT` | not null, default: 0.0 |
| `created_at` | `TEXT NOT NULL` | not null |
| `updated_at` | `TEXT NOT NULL` | not null |

**Foreign Keys:**

- FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE
- FOREIGN KEY(brief_id) REFERENCES draft_briefs(brief_id) ON DELETE CASCADE

#### `canon_generation_runs`

| Column | Type | Notes |
|--------|------|-------|
| `generation_id` | `TEXT PRIMARY KEY` | PK |
| `source_project_id` | `TEXT NOT NULL` | not null |
| `target_project_id` | `TEXT NOT NULL` | not null |
| `mode` | `TEXT NOT NULL` | not null |
| `request_json` | `TEXT NOT NULL` | not null |
| `canon_scope_json` | `TEXT NOT NULL` | not null |
| `canon_policy_json` | `TEXT NOT NULL` | not null |
| `status` | `TEXT NOT NULL` | not null |
| `gate_status` | `TEXT NOT NULL DEFAULT` | not null, default: 'pending' |
| `warnings_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `created_job_ids_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `created_artifacts_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `idempotency_key` | `TEXT` | - |
| `request_hash` | `TEXT NOT NULL` | not null |
| `created_at` | `TEXT NOT NULL` | not null |
| `updated_at` | `TEXT NOT NULL` | not null |

#### `canon_generation_packets`

| Column | Type | Notes |
|--------|------|-------|
| `packet_id` | `TEXT PRIMARY KEY` | PK |
| `generation_id` | `TEXT NOT NULL` | not null |
| `source_project_id` | `TEXT NOT NULL` | not null |
| `target_project_id` | `TEXT NOT NULL` | not null |
| `packet_json` | `TEXT NOT NULL` | not null |
| `source_hashes_json` | `TEXT NOT NULL` | not null |
| `prompt_budget_json` | `TEXT NOT NULL` | not null |
| `created_at` | `TEXT NOT NULL` | not null |
| `updated_at` | `TEXT NOT NULL` | not null |

**Foreign Keys:**

- FOREIGN KEY(generation_id) REFERENCES canon_generation_runs(generation_id) ON DELETE CASCADE

#### `generation_gate_results`

| Column | Type | Notes |
|--------|------|-------|
| `gate_result_id` | `TEXT PRIMARY KEY` | PK |
| `generation_id` | `TEXT NOT NULL` | not null |
| `project_id` | `TEXT NOT NULL` | not null |
| `artifact_kind` | `TEXT NOT NULL` | not null |
| `artifact_id` | `TEXT NOT NULL` | not null |
| `gate_name` | `TEXT NOT NULL` | not null |
| `passed` | `INTEGER NOT NULL` | not null |
| `severity` | `TEXT NOT NULL` | not null |
| `reasons_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `repair_attempted` | `INTEGER NOT NULL DEFAULT` | not null, default: 0 |
| `repair_job_id` | `TEXT` | - |
| `created_at` | `TEXT NOT NULL` | not null |

**Foreign Keys:**

- FOREIGN KEY(generation_id) REFERENCES canon_generation_runs(generation_id) ON DELETE CASCADE

#### `manuscript_assist_runs`

| Column | Type | Notes |
|--------|------|-------|
| `assist_id` | `TEXT PRIMARY KEY` | PK |
| `project_id` | `TEXT NOT NULL` | not null |
| `document_id` | `TEXT NOT NULL` | not null |
| `assist_kind` | `TEXT NOT NULL` | not null |
| `request_json` | `TEXT NOT NULL` | not null |
| `status` | `TEXT NOT NULL` | not null |
| `summary` | `TEXT NOT NULL DEFAULT` | not null, default: '' |
| `created_draft_artifact_id` | `TEXT` | - |
| `created_branch_id` | `TEXT` | - |
| `created_manuscript_document_id` | `TEXT` | - |
| `job_ids_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `warnings_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `idempotency_key` | `TEXT` | - |
| `request_hash` | `TEXT NOT NULL` | not null |
| `created_at` | `TEXT NOT NULL` | not null |
| `updated_at` | `TEXT NOT NULL` | not null |

**Foreign Keys:**

- FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE
- FOREIGN KEY(document_id) REFERENCES manuscript_documents(document_id) ON DELETE CASCADE

#### `manuscript_assist_suggestions`

| Column | Type | Notes |
|--------|------|-------|
| `suggestion_id` | `TEXT PRIMARY KEY` | PK |
| `assist_id` | `TEXT NOT NULL` | not null |
| `project_id` | `TEXT NOT NULL` | not null |
| `target_document_id` | `TEXT NOT NULL` | not null |
| `suggestion_kind` | `TEXT NOT NULL` | not null |
| `source_text` | `TEXT NOT NULL` | not null |
| `proposed_text` | `TEXT NOT NULL` | not null |
| `rationale` | `TEXT NOT NULL` | not null |
| `range_json` | `TEXT` | - |
| `canon_risk` | `TEXT NOT NULL DEFAULT` | not null, default: 'none' |
| `confidence_score` | `REAL NOT NULL DEFAULT` | not null, default: 0.0 |
| `source_context_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `status` | `TEXT NOT NULL DEFAULT` | not null, default: 'REQUESTED' |
| `created_at` | `TEXT NOT NULL` | not null |
| `updated_at` | `TEXT NOT NULL` | not null |

**Foreign Keys:**

- FOREIGN KEY(assist_id) REFERENCES manuscript_assist_runs(assist_id) ON DELETE CASCADE
- FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE
- FOREIGN KEY(target_document_id) REFERENCES manuscript_documents(document_id) ON DELETE CASCADE

#### `manuscript_assist_gate_results`

| Column | Type | Notes |
|--------|------|-------|
| `gate_result_id` | `TEXT PRIMARY KEY` | PK |
| `assist_id` | `TEXT NOT NULL` | not null |
| `project_id` | `TEXT NOT NULL` | not null |
| `document_id` | `TEXT NOT NULL` | not null |
| `gate_name` | `TEXT NOT NULL` | not null |
| `passed` | `INTEGER NOT NULL` | not null |
| `severity` | `TEXT NOT NULL` | not null |
| `reasons_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `created_at` | `TEXT NOT NULL` | not null |

**Foreign Keys:**

- FOREIGN KEY(assist_id) REFERENCES manuscript_assist_runs(assist_id) ON DELETE CASCADE
- FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE
- FOREIGN KEY(document_id) REFERENCES manuscript_documents(document_id) ON DELETE CASCADE

#### `canon_annotations`

| Column | Type | Notes |
|--------|------|-------|
| `annotation_id` | `TEXT PRIMARY KEY` | PK |
| `project_id` | `TEXT NOT NULL` | not null |
| `target_kind` | `TEXT NOT NULL` | not null |
| `target_id` | `TEXT NOT NULL` | not null |
| `field_path` | `TEXT NOT NULL` | not null |
| `annotation_kind` | `TEXT NOT NULL` | not null |
| `note` | `TEXT NOT NULL DEFAULT` | not null, default: '' |
| `applies_to_modes_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `created_at` | `TEXT NOT NULL` | not null |
| `updated_at` | `TEXT NOT NULL` | not null |

**Foreign Keys:**

- FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE

#### `canon_customization_profiles`

| Column | Type | Notes |
|--------|------|-------|
| `profile_id` | `TEXT PRIMARY KEY` | PK |
| `project_id` | `TEXT NOT NULL` | not null |
| `name` | `TEXT NOT NULL` | not null |
| `description` | `TEXT NOT NULL DEFAULT` | not null, default: '' |
| `default_generation_mode` | `TEXT NOT NULL` | not null |
| `canon_scope_json` | `TEXT NOT NULL` | not null |
| `canon_policy_json` | `TEXT NOT NULL` | not null |
| `generation_brief_template` | `TEXT NOT NULL DEFAULT` | not null, default: '' |
| `selected_annotation_ids_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `status` | `TEXT NOT NULL DEFAULT` | not null, default: 'draft' |
| `created_at` | `TEXT NOT NULL` | not null |
| `updated_at` | `TEXT NOT NULL` | not null |

**Foreign Keys:**

- FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE

#### `mythos_entries`

| Column | Type | Notes |
|--------|------|-------|
| `mythos_id` | `TEXT PRIMARY KEY` | PK |
| `project_id` | `TEXT NOT NULL` | not null |
| `entry_type` | `TEXT NOT NULL` | not null |
| `name` | `TEXT NOT NULL` | not null |
| `summary` | `TEXT NOT NULL DEFAULT` | not null, default: '' |
| `canonical_facts_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `pattern_notes_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `source_corpus` | `TEXT` | - |
| `generation_guidance` | `TEXT NOT NULL DEFAULT` | not null, default: '' |
| `visibility_scope` | `TEXT NOT NULL DEFAULT` | not null, default: 'project' |
| `writer_notes` | `TEXT` | - |
| `created_at` | `TEXT NOT NULL` | not null |
| `updated_at` | `TEXT NOT NULL` | not null |

**Foreign Keys:**

- FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE

#### `pattern_entries`

| Column | Type | Notes |
|--------|------|-------|
| `pattern_id` | `TEXT PRIMARY KEY` | PK |
| `project_id` | `TEXT NOT NULL` | not null |
| `pattern_type` | `TEXT NOT NULL` | not null |
| `name` | `TEXT NOT NULL` | not null |
| `summary` | `TEXT NOT NULL DEFAULT` | not null, default: '' |
| `source_type` | `TEXT NOT NULL DEFAULT` | not null, default: 'manual' |
| `generation_modes_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `beats_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `constraints_json` | `TEXT NOT NULL DEFAULT` | not null, default: '[]' |
| `transposition_notes` | `TEXT NOT NULL DEFAULT` | not null, default: '' |
| `writer_notes` | `TEXT` | - |
| `created_at` | `TEXT NOT NULL` | not null |
| `updated_at` | `TEXT NOT NULL` | not null |

**Foreign Keys:**

- FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE

---

### Project Database (bible.db)

2 tables

#### `project_metadata`

| Column | Type | Notes |
|--------|------|-------|
| `key` | `TEXT PRIMARY KEY` | PK |
| `value` | `TEXT NOT NULL` | not null |

#### `artifacts`

| Column | Type | Notes |
|--------|------|-------|
| `artifact_type` | `TEXT PRIMARY KEY` | PK |
| `path` | `TEXT NOT NULL` | not null |
| `updated_at` | `TEXT NOT NULL` | not null |

