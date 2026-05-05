from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from ..request_identity import checker_request_scope, job_request_scope, request_hash

OPERATIONS_DB_VERSION = 22
PROJECT_DB_VERSION = 1
SQLITE_BUSY_TIMEOUT_MS = 5000


OPERATIONS_SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (
    project_id TEXT PRIMARY KEY,
    project_name TEXT NOT NULL,
    manifest_path TEXT NOT NULL,
    db_path TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS project_artifacts (
    artifact_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    artifact_type TEXT NOT NULL,
    path TEXT NOT NULL,
    content_hash TEXT,
    size_bytes INTEGER,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(project_id, artifact_type),
    FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS jobs (
    job_id TEXT PRIMARY KEY,
    logical_run_id TEXT NOT NULL,
    attempt_number INTEGER NOT NULL DEFAULT 1,
    project_id TEXT,
    phase TEXT NOT NULL,
    status TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    request_json TEXT NOT NULL DEFAULT '{}',
    idempotency_key TEXT,
    request_hash TEXT NOT NULL DEFAULT '',
    request_scope TEXT NOT NULL DEFAULT '',
    current_phase TEXT,
    current_step TEXT,
    detail TEXT,
    progress_current INTEGER,
    progress_total INTEGER,
    heartbeat_at TEXT,
    lease_owner TEXT,
    lease_expires_at TEXT,
    claimed_at TEXT,
    error TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS job_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    level TEXT NOT NULL,
    message TEXT NOT NULL,
    FOREIGN KEY(job_id) REFERENCES jobs(job_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS job_attempts (
    attempt_id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT NOT NULL,
    logical_run_id TEXT NOT NULL,
    attempt_number INTEGER NOT NULL,
    status TEXT NOT NULL,
    executor_name TEXT,
    executor_instance_id TEXT,
    queue_delay_ms INTEGER,
    lease_owner TEXT,
    lease_expires_at TEXT,
    claimed_at TEXT,
    started_at TEXT,
    finished_at TEXT,
    last_heartbeat_at TEXT,
    finish_reason TEXT,
    failure_stage TEXT,
    retryable INTEGER,
    retry_reason TEXT,
    error_code TEXT,
    error_category TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(logical_run_id, attempt_number),
    FOREIGN KEY(job_id) REFERENCES jobs(job_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS job_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT NOT NULL,
    logical_run_id TEXT NOT NULL,
    attempt_number INTEGER NOT NULL DEFAULT 1,
    event_type TEXT NOT NULL,
    from_state TEXT,
    to_state TEXT,
    occurred_at TEXT NOT NULL,
    payload_json TEXT NOT NULL DEFAULT '{}',
    FOREIGN KEY(job_id) REFERENCES jobs(job_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS checker_runs (
    run_id TEXT PRIMARY KEY,
    logical_run_id TEXT NOT NULL,
    attempt_number INTEGER NOT NULL DEFAULT 1,
    project_id TEXT,
    status TEXT NOT NULL,
    request_json TEXT NOT NULL DEFAULT '{}',
    idempotency_key TEXT,
    request_hash TEXT NOT NULL DEFAULT '',
    request_scope TEXT NOT NULL DEFAULT '',
    current_role TEXT,
    detail TEXT,
    heartbeat_at TEXT,
    lease_owner TEXT,
    lease_expires_at TEXT,
    claimed_at TEXT,
    report_path TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS checker_results (
    result_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    role TEXT NOT NULL,
    passed INTEGER NOT NULL,
    duration_seconds REAL NOT NULL,
    findings_json TEXT NOT NULL,
    warnings_json TEXT NOT NULL,
    preview TEXT,
    metadata_json TEXT NOT NULL,
    FOREIGN KEY(run_id) REFERENCES checker_runs(run_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS checker_run_attempts (
    attempt_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    logical_run_id TEXT NOT NULL,
    attempt_number INTEGER NOT NULL,
    status TEXT NOT NULL,
    executor_name TEXT,
    executor_instance_id TEXT,
    queue_delay_ms INTEGER,
    lease_owner TEXT,
    lease_expires_at TEXT,
    claimed_at TEXT,
    started_at TEXT,
    finished_at TEXT,
    last_heartbeat_at TEXT,
    finish_reason TEXT,
    failure_stage TEXT,
    retryable INTEGER,
    retry_reason TEXT,
    error_code TEXT,
    error_category TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(logical_run_id, attempt_number),
    FOREIGN KEY(run_id) REFERENCES checker_runs(run_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS checker_run_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    logical_run_id TEXT NOT NULL,
    attempt_number INTEGER NOT NULL DEFAULT 1,
    event_type TEXT NOT NULL,
    from_state TEXT,
    to_state TEXT,
    occurred_at TEXT NOT NULL,
    payload_json TEXT NOT NULL DEFAULT '{}',
    FOREIGN KEY(run_id) REFERENCES checker_runs(run_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS step_records (
    step_record_id INTEGER PRIMARY KEY AUTOINCREMENT,
    logical_run_id TEXT NOT NULL,
    run_id TEXT NOT NULL,
    run_kind TEXT NOT NULL,
    attempt_number INTEGER NOT NULL,
    step_name TEXT NOT NULL,
    step_index INTEGER NOT NULL,
    state TEXT NOT NULL,
    project_id TEXT,
    model_id TEXT,
    critic_profile TEXT,
    backend_name TEXT,
    backend_version TEXT,
    input_hash TEXT,
    output_hash TEXT,
    prompt_hash TEXT,
    input_artifact_refs_json TEXT NOT NULL DEFAULT '[]',
    output_artifact_refs_json TEXT NOT NULL DEFAULT '[]',
    started_at TEXT,
    finished_at TEXT,
    duration_seconds REAL,
    finish_reason TEXT,
    error_code TEXT,
    error_category TEXT,
    executor_id TEXT,
    lease_owner TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS artifact_lineage (
    artifact_lineage_id INTEGER PRIMARY KEY AUTOINCREMENT,
    logical_run_id TEXT NOT NULL,
    run_id TEXT NOT NULL,
    run_kind TEXT NOT NULL,
    attempt_number INTEGER NOT NULL,
    step_name TEXT NOT NULL,
    project_id TEXT,
    artifact_role TEXT NOT NULL,
    artifact_kind TEXT NOT NULL,
    path TEXT NOT NULL,
    content_hash TEXT,
    status TEXT NOT NULL,
    validation_state TEXT NOT NULL,
    produced_at TEXT NOT NULL,
    registered_at TEXT,
    supersedes_artifact_lineage_id INTEGER,
    source_artifact_refs_json TEXT NOT NULL DEFAULT '[]',
    source_content_hashes_json TEXT NOT NULL DEFAULT '[]',
    output_of_step_record_id INTEGER NOT NULL,
    FOREIGN KEY(supersedes_artifact_lineage_id) REFERENCES artifact_lineage(artifact_lineage_id) ON DELETE SET NULL,
    FOREIGN KEY(output_of_step_record_id) REFERENCES step_records(step_record_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS runtime_artifact_selections (
    selection_id INTEGER PRIMARY KEY AUTOINCREMENT,
    logical_run_id TEXT NOT NULL,
    run_id TEXT NOT NULL,
    run_kind TEXT NOT NULL,
    attempt_number INTEGER NOT NULL,
    step_name TEXT NOT NULL,
    project_id TEXT,
    artifact_role TEXT NOT NULL,
    selected_artifact_lineage_id INTEGER,
    selected_path TEXT,
    selected_content_hash TEXT NOT NULL,
    selected_content TEXT NOT NULL,
    selected_at TEXT NOT NULL,
    UNIQUE(run_id, run_kind, attempt_number, step_name, artifact_role),
    FOREIGN KEY(selected_artifact_lineage_id) REFERENCES artifact_lineage(artifact_lineage_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS story_flow_definitions (
    project_id TEXT PRIMARY KEY,
    flow_name TEXT NOT NULL,
    flow_notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS story_flow_stages (
    stage_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    stage_key TEXT NOT NULL,
    stage_kind TEXT NOT NULL,
    is_custom INTEGER NOT NULL DEFAULT 0,
    display_name TEXT NOT NULL,
    description TEXT,
    position INTEGER NOT NULL,
    depends_on_json TEXT NOT NULL DEFAULT '[]',
    stage_configuration_state TEXT NOT NULL,
    stage_progress_state TEXT NOT NULL,
    writer_notes TEXT,
    custom_prompt_guidance TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(project_id, stage_key),
    FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS brainstorm_items (
    item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    cluster_key TEXT,
    content TEXT NOT NULL,
    item_state TEXT NOT NULL,
    tags_json TEXT NOT NULL DEFAULT '[]',
    source_artifact_refs_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS brain_dump_sessions (
    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    title TEXT,
    raw_text TEXT NOT NULL DEFAULT '',
    state TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS foundation_profiles (
    project_id TEXT PRIMARY KEY,
    current_revision_id INTEGER,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS foundation_revisions (
    revision_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    revision_number INTEGER NOT NULL,
    premise TEXT NOT NULL,
    logline TEXT NOT NULL,
    thematic_spine TEXT,
    emotional_promise TEXT,
    tone_direction TEXT,
    target_audience TEXT,
    narrative_constraints_json TEXT NOT NULL DEFAULT '[]',
    complexity_level TEXT,
    success_definition TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(project_id, revision_number),
    FOREIGN KEY(project_id) REFERENCES foundation_profiles(project_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS character_profiles (
    character_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    display_name TEXT NOT NULL,
    role_in_story TEXT,
    archetype TEXT,
    external_goal TEXT,
    internal_need TEXT,
    misbelief_or_wound TEXT,
    core_fear TEXT,
    primary_strength TEXT,
    fatal_flaw_or_limitation TEXT,
    contradictions_json TEXT NOT NULL DEFAULT '[]',
    backstory_summary TEXT,
    voice_notes TEXT,
    relationship_map_json TEXT NOT NULL DEFAULT '[]',
    secrets_json TEXT NOT NULL DEFAULT '[]',
    values_json TEXT NOT NULL DEFAULT '[]',
    taboos_json TEXT NOT NULL DEFAULT '[]',
    change_axis TEXT,
    arc_stage_notes TEXT,
    continuity_facts_json TEXT NOT NULL DEFAULT '[]',
    writer_notes TEXT,
    aliases_json TEXT NOT NULL DEFAULT '[]',
    physical_description TEXT,
    personality_traits_json TEXT NOT NULL DEFAULT '[]',
    motives TEXT,
    relationships_json TEXT NOT NULL DEFAULT '[]',
    character_arc TEXT,
    symbolic_role TEXT,
    dialogue_patterns TEXT,
    psychological_depth TEXT,
    narrative_purpose TEXT,
    thematic_significance TEXT,
    impact_on_others TEXT,
    first_appearance_chapter TEXT,
    chapter_appearances_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS relationship_edges (
    edge_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    source_character_id TEXT NOT NULL,
    target_character_id TEXT NOT NULL,
    relation_kind TEXT NOT NULL,
    summary TEXT NOT NULL,
    tension TEXT,
    notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
    FOREIGN KEY(source_character_id) REFERENCES character_profiles(character_id) ON DELETE CASCADE,
    FOREIGN KEY(target_character_id) REFERENCES character_profiles(character_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS world_bible_entries (
    entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    entry_type TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT,
    canonical_facts_json TEXT NOT NULL DEFAULT '[]',
    related_character_ids_json TEXT NOT NULL DEFAULT '[]',
    visibility_scope TEXT NOT NULL DEFAULT 'project',
    source_artifacts_json TEXT NOT NULL DEFAULT '[]',
    continuity_warnings_json TEXT NOT NULL DEFAULT '[]',
    writer_notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(project_id, entry_type, title),
    FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS arc_candidates (
    arc_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    name TEXT NOT NULL,
    summary TEXT NOT NULL,
    stage_map_notes_json TEXT NOT NULL DEFAULT '[]',
    fit_notes_json TEXT NOT NULL DEFAULT '[]',
    tags_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS arc_stage_maps (
    arc_stage_map_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    arc_id TEXT NOT NULL,
    stage_kinds_json TEXT NOT NULL DEFAULT '[]',
    notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(project_id, arc_id),
    FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
    FOREIGN KEY(arc_id) REFERENCES arc_candidates(arc_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS arc_selections (
    selection_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    selected_arc_id TEXT,
    selected_arc_json TEXT NOT NULL,
    rejected_candidate_ids_json TEXT NOT NULL DEFAULT '[]',
    comparison_notes_json TEXT NOT NULL DEFAULT '[]',
    stage_map_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
    FOREIGN KEY(selected_arc_id) REFERENCES arc_candidates(arc_id) ON DELETE SET NULL,
    FOREIGN KEY(stage_map_id) REFERENCES arc_stage_maps(arc_stage_map_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS arc_comparisons (
    comparison_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    candidate_ids_json TEXT NOT NULL DEFAULT '[]',
    candidate_set_json TEXT NOT NULL DEFAULT '[]',
    ranked_candidates_json TEXT NOT NULL DEFAULT '[]',
    review_notes_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS arc_selection_comparisons (
    selection_id TEXT NOT NULL,
    comparison_id TEXT NOT NULL,
    link_order INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY(selection_id, comparison_id),
    UNIQUE(selection_id, link_order),
    FOREIGN KEY(selection_id) REFERENCES arc_selections(selection_id) ON DELETE CASCADE,
    FOREIGN KEY(comparison_id) REFERENCES arc_comparisons(comparison_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS story_decision_nodes (
    node_record_id INTEGER PRIMARY KEY AUTOINCREMENT,
    node_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    node_type TEXT NOT NULL,
    change_type TEXT NOT NULL,
    subject_type TEXT NOT NULL,
    subject_id TEXT NOT NULL,
    parent_node_id TEXT,
    branch_id TEXT,
    summary TEXT NOT NULL,
    prior_state_ref TEXT,
    prior_state_summary TEXT,
    new_state_ref TEXT,
    new_state_summary TEXT,
    reason_or_note TEXT,
    decision_made_at TEXT NOT NULL,
    made_by TEXT NOT NULL,
    related_object_links_json TEXT NOT NULL DEFAULT '[]',
    informing_object_links_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(project_id, node_id),
    FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS branch_points (
    branch_point_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    source_node_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(project_id, source_node_id),
    UNIQUE(project_id, branch_point_id),
    FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
    FOREIGN KEY(project_id, source_node_id) REFERENCES story_decision_nodes(project_id, node_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS story_branches (
    branch_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    branch_point_id TEXT NOT NULL,
    branch_name TEXT NOT NULL,
    branch_state TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
    UNIQUE(project_id, branch_id),
    FOREIGN KEY(project_id, branch_point_id) REFERENCES branch_points(project_id, branch_point_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS branch_state_refs (
    branch_state_ref_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    branch_id TEXT NOT NULL,
    state_object_type TEXT NOT NULL,
    state_object_id TEXT NOT NULL,
    decision_node_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(project_id, branch_id, state_object_type, state_object_id),
    FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
    FOREIGN KEY(project_id, branch_id) REFERENCES story_branches(project_id, branch_id) ON DELETE CASCADE,
    FOREIGN KEY(project_id, decision_node_id) REFERENCES story_decision_nodes(project_id, node_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS branch_comparisons (
    comparison_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    source_branch_id TEXT NOT NULL,
    target_branch_id TEXT NOT NULL,
    review_notes_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
    FOREIGN KEY(source_branch_id) REFERENCES story_branches(branch_id) ON DELETE CASCADE,
    FOREIGN KEY(target_branch_id) REFERENCES story_branches(branch_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS branch_merge_decisions (
    merge_decision_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    source_branch_id TEXT NOT NULL,
    target_branch_id TEXT NOT NULL,
    merge_rationale TEXT NOT NULL,
    resulting_decision_node_ids_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
    FOREIGN KEY(project_id, source_branch_id) REFERENCES story_branches(project_id, branch_id) ON DELETE CASCADE,
    FOREIGN KEY(project_id, target_branch_id) REFERENCES story_branches(project_id, branch_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS checker_findings (
    finding_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    source_object_id TEXT NOT NULL,
    source_object_kind TEXT NOT NULL,
    severity TEXT NOT NULL,
    summary TEXT NOT NULL,
    details TEXT,
    source_context_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS review_decisions (
    decision_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    target_kind TEXT NOT NULL,
    decision TEXT NOT NULL,
    notes TEXT,
    source_context_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS inspect_run_links (
    link_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    object_kind TEXT NOT NULL,
    object_id TEXT NOT NULL,
    logical_run_id TEXT NOT NULL,
    run_id TEXT NOT NULL,
    run_kind TEXT NOT NULL,
    attempt_number INTEGER,
    label TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS draft_artifacts (
    artifact_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    source_plan_ids_json TEXT NOT NULL DEFAULT '[]',
    source_context_json TEXT NOT NULL DEFAULT '[]',
    provenance_note TEXT,
    status TEXT NOT NULL DEFAULT 'DRAFT',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS manuscript_documents (
    document_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    chapter_id TEXT,
    scene_id TEXT,
    current_draft_artifact_id TEXT,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
    FOREIGN KEY(chapter_id) REFERENCES chapter_plans(chapter_id) ON DELETE SET NULL,
    FOREIGN KEY(scene_id) REFERENCES scene_plans(scene_id) ON DELETE SET NULL,
    FOREIGN KEY(current_draft_artifact_id) REFERENCES draft_artifacts(artifact_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS revision_suggestions (
    suggestion_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    target_document_id TEXT NOT NULL,
    source_text TEXT NOT NULL,
    proposed_text TEXT NOT NULL,
    rationale TEXT NOT NULL,
    source_context_json TEXT NOT NULL DEFAULT '[]',
    status TEXT NOT NULL DEFAULT 'REQUESTED',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
    FOREIGN KEY(target_document_id) REFERENCES manuscript_documents(document_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS beat_plans (
    beat_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    objective TEXT NOT NULL,
    conflict TEXT NOT NULL,
    stakes TEXT NOT NULL,
    dependency_ids_json TEXT NOT NULL DEFAULT '[]',
    arc_stage TEXT NOT NULL,
    active_character_ids_json TEXT NOT NULL DEFAULT '[]',
    continuity_requirements_json TEXT NOT NULL DEFAULT '[]',
    unresolved_questions_json TEXT NOT NULL DEFAULT '[]',
    status TEXT NOT NULL DEFAULT 'draft',
    position INTEGER NOT NULL DEFAULT 0,
    provenance_note TEXT,
    confidence_score REAL NOT NULL DEFAULT 0.0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS sequence_plans (
    sequence_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    beat_ids_json TEXT NOT NULL DEFAULT '[]',
    chapter_ids_json TEXT NOT NULL DEFAULT '[]',
    status TEXT NOT NULL DEFAULT 'draft',
    position INTEGER NOT NULL DEFAULT 0,
    provenance_note TEXT,
    confidence_score REAL NOT NULL DEFAULT 0.0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS storyboard_cards (
    card_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    card_type TEXT NOT NULL DEFAULT 'idea',
    column_id TEXT,
    position INTEGER NOT NULL DEFAULT 0,
    tags TEXT NOT NULL DEFAULT '[]',
    character_ids TEXT NOT NULL DEFAULT '[]',
    dependencies TEXT NOT NULL DEFAULT '[]',
    metadata TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS chapter_plans (
    chapter_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    sequence_id TEXT,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    objective TEXT NOT NULL,
    conflict TEXT NOT NULL,
    stakes TEXT NOT NULL,
    active_character_ids_json TEXT NOT NULL DEFAULT '[]',
    continuity_requirements_json TEXT NOT NULL DEFAULT '[]',
    unresolved_questions_json TEXT NOT NULL DEFAULT '[]',
    status TEXT NOT NULL DEFAULT 'draft',
    position INTEGER NOT NULL DEFAULT 0,
    provenance_note TEXT,
    confidence_score REAL NOT NULL DEFAULT 0.0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    target_word_count INTEGER,
    FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
    FOREIGN KEY(sequence_id) REFERENCES sequence_plans(sequence_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS scene_plans (
    scene_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    chapter_id TEXT,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    objective TEXT NOT NULL,
    conflict TEXT NOT NULL,
    stakes TEXT NOT NULL,
    active_character_ids_json TEXT NOT NULL DEFAULT '[]',
    continuity_requirements_json TEXT NOT NULL DEFAULT '[]',
    unresolved_questions_json TEXT NOT NULL DEFAULT '[]',
    status TEXT NOT NULL DEFAULT 'draft',
    position INTEGER NOT NULL DEFAULT 0,
    provenance_note TEXT,
    confidence_score REAL NOT NULL DEFAULT 0.0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
    FOREIGN KEY(chapter_id) REFERENCES chapter_plans(chapter_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS chapter_packets (
    packet_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    chapter_id TEXT NOT NULL,
    included_reference_ids_json TEXT NOT NULL DEFAULT '[]',
    constraints_json TEXT NOT NULL DEFAULT '[]',
    scene_goals_json TEXT NOT NULL DEFAULT '[]',
    status TEXT NOT NULL DEFAULT 'draft',
    provenance_note TEXT,
    confidence_score REAL NOT NULL DEFAULT 0.0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
    FOREIGN KEY(chapter_id) REFERENCES chapter_plans(chapter_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS planning_dependencies (
    dependency_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    upstream_id TEXT NOT NULL,
    downstream_id TEXT NOT NULL,
    dependency_kind TEXT NOT NULL,
    reason TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS continuity_threads (
    thread_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'active',
    chapter_ids_json TEXT NOT NULL DEFAULT '[]',
    character_ids_json TEXT NOT NULL DEFAULT '[]',
    evidence_json TEXT NOT NULL DEFAULT '[]',
    provenance_note TEXT,
    confidence_score REAL NOT NULL DEFAULT 0.0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS continuity_states (
    state_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    chapter_id TEXT NOT NULL,
    summary TEXT NOT NULL DEFAULT '',
    active_threads_json TEXT NOT NULL DEFAULT '[]',
    resolved_threads_json TEXT NOT NULL DEFAULT '[]',
    character_states_json TEXT NOT NULL DEFAULT '{}',
    world_facts_json TEXT NOT NULL DEFAULT '[]',
    unresolved_questions_json TEXT NOT NULL DEFAULT '[]',
    contradictions_json TEXT NOT NULL DEFAULT '[]',
    status TEXT NOT NULL DEFAULT 'complete',
    provenance_note TEXT,
    confidence_score REAL NOT NULL DEFAULT 0.0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS continuity_findings (
    finding_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    finding_key TEXT,
    overall_confidence REAL NOT NULL DEFAULT 0.0,
    status TEXT NOT NULL DEFAULT 'complete',
    contradictions_json TEXT NOT NULL DEFAULT '[]',
    unresolved_questions_json TEXT NOT NULL DEFAULT '[]',
    provenance_note TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS draft_briefs (
    brief_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    chapter_id TEXT NOT NULL,
    objective TEXT NOT NULL DEFAULT '',
    emotional_turn TEXT NOT NULL DEFAULT '',
    continuity_obligations_json TEXT NOT NULL DEFAULT '[]',
    required_callbacks_json TEXT NOT NULL DEFAULT '[]',
    forbidden_contradictions_json TEXT NOT NULL DEFAULT '[]',
    voice_guidance TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'draft',
    provenance_note TEXT,
    confidence_score REAL NOT NULL DEFAULT 0.0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS drafting_context_packets (
    packet_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    brief_id TEXT NOT NULL,
    character_anchors_json TEXT NOT NULL DEFAULT '[]',
    world_constraints_json TEXT NOT NULL DEFAULT '[]',
    prior_summaries_json TEXT NOT NULL DEFAULT '[]',
    pattern_guidance_json TEXT NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'draft',
    provenance_note TEXT,
    confidence_score REAL NOT NULL DEFAULT 0.0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
    FOREIGN KEY(brief_id) REFERENCES draft_briefs(brief_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS canon_generation_runs (
    generation_id TEXT PRIMARY KEY,
    source_project_id TEXT NOT NULL,
    target_project_id TEXT NOT NULL,
    mode TEXT NOT NULL,
    request_json TEXT NOT NULL,
    canon_scope_json TEXT NOT NULL,
    canon_policy_json TEXT NOT NULL,
    status TEXT NOT NULL,
    gate_status TEXT NOT NULL DEFAULT 'pending',
    warnings_json TEXT NOT NULL DEFAULT '[]',
    created_job_ids_json TEXT NOT NULL DEFAULT '[]',
    created_artifacts_json TEXT NOT NULL DEFAULT '[]',
    idempotency_key TEXT,
    request_hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS canon_generation_packets (
    packet_id TEXT PRIMARY KEY,
    generation_id TEXT NOT NULL,
    source_project_id TEXT NOT NULL,
    target_project_id TEXT NOT NULL,
    packet_json TEXT NOT NULL,
    source_hashes_json TEXT NOT NULL,
    prompt_budget_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(generation_id) REFERENCES canon_generation_runs(generation_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS generation_gate_results (
    gate_result_id TEXT PRIMARY KEY,
    generation_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    artifact_kind TEXT NOT NULL,
    artifact_id TEXT NOT NULL,
    gate_name TEXT NOT NULL,
    passed INTEGER NOT NULL,
    severity TEXT NOT NULL,
    reasons_json TEXT NOT NULL DEFAULT '[]',
    repair_attempted INTEGER NOT NULL DEFAULT 0,
    repair_job_id TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(generation_id) REFERENCES canon_generation_runs(generation_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS manuscript_assist_runs (
    assist_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    document_id TEXT NOT NULL,
    assist_kind TEXT NOT NULL,
    request_json TEXT NOT NULL,
    status TEXT NOT NULL,
    summary TEXT NOT NULL DEFAULT '',
    created_draft_artifact_id TEXT,
    created_branch_id TEXT,
    created_manuscript_document_id TEXT,
    job_ids_json TEXT NOT NULL DEFAULT '[]',
    warnings_json TEXT NOT NULL DEFAULT '[]',
    idempotency_key TEXT,
    request_hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
    FOREIGN KEY(document_id) REFERENCES manuscript_documents(document_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS manuscript_assist_suggestions (
    suggestion_id TEXT PRIMARY KEY,
    assist_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    target_document_id TEXT NOT NULL,
    suggestion_kind TEXT NOT NULL,
    source_text TEXT NOT NULL,
    proposed_text TEXT NOT NULL,
    rationale TEXT NOT NULL,
    range_json TEXT,
    canon_risk TEXT NOT NULL DEFAULT 'none',
    confidence_score REAL NOT NULL DEFAULT 0.0,
    source_context_json TEXT NOT NULL DEFAULT '[]',
    status TEXT NOT NULL DEFAULT 'REQUESTED',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(assist_id) REFERENCES manuscript_assist_runs(assist_id) ON DELETE CASCADE,
    FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
    FOREIGN KEY(target_document_id) REFERENCES manuscript_documents(document_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS manuscript_assist_gate_results (
    gate_result_id TEXT PRIMARY KEY,
    assist_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    document_id TEXT NOT NULL,
    gate_name TEXT NOT NULL,
    passed INTEGER NOT NULL,
    severity TEXT NOT NULL,
    reasons_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    FOREIGN KEY(assist_id) REFERENCES manuscript_assist_runs(assist_id) ON DELETE CASCADE,
    FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
    FOREIGN KEY(document_id) REFERENCES manuscript_documents(document_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS canon_annotations (
    annotation_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    target_kind TEXT NOT NULL,
    target_id TEXT NOT NULL,
    field_path TEXT NOT NULL,
    annotation_kind TEXT NOT NULL,
    note TEXT NOT NULL DEFAULT '',
    applies_to_modes_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS canon_customization_profiles (
    profile_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    default_generation_mode TEXT NOT NULL,
    canon_scope_json TEXT NOT NULL,
    canon_policy_json TEXT NOT NULL,
    generation_brief_template TEXT NOT NULL DEFAULT '',
    selected_annotation_ids_json TEXT NOT NULL DEFAULT '[]',
    status TEXT NOT NULL DEFAULT 'draft',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS mythos_entries (
    mythos_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    entry_type TEXT NOT NULL,
    name TEXT NOT NULL,
    summary TEXT NOT NULL DEFAULT '',
    canonical_facts_json TEXT NOT NULL DEFAULT '[]',
    pattern_notes_json TEXT NOT NULL DEFAULT '[]',
    source_corpus TEXT,
    generation_guidance TEXT NOT NULL DEFAULT '',
    visibility_scope TEXT NOT NULL DEFAULT 'project',
    writer_notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS pattern_entries (
    pattern_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    pattern_type TEXT NOT NULL,
    name TEXT NOT NULL,
    summary TEXT NOT NULL DEFAULT '',
    source_type TEXT NOT NULL DEFAULT 'manual',
    generation_modes_json TEXT NOT NULL DEFAULT '[]',
    beats_json TEXT NOT NULL DEFAULT '[]',
    constraints_json TEXT NOT NULL DEFAULT '[]',
    transposition_notes TEXT NOT NULL DEFAULT '',
    writer_notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);
"""


OPERATIONS_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_projects_updated_at ON projects(updated_at);
CREATE INDEX IF NOT EXISTS idx_project_artifacts_project_type ON project_artifacts(project_id, artifact_type);
CREATE INDEX IF NOT EXISTS idx_jobs_project_status ON jobs(project_id, status);
CREATE INDEX IF NOT EXISTS idx_jobs_logical_attempt ON jobs(logical_run_id, attempt_number);
CREATE INDEX IF NOT EXISTS idx_jobs_status_updated_at ON jobs(status, updated_at);
CREATE INDEX IF NOT EXISTS idx_jobs_status_lease ON jobs(status, lease_expires_at, created_at);
CREATE INDEX IF NOT EXISTS idx_jobs_request_scope_hash ON jobs(request_scope, request_hash);
CREATE UNIQUE INDEX IF NOT EXISTS idx_jobs_scope_idempotency_key ON jobs(request_scope, idempotency_key) WHERE idempotency_key IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_job_logs_job_id_log_id ON job_logs(job_id, log_id);
CREATE INDEX IF NOT EXISTS idx_job_attempts_job_id_attempt ON job_attempts(job_id, attempt_number);
CREATE INDEX IF NOT EXISTS idx_job_attempts_logical_attempt ON job_attempts(logical_run_id, attempt_number);
CREATE INDEX IF NOT EXISTS idx_job_attempts_status_lease ON job_attempts(status, lease_expires_at, created_at);
CREATE INDEX IF NOT EXISTS idx_job_events_job_id_event_id ON job_events(job_id, event_id);
CREATE INDEX IF NOT EXISTS idx_job_events_logical_attempt ON job_events(logical_run_id, attempt_number, event_id);
CREATE INDEX IF NOT EXISTS idx_checker_runs_project_status ON checker_runs(project_id, status);
CREATE INDEX IF NOT EXISTS idx_checker_runs_logical_attempt ON checker_runs(logical_run_id, attempt_number);
CREATE INDEX IF NOT EXISTS idx_checker_runs_status_updated_at ON checker_runs(status, updated_at);
CREATE INDEX IF NOT EXISTS idx_checker_runs_status_lease ON checker_runs(status, lease_expires_at, created_at);
CREATE INDEX IF NOT EXISTS idx_checker_runs_request_scope_hash ON checker_runs(request_scope, request_hash);
CREATE UNIQUE INDEX IF NOT EXISTS idx_checker_runs_scope_idempotency_key ON checker_runs(request_scope, idempotency_key) WHERE idempotency_key IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_checker_results_run_id_result_id ON checker_results(run_id, result_id);
CREATE INDEX IF NOT EXISTS idx_checker_run_attempts_run_id_attempt ON checker_run_attempts(run_id, attempt_number);
CREATE INDEX IF NOT EXISTS idx_checker_run_attempts_logical_attempt ON checker_run_attempts(logical_run_id, attempt_number);
CREATE INDEX IF NOT EXISTS idx_checker_run_attempts_status_lease ON checker_run_attempts(status, lease_expires_at, created_at);
CREATE INDEX IF NOT EXISTS idx_checker_run_events_run_id_event_id ON checker_run_events(run_id, event_id);
CREATE INDEX IF NOT EXISTS idx_checker_run_events_logical_attempt ON checker_run_events(logical_run_id, attempt_number, event_id);
CREATE INDEX IF NOT EXISTS idx_step_records_run ON step_records(run_kind, run_id, step_index, step_record_id);
CREATE INDEX IF NOT EXISTS idx_step_records_logical_attempt ON step_records(logical_run_id, attempt_number, step_index);
CREATE INDEX IF NOT EXISTS idx_artifact_lineage_run ON artifact_lineage(run_kind, run_id, artifact_lineage_id);
CREATE INDEX IF NOT EXISTS idx_artifact_lineage_step_record ON artifact_lineage(output_of_step_record_id, artifact_lineage_id);
CREATE INDEX IF NOT EXISTS idx_runtime_artifact_selections_run_step ON runtime_artifact_selections(run_kind, run_id, attempt_number, step_name, selection_id);
CREATE INDEX IF NOT EXISTS idx_story_flow_definitions_updated_at ON story_flow_definitions(updated_at);
CREATE INDEX IF NOT EXISTS idx_story_flow_stages_project_position ON story_flow_stages(project_id, position, stage_id);
CREATE INDEX IF NOT EXISTS idx_story_flow_stages_project_key ON story_flow_stages(project_id, stage_key);
CREATE INDEX IF NOT EXISTS idx_brainstorm_items_project_state ON brainstorm_items(project_id, item_state, item_id);
CREATE INDEX IF NOT EXISTS idx_foundation_revisions_project_revision ON foundation_revisions(project_id, revision_number);
CREATE INDEX IF NOT EXISTS idx_character_profiles_project_name ON character_profiles(project_id, display_name);
CREATE INDEX IF NOT EXISTS idx_relationship_edges_project_characters ON relationship_edges(project_id, source_character_id, target_character_id, edge_id);
CREATE INDEX IF NOT EXISTS idx_world_bible_entries_project_type_title ON world_bible_entries(project_id, entry_type, title);
CREATE INDEX IF NOT EXISTS idx_arc_candidates_project_name ON arc_candidates(project_id, name, arc_id);
CREATE INDEX IF NOT EXISTS idx_arc_stage_maps_project_arc ON arc_stage_maps(project_id, arc_id, arc_stage_map_id);
CREATE INDEX IF NOT EXISTS idx_arc_selections_project_created ON arc_selections(project_id, created_at);
CREATE INDEX IF NOT EXISTS idx_arc_comparisons_project_created ON arc_comparisons(project_id, created_at, comparison_id);
CREATE INDEX IF NOT EXISTS idx_arc_selection_comparisons_selection_order ON arc_selection_comparisons(selection_id, link_order, comparison_id);
CREATE INDEX IF NOT EXISTS idx_story_decision_nodes_project_made_at ON story_decision_nodes(project_id, decision_made_at, node_id, node_record_id);
CREATE INDEX IF NOT EXISTS idx_story_decision_nodes_project_subject ON story_decision_nodes(project_id, subject_type, subject_id, decision_made_at, node_id);
CREATE INDEX IF NOT EXISTS idx_branch_points_project_source ON branch_points(project_id, source_node_id, branch_point_id);
CREATE INDEX IF NOT EXISTS idx_story_branches_project_created ON story_branches(project_id, created_at, branch_id);
CREATE INDEX IF NOT EXISTS idx_branch_state_refs_project_branch_created ON branch_state_refs(project_id, branch_id, created_at, branch_state_ref_id);
CREATE INDEX IF NOT EXISTS idx_branch_state_refs_project_object ON branch_state_refs(project_id, state_object_type, state_object_id, branch_state_ref_id);
CREATE INDEX IF NOT EXISTS idx_branch_state_refs_project_decision ON branch_state_refs(project_id, branch_id, decision_node_id, created_at, branch_state_ref_id);
CREATE INDEX IF NOT EXISTS idx_branch_comparisons_project_created ON branch_comparisons(project_id, created_at, comparison_id);
CREATE INDEX IF NOT EXISTS idx_branch_comparisons_project_pair ON branch_comparisons(project_id, source_branch_id, target_branch_id, comparison_id);
CREATE INDEX IF NOT EXISTS idx_branch_merge_decisions_project_created ON branch_merge_decisions(project_id, created_at, merge_decision_id);
CREATE INDEX IF NOT EXISTS idx_branch_merge_decisions_project_pair ON branch_merge_decisions(project_id, source_branch_id, target_branch_id, merge_decision_id);
CREATE INDEX IF NOT EXISTS idx_checker_findings_project_source ON checker_findings(project_id, source_object_kind, source_object_id, finding_id);
CREATE INDEX IF NOT EXISTS idx_checker_findings_project_severity ON checker_findings(project_id, severity, created_at, finding_id);
CREATE INDEX IF NOT EXISTS idx_review_decisions_project_target ON review_decisions(project_id, target_kind, target_id, created_at, decision_id);
CREATE INDEX IF NOT EXISTS idx_inspect_run_links_project_object ON inspect_run_links(project_id, object_kind, object_id, created_at, link_id);
CREATE INDEX IF NOT EXISTS idx_inspect_run_links_project_run ON inspect_run_links(project_id, logical_run_id, run_id, created_at, link_id);
CREATE INDEX IF NOT EXISTS idx_draft_artifacts_project_title ON draft_artifacts(project_id, title, artifact_id);
CREATE INDEX IF NOT EXISTS idx_manuscript_documents_project_title ON manuscript_documents(project_id, title, document_id);
CREATE INDEX IF NOT EXISTS idx_manuscript_documents_project_chapter_scene ON manuscript_documents(project_id, chapter_id, scene_id, document_id);
CREATE INDEX IF NOT EXISTS idx_revision_suggestions_project_target ON revision_suggestions(project_id, target_document_id, suggestion_id);
CREATE INDEX IF NOT EXISTS idx_beat_plans_project_position ON beat_plans(project_id, position, beat_id);
CREATE INDEX IF NOT EXISTS idx_sequence_plans_project_position ON sequence_plans(project_id, position, sequence_id);
CREATE INDEX IF NOT EXISTS idx_chapter_plans_project_sequence_position ON chapter_plans(project_id, sequence_id, position, chapter_id);
CREATE INDEX IF NOT EXISTS idx_scene_plans_project_chapter_position ON scene_plans(project_id, chapter_id, position, scene_id);
CREATE INDEX IF NOT EXISTS idx_chapter_packets_project_chapter ON chapter_packets(project_id, chapter_id, packet_id);
CREATE INDEX IF NOT EXISTS idx_planning_dependencies_project_upstream ON planning_dependencies(project_id, upstream_id, downstream_id, dependency_id);
CREATE INDEX IF NOT EXISTS idx_continuity_threads_project_status ON continuity_threads(project_id, status, thread_id);
CREATE INDEX IF NOT EXISTS idx_continuity_states_project_chapter ON continuity_states(project_id, chapter_id, state_id);
CREATE INDEX IF NOT EXISTS idx_continuity_findings_project_created ON continuity_findings(project_id, created_at, finding_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_continuity_findings_project_key ON continuity_findings(project_id, finding_key) WHERE finding_key IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_draft_briefs_project_chapter ON draft_briefs(project_id, chapter_id, brief_id);
CREATE INDEX IF NOT EXISTS idx_drafting_context_packets_project_brief ON drafting_context_packets(project_id, brief_id, packet_id);
CREATE INDEX IF NOT EXISTS idx_generation_runs_source_created ON canon_generation_runs(source_project_id, created_at);
CREATE INDEX IF NOT EXISTS idx_generation_runs_target_created ON canon_generation_runs(target_project_id, created_at);
CREATE INDEX IF NOT EXISTS idx_generation_runs_status ON canon_generation_runs(status, updated_at);
CREATE UNIQUE INDEX IF NOT EXISTS idx_generation_runs_idempotency ON canon_generation_runs(source_project_id, idempotency_key) WHERE idempotency_key IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_generation_packets_generation ON canon_generation_packets(generation_id, created_at);
CREATE INDEX IF NOT EXISTS idx_generation_gate_results_generation ON generation_gate_results(generation_id, created_at);
CREATE INDEX IF NOT EXISTS idx_generation_gate_results_artifact ON generation_gate_results(project_id, artifact_kind, artifact_id, created_at);
CREATE INDEX IF NOT EXISTS idx_assist_runs_project_document ON manuscript_assist_runs(project_id, document_id, updated_at);
CREATE INDEX IF NOT EXISTS idx_assist_runs_status ON manuscript_assist_runs(status, updated_at);
CREATE UNIQUE INDEX IF NOT EXISTS idx_assist_runs_idempotency ON manuscript_assist_runs(project_id, idempotency_key) WHERE idempotency_key IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_assist_suggestions_document_status ON manuscript_assist_suggestions(project_id, target_document_id, status, updated_at);
CREATE INDEX IF NOT EXISTS idx_assist_suggestions_assist ON manuscript_assist_suggestions(assist_id, suggestion_id);
CREATE INDEX IF NOT EXISTS idx_assist_gate_results_assist ON manuscript_assist_gate_results(assist_id, created_at);
CREATE INDEX IF NOT EXISTS idx_canon_annotations_project_target ON canon_annotations(project_id, target_kind, target_id);
CREATE INDEX IF NOT EXISTS idx_canon_annotations_project_kind ON canon_annotations(project_id, annotation_kind);
CREATE INDEX IF NOT EXISTS idx_canon_profiles_project_status ON canon_customization_profiles(project_id, status, updated_at);
CREATE INDEX IF NOT EXISTS idx_mythos_entries_project_type ON mythos_entries(project_id, entry_type, name);
CREATE INDEX IF NOT EXISTS idx_pattern_entries_project_type ON pattern_entries(project_id, pattern_type, name);
"""


PROJECT_SCHEMA = """
CREATE TABLE IF NOT EXISTS project_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS artifacts (
    artifact_type TEXT PRIMARY KEY,
    path TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""


PROJECT_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_artifacts_updated_at ON artifacts(updated_at);
"""


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(db_path), timeout=SQLITE_BUSY_TIMEOUT_MS / 1000)
    connection.row_factory = sqlite3.Row
    _configure_connection(connection)
    return connection


def ensure_operations_db(db_path: Path) -> Path:
    with connect(db_path) as connection:
        _migrate_operations_db(connection)
        connection.commit()
    return db_path


def ensure_project_db(db_path: Path) -> Path:
    with connect(db_path) as connection:
        _migrate_project_db(connection)
        connection.commit()
    return db_path


def _configure_connection(connection: sqlite3.Connection) -> None:
    connection.execute(f"PRAGMA busy_timeout = {SQLITE_BUSY_TIMEOUT_MS}")
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA wal_checkpoint(PASSIVE)")


def _migrate_operations_db(connection: sqlite3.Connection) -> None:
    version = _get_user_version(connection)
    if version == 0:
        connection.executescript(OPERATIONS_SCHEMA)
        _apply_operations_indexes(connection)
        _set_user_version(connection, OPERATIONS_DB_VERSION)
        return

    if version < OPERATIONS_DB_VERSION:
        _rebuild_operations_schema(connection)
        _set_user_version(connection, OPERATIONS_DB_VERSION)
        return

    _migrate_chapter_plans_add_target_word_count(connection)
    _migrate_character_profiles_add_deep_analysis(connection)
    _migrate_planning_artifacts_add_provenance_fields(connection)
    _migrate_continuity_findings_add_finding_key(connection)
    connection.executescript(OPERATIONS_SCHEMA)
    _apply_operations_indexes(connection)


def _migrate_chapter_plans_add_target_word_count(connection: sqlite3.Connection) -> None:
    if not _column_exists(connection, "chapter_plans", "target_word_count"):
        connection.execute("ALTER TABLE chapter_plans ADD COLUMN target_word_count INTEGER")
        connection.commit()


def _migrate_character_profiles_add_deep_analysis(connection: sqlite3.Connection) -> None:
    """Add deep character analysis columns for multi-pass story import."""
    columns = [
        ("aliases_json", "TEXT NOT NULL DEFAULT '[]'"),
        ("physical_description", "TEXT"),
        ("personality_traits_json", "TEXT NOT NULL DEFAULT '[]'"),
        ("motives", "TEXT"),
        ("relationships_json", "TEXT NOT NULL DEFAULT '[]'"),
        ("character_arc", "TEXT"),
        ("symbolic_role", "TEXT"),
        ("dialogue_patterns", "TEXT"),
        ("psychological_depth", "TEXT"),
        ("narrative_purpose", "TEXT"),
        ("thematic_significance", "TEXT"),
        ("impact_on_others", "TEXT"),
        ("first_appearance_chapter", "TEXT"),
        ("chapter_appearances_json", "TEXT NOT NULL DEFAULT '[]'"),
    ]
    added = False
    for col_name, col_type in columns:
        if not _column_exists(connection, "character_profiles", col_name):
            connection.execute(f"ALTER TABLE character_profiles ADD COLUMN {col_name} {col_type}")
            added = True
    if added:
        connection.commit()


def _migrate_planning_artifacts_add_provenance_fields(connection: sqlite3.Connection) -> None:
    planning_tables = (
        "beat_plans",
        "sequence_plans",
        "chapter_plans",
        "scene_plans",
        "chapter_packets",
    )
    added = False
    for table_name in planning_tables:
        if not _column_exists(connection, table_name, "provenance_note"):
            connection.execute(f"ALTER TABLE {table_name} ADD COLUMN provenance_note TEXT")
            added = True
        if not _column_exists(connection, table_name, "confidence_score"):
            connection.execute(f"ALTER TABLE {table_name} ADD COLUMN confidence_score REAL NOT NULL DEFAULT 0.0")
            added = True
    if added:
        connection.commit()


def _migrate_continuity_findings_add_finding_key(connection: sqlite3.Connection) -> None:
    if _table_exists(connection, "continuity_findings") and not _column_exists(
        connection,
        "continuity_findings",
        "finding_key",
    ):
        connection.execute("ALTER TABLE continuity_findings ADD COLUMN finding_key TEXT")
        connection.commit()


def _migrate_project_db(connection: sqlite3.Connection) -> None:
    version = _get_user_version(connection)
    if version == 0:
        connection.executescript(PROJECT_SCHEMA)
        connection.executescript(PROJECT_INDEXES)
        _set_user_version(connection, PROJECT_DB_VERSION)
        return

    connection.executescript(PROJECT_SCHEMA)
    connection.executescript(PROJECT_INDEXES)
    if version < PROJECT_DB_VERSION:
        _set_user_version(connection, PROJECT_DB_VERSION)


def _rebuild_operations_schema(connection: sqlite3.Connection) -> None:
    connection.execute("PRAGMA foreign_keys = OFF")
    try:
        _reset_partial_rebuild_state(connection)
        _rename_table_if_exists(connection, "projects", "projects__legacy")
        _rename_table_if_exists(connection, "project_artifacts", "project_artifacts__legacy")
        _rename_table_if_exists(connection, "jobs", "jobs__legacy")
        _rename_table_if_exists(connection, "job_logs", "job_logs__legacy")
        _rename_table_if_exists(connection, "job_attempts", "job_attempts__legacy")
        _rename_table_if_exists(connection, "job_events", "job_events__legacy")
        _rename_table_if_exists(connection, "checker_runs", "checker_runs__legacy")
        _rename_table_if_exists(connection, "checker_results", "checker_results__legacy")
        _rename_table_if_exists(connection, "checker_run_attempts", "checker_run_attempts__legacy")
        _rename_table_if_exists(connection, "checker_run_events", "checker_run_events__legacy")
        _rename_table_if_exists(connection, "step_records", "step_records__legacy")
        _rename_table_if_exists(connection, "artifact_lineage", "artifact_lineage__legacy")
        _rename_table_if_exists(connection, "world_bible_entries", "world_bible_entries__legacy")
        _rename_table_if_exists(connection, "arc_candidates", "arc_candidates__legacy")
        _rename_table_if_exists(connection, "arc_selections", "arc_selections__legacy")
        _rename_table_if_exists(connection, "story_decision_nodes", "story_decision_nodes__legacy")
        _rename_table_if_exists(connection, "story_decision_records", "story_decision_records__legacy")
        _rename_table_if_exists(connection, "branch_points", "branch_points__legacy")
        _rename_table_if_exists(connection, "story_branches", "story_branches__legacy")
        _rename_table_if_exists(connection, "branch_state_refs", "branch_state_refs__legacy")
        _rename_table_if_exists(connection, "branch_comparisons", "branch_comparisons__legacy")
        _rename_table_if_exists(connection, "branch_merge_decisions", "branch_merge_decisions__legacy")
        _rename_table_if_exists(connection, "checker_findings", "checker_findings__legacy")
        _rename_table_if_exists(connection, "review_decisions", "review_decisions__legacy")
        _rename_table_if_exists(connection, "inspect_run_links", "inspect_run_links__legacy")
        _rename_table_if_exists(connection, "draft_artifacts", "draft_artifacts__legacy")
        _rename_table_if_exists(connection, "manuscript_documents", "manuscript_documents__legacy")
        _rename_table_if_exists(connection, "revision_suggestions", "revision_suggestions__legacy")
        _rename_table_if_exists(connection, "runtime_artifact_selections", "runtime_artifact_selections__legacy")
        _rename_table_if_exists(connection, "story_flow_definitions", "story_flow_definitions__legacy")
        _rename_table_if_exists(connection, "story_flow_stages", "story_flow_stages__legacy")
        _rename_table_if_exists(connection, "brainstorm_items", "brainstorm_items__legacy")
        _rename_table_if_exists(connection, "brain_dump_sessions", "brain_dump_sessions__legacy")
        _rename_table_if_exists(connection, "foundation_profiles", "foundation_profiles__legacy")
        _rename_table_if_exists(connection, "foundation_revisions", "foundation_revisions__legacy")
        _rename_table_if_exists(connection, "character_profiles", "character_profiles__legacy")
        _rename_table_if_exists(connection, "relationship_edges", "relationship_edges__legacy")
        _rename_table_if_exists(connection, "arc_stage_maps", "arc_stage_maps__legacy")
        _rename_table_if_exists(connection, "arc_comparisons", "arc_comparisons__legacy")
        _rename_table_if_exists(connection, "arc_selection_comparisons", "arc_selection_comparisons__legacy")
        _rename_table_if_exists(connection, "beat_plans", "beat_plans__legacy")
        _rename_table_if_exists(connection, "sequence_plans", "sequence_plans__legacy")
        _rename_table_if_exists(connection, "storyboard_cards", "storyboard_cards__legacy")
        _rename_table_if_exists(connection, "chapter_plans", "chapter_plans__legacy")
        _rename_table_if_exists(connection, "scene_plans", "scene_plans__legacy")
        _rename_table_if_exists(connection, "chapter_packets", "chapter_packets__legacy")
        _rename_table_if_exists(connection, "planning_dependencies", "planning_dependencies__legacy")
        _rename_table_if_exists(connection, "continuity_threads", "continuity_threads__legacy")
        _rename_table_if_exists(connection, "continuity_states", "continuity_states__legacy")
        _rename_table_if_exists(connection, "continuity_findings", "continuity_findings__legacy")
        _rename_table_if_exists(connection, "draft_briefs", "draft_briefs__legacy")
        _rename_table_if_exists(connection, "drafting_context_packets", "drafting_context_packets__legacy")

        connection.executescript(OPERATIONS_SCHEMA)

        _copy_if_exists(
            connection,
            "projects__legacy",
            """
            INSERT INTO projects (
                project_id, project_name, manifest_path, db_path, created_at, updated_at
            )
            SELECT project_id, project_name, manifest_path, db_path, created_at, updated_at
            FROM projects__legacy
            """,
        )
        _copy_if_exists(
            connection,
            "project_artifacts__legacy",
            """
            INSERT INTO project_artifacts (
                artifact_id, project_id, artifact_type, path, content_hash, size_bytes, created_at, updated_at
            )
            SELECT artifact_id, project_id, artifact_type, path, content_hash, size_bytes, created_at, updated_at
            FROM project_artifacts__legacy
            """,
        )
        _copy_jobs_legacy(connection)
        _backfill_job_request_identity(connection)
        _copy_if_exists(
            connection,
            "job_logs__legacy",
            """
            INSERT INTO job_logs (log_id, job_id, timestamp, level, message)
            SELECT log_id, job_id, timestamp, level, message
            FROM job_logs__legacy
            """,
        )
        _copy_job_attempts_legacy(connection)
        if not _table_exists(connection, "job_attempts__legacy"):
            _backfill_job_attempts(connection)
        _copy_job_events_legacy(connection)
        _copy_checker_runs_legacy(connection)
        _backfill_checker_run_request_identity(connection)
        _copy_if_exists(
            connection,
            "checker_results__legacy",
            """
            INSERT INTO checker_results (
                result_id, run_id, role, passed, duration_seconds, findings_json, warnings_json, preview, metadata_json
            )
            SELECT result_id, run_id, role, passed, duration_seconds, findings_json, warnings_json, preview, metadata_json
            FROM checker_results__legacy
            """,
        )
        _copy_checker_run_attempts_legacy(connection)
        if not _table_exists(connection, "checker_run_attempts__legacy"):
            _backfill_checker_run_attempts(connection)
        _copy_checker_run_events_legacy(connection)
        _copy_step_records_legacy(connection)
        _copy_artifact_lineage_legacy(connection)
        _copy_world_bible_entries_legacy(connection)
        _copy_arc_candidates_legacy(connection)
        _copy_arc_selections_legacy(connection)
        _copy_story_decision_nodes_legacy(connection)
        _copy_branch_points_legacy(connection)
        _copy_story_branches_legacy(connection)
        _copy_branch_state_refs_legacy(connection)
        _copy_branch_comparisons_legacy(connection)
        _copy_branch_merge_decisions_legacy(connection)
        _copy_checker_findings_legacy(connection)
        _copy_review_decisions_legacy(connection)
        _copy_inspect_run_links_legacy(connection)
        _copy_draft_artifacts_legacy(connection)
        _copy_manuscript_documents_legacy(connection)
        _copy_revision_suggestions_legacy(connection)
        _copy_runtime_artifact_selections_legacy(connection)
        _copy_story_flow_definitions_legacy(connection)
        _copy_story_flow_stages_legacy(connection)
        _copy_brainstorm_items_legacy(connection)
        _copy_brain_dump_sessions_legacy(connection)
        _copy_foundation_profiles_legacy(connection)
        _copy_foundation_revisions_legacy(connection)
        _copy_character_profiles_legacy(connection)
        _copy_relationship_edges_legacy(connection)
        _copy_arc_stage_maps_legacy(connection)
        _copy_arc_comparisons_legacy(connection)
        _copy_arc_selection_comparisons_legacy(connection)
        _copy_beat_plans_legacy(connection)
        _copy_sequence_plans_legacy(connection)
        _copy_storyboard_cards_legacy(connection)
        _copy_chapter_plans_legacy(connection)
        _copy_scene_plans_legacy(connection)
        _copy_chapter_packets_legacy(connection)
        _copy_planning_dependencies_legacy(connection)
        _copy_continuity_threads_legacy(connection)
        _copy_continuity_states_legacy(connection)
        _copy_continuity_findings_legacy(connection)
        _copy_draft_briefs_legacy(connection)
        _copy_drafting_context_packets_legacy(connection)

        _apply_operations_indexes(connection)
        _drop_legacy_tables(connection)
    except Exception:
        raise
    finally:
        connection.execute("PRAGMA foreign_keys = ON")


def _apply_operations_indexes(connection: sqlite3.Connection) -> None:
    connection.executescript(OPERATIONS_INDEXES)


def _reset_partial_rebuild_state(connection: sqlite3.Connection) -> None:
    for table_name, legacy_name in (
        ("project_artifacts", "project_artifacts__legacy"),
        ("projects", "projects__legacy"),
        ("job_logs", "job_logs__legacy"),
        ("job_events", "job_events__legacy"),
        ("jobs", "jobs__legacy"),
        ("job_attempts", "jobs__legacy"),
        ("checker_results", "checker_results__legacy"),
        ("checker_run_events", "checker_run_events__legacy"),
        ("checker_runs", "checker_runs__legacy"),
        ("checker_run_attempts", "checker_runs__legacy"),
        ("step_records", "step_records__legacy"),
        ("artifact_lineage", "artifact_lineage__legacy"),
        ("world_bible_entries", "world_bible_entries__legacy"),
        ("arc_candidates", "arc_candidates__legacy"),
        ("arc_selections", "arc_selections__legacy"),
        ("story_decision_nodes", "story_decision_nodes__legacy"),
        ("story_decision_records", "story_decision_records__legacy"),
        ("branch_points", "branch_points__legacy"),
        ("story_branches", "story_branches__legacy"),
        ("branch_state_refs", "branch_state_refs__legacy"),
        ("branch_comparisons", "branch_comparisons__legacy"),
        ("branch_merge_decisions", "branch_merge_decisions__legacy"),
        ("checker_findings", "checker_findings__legacy"),
        ("review_decisions", "review_decisions__legacy"),
        ("inspect_run_links", "inspect_run_links__legacy"),
        ("draft_artifacts", "draft_artifacts__legacy"),
        ("manuscript_documents", "manuscript_documents__legacy"),
        ("revision_suggestions", "revision_suggestions__legacy"),
        ("runtime_artifact_selections", "runtime_artifact_selections__legacy"),
        ("story_flow_definitions", "story_flow_definitions__legacy"),
        ("story_flow_stages", "story_flow_stages__legacy"),
        ("brainstorm_items", "brainstorm_items__legacy"),
        ("brain_dump_sessions", "brain_dump_sessions__legacy"),
        ("foundation_profiles", "foundation_profiles__legacy"),
        ("foundation_revisions", "foundation_revisions__legacy"),
        ("character_profiles", "character_profiles__legacy"),
        ("relationship_edges", "relationship_edges__legacy"),
        ("arc_stage_maps", "arc_stage_maps__legacy"),
        ("arc_comparisons", "arc_comparisons__legacy"),
        ("arc_selection_comparisons", "arc_selection_comparisons__legacy"),
        ("beat_plans", "beat_plans__legacy"),
        ("sequence_plans", "sequence_plans__legacy"),
        ("storyboard_cards", "storyboard_cards__legacy"),
        ("chapter_plans", "chapter_plans__legacy"),
        ("scene_plans", "scene_plans__legacy"),
        ("chapter_packets", "chapter_packets__legacy"),
        ("planning_dependencies", "planning_dependencies__legacy"),
        ("continuity_threads", "continuity_threads__legacy"),
        ("continuity_states", "continuity_states__legacy"),
        ("continuity_findings", "continuity_findings__legacy"),
        ("draft_briefs", "draft_briefs__legacy"),
        ("drafting_context_packets", "drafting_context_packets__legacy"),
    ):
        if _table_exists(connection, legacy_name) and _table_exists(connection, table_name):
            connection.execute(f"DROP TABLE {table_name}")


def _rename_table_if_exists(connection: sqlite3.Connection, table_name: str, legacy_name: str) -> None:
    if _table_exists(connection, table_name):
        connection.execute(f"ALTER TABLE {table_name} RENAME TO {legacy_name}")


def _copy_if_exists(connection: sqlite3.Connection, table_name: str, sql: str) -> None:
    if _table_exists(connection, table_name):
        connection.execute(sql)


def _backfill_job_attempts(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        INSERT INTO job_attempts (
            job_id, logical_run_id, attempt_number, status, executor_name, executor_instance_id, queue_delay_ms, lease_owner, lease_expires_at, claimed_at,
            started_at, finished_at, last_heartbeat_at, finish_reason, failure_stage, retryable, retry_reason, error_code, error_category, created_at, updated_at
        )
        SELECT
            job_id,
            logical_run_id,
            attempt_number,
            status,
            NULL,
            NULL,
            NULL,
            lease_owner,
            lease_expires_at,
            claimed_at,
            CASE WHEN status IN ('PROCESSING', 'COMPLETED', 'FAILED') THEN COALESCE(claimed_at, created_at) ELSE NULL END,
            CASE WHEN status IN ('COMPLETED', 'FAILED') THEN updated_at ELSE NULL END,
            heartbeat_at,
            CASE WHEN status = 'COMPLETED' THEN 'completed' WHEN status = 'FAILED' THEN 'failed' ELSE NULL END,
            CASE WHEN status = 'FAILED' THEN 'run' ELSE NULL END,
            CASE WHEN status = 'FAILED' THEN 0 ELSE NULL END,
            NULL,
            NULL,
            NULL,
            created_at,
            updated_at
        FROM jobs
        """
    )


def _backfill_checker_run_attempts(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        INSERT INTO checker_run_attempts (
            run_id, logical_run_id, attempt_number, status, executor_name, executor_instance_id, queue_delay_ms, lease_owner, lease_expires_at, claimed_at,
            started_at, finished_at, last_heartbeat_at, finish_reason, failure_stage, retryable, retry_reason, error_code, error_category, created_at, updated_at
        )
        SELECT
            run_id,
            logical_run_id,
            attempt_number,
            status,
            NULL,
            NULL,
            NULL,
            lease_owner,
            lease_expires_at,
            claimed_at,
            CASE WHEN status IN ('RUNNING', 'COMPLETED', 'FAILED') THEN COALESCE(claimed_at, created_at) ELSE NULL END,
            CASE WHEN status IN ('COMPLETED', 'FAILED') THEN updated_at ELSE NULL END,
            heartbeat_at,
            CASE WHEN status = 'COMPLETED' THEN 'completed' WHEN status = 'FAILED' THEN 'failed' ELSE NULL END,
            CASE WHEN status = 'FAILED' THEN 'run' ELSE NULL END,
            CASE WHEN status = 'FAILED' THEN 0 ELSE NULL END,
            NULL,
            NULL,
            NULL,
            created_at,
            updated_at
        FROM checker_runs
        """
    )


def _copy_jobs_legacy(connection: sqlite3.Connection) -> None:
    if not _table_exists(connection, "jobs__legacy"):
        return
    logical_run_expr = "logical_run_id" if _column_exists(connection, "jobs__legacy", "logical_run_id") else "job_id"
    attempt_expr = "attempt_number" if _column_exists(connection, "jobs__legacy", "attempt_number") else "1"
    request_expr = "request_json" if _column_exists(connection, "jobs__legacy", "request_json") else "payload_json"
    lease_owner_expr = "lease_owner" if _column_exists(connection, "jobs__legacy", "lease_owner") else "NULL"
    lease_expires_expr = "lease_expires_at" if _column_exists(connection, "jobs__legacy", "lease_expires_at") else "NULL"
    claimed_at_expr = "claimed_at" if _column_exists(connection, "jobs__legacy", "claimed_at") else "NULL"
    connection.execute(
        f"""
        INSERT INTO jobs (
            job_id, logical_run_id, attempt_number, project_id, phase, status, payload_json, request_json,
            idempotency_key, request_hash, request_scope, current_phase, current_step, detail, progress_current, progress_total,
            heartbeat_at, lease_owner, lease_expires_at, claimed_at, error, created_at, updated_at
        )
        SELECT
            job_id,
            COALESCE({logical_run_expr}, job_id),
            COALESCE({attempt_expr}, 1),
            project_id,
            phase,
            status,
            payload_json,
            COALESCE({request_expr}, payload_json, '{{}}'),
            NULL,
            '',
            '',
            current_phase,
            current_step,
            detail,
            progress_current,
            progress_total,
            heartbeat_at,
            {lease_owner_expr},
            {lease_expires_expr},
            {claimed_at_expr},
            error,
            created_at,
            updated_at
        FROM jobs__legacy
        """
    )


def _copy_job_events_legacy(connection: sqlite3.Connection) -> None:
    if not _table_exists(connection, "job_events__legacy"):
        return
    logical_run_expr = "logical_run_id" if _column_exists(connection, "job_events__legacy", "logical_run_id") else "job_id"
    attempt_expr = "attempt_number" if _column_exists(connection, "job_events__legacy", "attempt_number") else "1"
    payload_expr = "payload_json" if _column_exists(connection, "job_events__legacy", "payload_json") else "'{}'"
    connection.execute(
        f"""
        INSERT INTO job_events (
            event_id, job_id, logical_run_id, attempt_number, event_type, from_state, to_state, occurred_at, payload_json
        )
        SELECT
            event_id,
            job_id,
            COALESCE({logical_run_expr}, job_id),
            COALESCE({attempt_expr}, 1),
            event_type,
            from_state,
            to_state,
            occurred_at,
            COALESCE({payload_expr}, '{{}}')
        FROM job_events__legacy
        """
    )


def _copy_job_attempts_legacy(connection: sqlite3.Connection) -> None:
    if not _table_exists(connection, "job_attempts__legacy"):
        return
    connection.execute(
        """
        INSERT INTO job_attempts (
            attempt_id, job_id, logical_run_id, attempt_number, status, executor_name, executor_instance_id, queue_delay_ms, lease_owner, lease_expires_at, claimed_at,
            started_at, finished_at, last_heartbeat_at, finish_reason, failure_stage, retryable, retry_reason, error_code, error_category, created_at, updated_at
        )
        SELECT
            attempt_id, job_id, logical_run_id, attempt_number, status,
            NULL, NULL, NULL,
            lease_owner, lease_expires_at, claimed_at,
            started_at, finished_at,
            NULL, NULL, NULL, NULL,
            retry_reason, error_code, error_category, created_at, updated_at
        FROM job_attempts__legacy
        """
    )


def _copy_checker_runs_legacy(connection: sqlite3.Connection) -> None:
    if not _table_exists(connection, "checker_runs__legacy"):
        return
    logical_run_expr = "logical_run_id" if _column_exists(connection, "checker_runs__legacy", "logical_run_id") else "run_id"
    attempt_expr = "attempt_number" if _column_exists(connection, "checker_runs__legacy", "attempt_number") else "1"
    request_expr = "request_json" if _column_exists(connection, "checker_runs__legacy", "request_json") else "'{}'"
    lease_owner_expr = "lease_owner" if _column_exists(connection, "checker_runs__legacy", "lease_owner") else "NULL"
    lease_expires_expr = "lease_expires_at" if _column_exists(connection, "checker_runs__legacy", "lease_expires_at") else "NULL"
    claimed_at_expr = "claimed_at" if _column_exists(connection, "checker_runs__legacy", "claimed_at") else "NULL"
    connection.execute(
        f"""
        INSERT INTO checker_runs (
            run_id, logical_run_id, attempt_number, project_id, status, request_json, idempotency_key, request_hash, request_scope, current_role, detail,
            heartbeat_at, lease_owner, lease_expires_at, claimed_at, report_path, created_at, updated_at
        )
        SELECT
            run_id,
            COALESCE({logical_run_expr}, run_id),
            COALESCE({attempt_expr}, 1),
            project_id,
            status,
            COALESCE({request_expr}, '{{}}'),
            NULL,
            '',
            '',
            current_role,
            detail,
            heartbeat_at,
            {lease_owner_expr},
            {lease_expires_expr},
            {claimed_at_expr},
            report_path,
            created_at,
            updated_at
        FROM checker_runs__legacy
        """
    )


def _copy_checker_run_attempts_legacy(connection: sqlite3.Connection) -> None:
    if not _table_exists(connection, "checker_run_attempts__legacy"):
        return
    connection.execute(
        """
        INSERT INTO checker_run_attempts (
            attempt_id, run_id, logical_run_id, attempt_number, status, executor_name, executor_instance_id, queue_delay_ms, lease_owner, lease_expires_at, claimed_at,
            started_at, finished_at, last_heartbeat_at, finish_reason, failure_stage, retryable, retry_reason, error_code, error_category, created_at, updated_at
        )
        SELECT
            attempt_id, run_id, logical_run_id, attempt_number, status,
            NULL, NULL, NULL,
            lease_owner, lease_expires_at, claimed_at,
            started_at, finished_at,
            NULL, NULL, NULL, NULL,
            retry_reason, error_code, error_category, created_at, updated_at
        FROM checker_run_attempts__legacy
        """
    )


def _copy_checker_run_events_legacy(connection: sqlite3.Connection) -> None:
    if not _table_exists(connection, "checker_run_events__legacy"):
        return
    logical_run_expr = "logical_run_id" if _column_exists(connection, "checker_run_events__legacy", "logical_run_id") else "run_id"
    attempt_expr = "attempt_number" if _column_exists(connection, "checker_run_events__legacy", "attempt_number") else "1"
    payload_expr = "payload_json" if _column_exists(connection, "checker_run_events__legacy", "payload_json") else "'{}'"
    connection.execute(
        f"""
        INSERT INTO checker_run_events (
            event_id, run_id, logical_run_id, attempt_number, event_type, from_state, to_state, occurred_at, payload_json
        )
        SELECT
            event_id,
            run_id,
            COALESCE({logical_run_expr}, run_id),
            COALESCE({attempt_expr}, 1),
            event_type,
            from_state,
            to_state,
            occurred_at,
            COALESCE({payload_expr}, '{{}}')
        FROM checker_run_events__legacy
        """
    )


def _copy_step_records_legacy(connection: sqlite3.Connection) -> None:
    if not _table_exists(connection, "step_records__legacy"):
        return
    connection.execute(
        """
        INSERT INTO step_records (
            step_record_id, logical_run_id, run_id, run_kind, attempt_number, step_name, step_index, state, project_id,
            model_id, critic_profile, backend_name, backend_version, input_hash, output_hash, prompt_hash,
            input_artifact_refs_json, output_artifact_refs_json, started_at, finished_at, duration_seconds,
            finish_reason, error_code, error_category, executor_id, lease_owner, created_at, updated_at
        )
        SELECT
            step_record_id, logical_run_id, run_id, run_kind, attempt_number, step_name, step_index, state, project_id,
            model_id, critic_profile, backend_name, backend_version, input_hash, output_hash, prompt_hash,
            input_artifact_refs_json, output_artifact_refs_json, started_at, finished_at, duration_seconds,
            finish_reason, error_code, error_category, executor_id, lease_owner, created_at, updated_at
        FROM step_records__legacy
        """
    )


def _copy_artifact_lineage_legacy(connection: sqlite3.Connection) -> None:
    if not _table_exists(connection, "artifact_lineage__legacy"):
        return
    connection.execute(
        """
        INSERT INTO artifact_lineage (
            artifact_lineage_id, logical_run_id, run_id, run_kind, attempt_number, step_name, project_id, artifact_role,
            artifact_kind, path, content_hash, status, validation_state, produced_at, registered_at,
            supersedes_artifact_lineage_id, source_artifact_refs_json, source_content_hashes_json, output_of_step_record_id
        )
        SELECT
            artifact_lineage_id, logical_run_id, run_id, run_kind, attempt_number, step_name, project_id, artifact_role,
            artifact_kind, path, content_hash, status, validation_state, produced_at, registered_at,
            supersedes_artifact_lineage_id, source_artifact_refs_json, source_content_hashes_json, output_of_step_record_id
        FROM artifact_lineage__legacy
        """
    )


def _copy_world_bible_entries_legacy(connection: sqlite3.Connection) -> None:
    if not _table_exists(connection, "world_bible_entries__legacy"):
        return
    connection.execute(
        """
        INSERT INTO world_bible_entries (
            entry_id, project_id, entry_type, title, summary, canonical_facts_json, related_character_ids_json,
            visibility_scope, source_artifacts_json, continuity_warnings_json, writer_notes, created_at, updated_at
        )
        SELECT
            entry_id, project_id, entry_type, title, summary, canonical_facts_json, '[]',
            visibility_scope, source_artifacts_json, continuity_warnings_json, writer_notes, created_at, updated_at
        FROM world_bible_entries__legacy
        """
    )


def _copy_arc_candidates_legacy(connection: sqlite3.Connection) -> None:
    if not _table_exists(connection, "arc_candidates__legacy"):
        return
    legacy_columns = {
        row["name"]
        for row in connection.execute("PRAGMA table_info(arc_candidates__legacy)").fetchall()
    }
    # Handle both old schema (candidate_id, label) and new schema (arc_id, name)
    has_old_schema = "candidate_id" in legacy_columns
    has_new_schema = "arc_id" in legacy_columns
    if not has_old_schema and not has_new_schema:
        return
    if has_old_schema:
        rows = connection.execute(
            """
            SELECT candidate_id, project_id, label, summary, fit_notes, stage_map_json, created_at, updated_at
            FROM arc_candidates__legacy
            ORDER BY candidate_id ASC
            """
        ).fetchall()
        for row in rows:
            arc_id = f"legacy-arc-{int(row['candidate_id'])}"
            connection.execute(
                """
                INSERT INTO arc_candidates (
                    arc_id, project_id, name, summary, stage_map_notes_json, fit_notes_json, tags_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    arc_id,
                    row["project_id"],
                    row["label"],
                    row["summary"] or "",
                    _legacy_json_list(row["stage_map_json"]),
                    _legacy_json_list(row["fit_notes"]),
                    "[]",
                    row["created_at"],
                    row["updated_at"],
                ),
            )
    if has_new_schema:
        rows = connection.execute(
            """
            SELECT arc_id, project_id, name, summary, stage_map_notes_json, fit_notes_json, tags_json, created_at, updated_at
            FROM arc_candidates__legacy
            ORDER BY arc_id ASC
            """
        ).fetchall()
        for row in rows:
            connection.execute(
                """
                INSERT OR IGNORE INTO arc_candidates (
                    arc_id, project_id, name, summary, stage_map_notes_json, fit_notes_json, tags_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row["arc_id"],
                    row["project_id"],
                    row["name"],
                    row["summary"],
                    row.get("stage_map_notes_json") or "[]",
                    row.get("fit_notes_json") or "[]",
                    row.get("tags_json") or "[]",
                    row["created_at"],
                    row["updated_at"],
                ),
            )


def _copy_arc_selections_legacy(connection: sqlite3.Connection) -> None:
    if not _table_exists(connection, "arc_selections__legacy"):
        return
    legacy_columns = {
        row["name"]
        for row in connection.execute("PRAGMA table_info(arc_selections__legacy)").fetchall()
    }
    # Path 1: Intermediate schema with comparison_inputs_json
    if {"selected_arc_json", "comparison_inputs_json"}.issubset(legacy_columns):
        rows = connection.execute(
            """
            SELECT selection_id, project_id, selected_arc_id, selected_arc_json, rejected_candidate_ids_json,
                   comparison_notes_json, comparison_inputs_json, stage_map_id, created_at, updated_at
            FROM arc_selections__legacy
            ORDER BY selection_id ASC
            """
        ).fetchall()
        for row in rows:
            comparison_inputs = _parse_json_objects(row["comparison_inputs_json"])
            connection.execute(
                """
                INSERT INTO arc_selections (
                    selection_id, project_id, selected_arc_id, selected_arc_json, rejected_candidate_ids_json,
                    comparison_notes_json, stage_map_id, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row["selection_id"],
                    row["project_id"],
                    row["selected_arc_id"],
                    row["selected_arc_json"],
                    row["rejected_candidate_ids_json"],
                    row["comparison_notes_json"],
                    row["stage_map_id"],
                    row["created_at"],
                    row["updated_at"],
                ),
            )
            if len(comparison_inputs) >= 2:
                comparison_id = f"{row['selection_id']}:comparison:001"
                ranked_candidates = _rank_arc_comparison_payloads(comparison_inputs)
                connection.execute(
                    """
                    INSERT INTO arc_comparisons (
                        comparison_id, project_id, candidate_ids_json, candidate_set_json, ranked_candidates_json,
                        review_notes_json, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        comparison_id,
                        row["project_id"],
                        json.dumps([str(item.get("arc_id", "")) for item in comparison_inputs], ensure_ascii=True, sort_keys=True),
                        json.dumps(comparison_inputs, ensure_ascii=True, sort_keys=True),
                        json.dumps(ranked_candidates, ensure_ascii=True, sort_keys=True),
                        row["comparison_notes_json"],
                        row["created_at"],
                        row["updated_at"],
                    ),
                )
                connection.execute(
                    """
                    INSERT INTO arc_selection_comparisons (
                        selection_id, comparison_id, link_order, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        row["selection_id"],
                        comparison_id,
                        0,
                        row["created_at"],
                        row["updated_at"],
                    ),
                )
        return

    # Path 2: Current schema (has selected_arc_id and selected_arc_json)
    if {"selected_arc_id", "selected_arc_json"}.issubset(legacy_columns):
        rows = connection.execute(
            """
            SELECT selection_id, project_id, selected_arc_id, selected_arc_json, rejected_candidate_ids_json,
                   comparison_notes_json, stage_map_id, created_at, updated_at
            FROM arc_selections__legacy
            ORDER BY selection_id ASC
            """
        ).fetchall()
        for row in rows:
            connection.execute(
                """
                INSERT OR IGNORE INTO arc_selections (
                    selection_id, project_id, selected_arc_id, selected_arc_json, rejected_candidate_ids_json,
                    comparison_notes_json, stage_map_id, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row["selection_id"],
                    row["project_id"],
                    row["selected_arc_id"],
                    row["selected_arc_json"],
                    row.get("rejected_candidate_ids_json") or "[]",
                    row.get("comparison_notes_json") or "[]",
                    row.get("stage_map_id"),
                    row["created_at"],
                    row["updated_at"],
                ),
            )
        return

    rows = connection.execute(
        """
        SELECT selection_id, project_id, selected_arc_candidate_id, rejected_candidate_ids_json,
               comparison_history_json, created_at, updated_at
        FROM arc_selections__legacy
        ORDER BY selection_id ASC
        """
    ).fetchall()
    for row in rows:
        selected_candidate_id = row["selected_arc_candidate_id"]
        selected_arc_id = f"legacy-arc-{int(selected_candidate_id)}" if selected_candidate_id is not None else None
        selected_arc_row = None
        if selected_candidate_id is not None:
            selected_arc_row = connection.execute(
                """
                SELECT arc_id, project_id, name, summary, stage_map_notes_json, fit_notes_json, tags_json, created_at, updated_at
                FROM arc_candidates
                WHERE arc_id = ?
                """,
                (selected_arc_id,),
            ).fetchone()
        if selected_arc_row is None:
            continue
        connection.execute(
            """
            INSERT INTO arc_selections (
                selection_id, project_id, selected_arc_id, selected_arc_json, rejected_candidate_ids_json,
                comparison_notes_json, stage_map_id, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                f"legacy-selection-{int(row['selection_id'])}",
                row["project_id"],
                selected_arc_id,
                json.dumps(
                    {
                        "arc_id": selected_arc_row["arc_id"],
                        "project_id": selected_arc_row["project_id"],
                        "name": selected_arc_row["name"],
                        "summary": selected_arc_row["summary"],
                        "stage_map_notes": _parse_json_list(selected_arc_row["stage_map_notes_json"]),
                        "fit_notes": _parse_json_list(selected_arc_row["fit_notes_json"]),
                        "tags": _parse_json_list(selected_arc_row["tags_json"]),
                        "created_at": selected_arc_row["created_at"],
                        "updated_at": selected_arc_row["updated_at"],
                    },
                    ensure_ascii=True,
                    sort_keys=True,
                ),
                row["rejected_candidate_ids_json"],
                json.dumps(_legacy_json_list(row["comparison_history_json"]), ensure_ascii=True, sort_keys=True),
                None,
                row["created_at"],
                row["updated_at"],
                ),
            )


def _copy_story_decision_nodes_legacy(connection: sqlite3.Connection) -> None:
    if _table_exists(connection, "story_decision_nodes__legacy"):
        connection.execute(
            """
            INSERT INTO story_decision_nodes (
                node_record_id, node_id, project_id, node_type, change_type, subject_type, subject_id,
                parent_node_id, branch_id, summary, prior_state_ref, prior_state_summary, new_state_ref,
                new_state_summary, reason_or_note, decision_made_at, made_by, related_object_links_json,
                informing_object_links_json, created_at, updated_at
            )
            SELECT
                node_record_id, node_id, project_id, node_type, change_type, subject_type, subject_id,
                parent_node_id, branch_id, summary, prior_state_ref, prior_state_summary, new_state_ref,
                new_state_summary, reason_or_note, decision_made_at, made_by, related_object_links_json,
                informing_object_links_json, created_at, updated_at
            FROM story_decision_nodes__legacy
            """
        )
        return
    if not _table_exists(connection, "story_decision_records__legacy"):
        return
    connection.execute(
        """
        INSERT INTO story_decision_nodes (
            node_record_id, node_id, project_id, node_type, change_type, subject_type, subject_id,
            parent_node_id, branch_id, summary, prior_state_ref, prior_state_summary, new_state_ref,
            new_state_summary, reason_or_note, decision_made_at, made_by, related_object_links_json,
            informing_object_links_json, created_at, updated_at
        )
        SELECT
            decision_record_id, decision_id, project_id, 'DECISION', UPPER(decision_type), UPPER(subject_type), subject_id,
            NULL, NULL, COALESCE(reason_or_note, decision_type), prior_state_ref, prior_state_summary, new_state_ref,
            new_state_summary, reason_or_note, decision_made_at, made_by, subject_links_json,
            informing_object_refs_json, created_at, updated_at
        FROM story_decision_records__legacy
        """
    )


def _copy_branch_points_legacy(connection: sqlite3.Connection) -> None:
    if not _table_exists(connection, "branch_points__legacy"):
        return
    connection.execute(
        """
        INSERT INTO branch_points (
            branch_point_id, project_id, source_node_id, created_at, updated_at
        )
        SELECT
            branch_point_id, project_id, source_node_id, created_at, updated_at
        FROM branch_points__legacy
        """
    )


def _copy_story_branches_legacy(connection: sqlite3.Connection) -> None:
    if not _table_exists(connection, "story_branches__legacy"):
        return
    connection.execute(
        """
        INSERT INTO story_branches (
            branch_id, project_id, branch_point_id, branch_name, branch_state, created_at, updated_at
        )
        SELECT
            branch_id, project_id, branch_point_id, branch_name, branch_state, created_at, updated_at
        FROM story_branches__legacy
        """
    )


def _copy_branch_state_refs_legacy(connection: sqlite3.Connection) -> None:
    if not _table_exists(connection, "branch_state_refs__legacy"):
        return
    connection.execute(
        """
        INSERT INTO branch_state_refs (
            branch_state_ref_id, project_id, branch_id, state_object_type, state_object_id, decision_node_id,
            created_at, updated_at
        )
        SELECT
            branch_state_ref_id, project_id, branch_id, state_object_type, state_object_id, decision_node_id,
            created_at, updated_at
        FROM branch_state_refs__legacy
        """
    )


def _copy_branch_comparisons_legacy(connection: sqlite3.Connection) -> None:
    if not _table_exists(connection, "branch_comparisons__legacy"):
        return
    connection.execute(
        """
        INSERT INTO branch_comparisons (
            comparison_id, project_id, source_branch_id, target_branch_id, review_notes_json, created_at, updated_at
        )
        SELECT
            comparison_id, project_id, source_branch_id, target_branch_id, review_notes_json, created_at, updated_at
        FROM branch_comparisons__legacy
        """
    )


def _copy_branch_merge_decisions_legacy(connection: sqlite3.Connection) -> None:
    if not _table_exists(connection, "branch_merge_decisions__legacy"):
        return
    connection.execute(
        """
        INSERT INTO branch_merge_decisions (
            merge_decision_id, project_id, source_branch_id, target_branch_id, merge_rationale,
            resulting_decision_node_ids_json, created_at, updated_at
        )
        SELECT
            merge_decision_id, project_id, source_branch_id, target_branch_id, merge_rationale,
            resulting_decision_node_ids_json, created_at, updated_at
        FROM branch_merge_decisions__legacy
        """
    )


def _copy_checker_findings_legacy(connection: sqlite3.Connection) -> None:
    if not _table_exists(connection, "checker_findings__legacy"):
        return
    connection.execute(
        """
        INSERT INTO checker_findings (
            finding_id, project_id, source_object_id, source_object_kind, severity, summary, details,
            source_context_json, created_at, updated_at
        )
        SELECT
            finding_id, project_id, source_object_id, source_object_kind, severity, summary, details,
            source_context_json, created_at, updated_at
        FROM checker_findings__legacy
        """
    )


def _copy_review_decisions_legacy(connection: sqlite3.Connection) -> None:
    if not _table_exists(connection, "review_decisions__legacy"):
        return
    connection.execute(
        """
        INSERT INTO review_decisions (
            decision_id, project_id, target_id, target_kind, decision, notes, source_context_json, created_at, updated_at
        )
        SELECT
            decision_id, project_id, target_id, target_kind, decision, notes, source_context_json, created_at, updated_at
        FROM review_decisions__legacy
        """
    )


def _copy_inspect_run_links_legacy(connection: sqlite3.Connection) -> None:
    if not _table_exists(connection, "inspect_run_links__legacy"):
        return
    connection.execute(
        """
        INSERT INTO inspect_run_links (
            link_id, project_id, object_kind, object_id, logical_run_id, run_id, run_kind, attempt_number,
            label, created_at, updated_at
        )
        SELECT
            link_id, project_id, object_kind, object_id, logical_run_id, run_id, run_kind, attempt_number,
            label, created_at, updated_at
        FROM inspect_run_links__legacy
        """
    )


def _copy_draft_artifacts_legacy(connection: sqlite3.Connection) -> None:
    if not _table_exists(connection, "draft_artifacts__legacy"):
        return
    connection.execute(
        """
        INSERT INTO draft_artifacts (
            artifact_id, project_id, title, content, source_plan_ids_json, source_context_json,
            provenance_note, status, created_at, updated_at
        )
        SELECT
            artifact_id, project_id, title, content, source_plan_ids_json, source_context_json,
            provenance_note, status, created_at, updated_at
        FROM draft_artifacts__legacy
        """
    )


def _copy_manuscript_documents_legacy(connection: sqlite3.Connection) -> None:
    if not _table_exists(connection, "manuscript_documents__legacy"):
        return
    connection.execute(
        """
        INSERT INTO manuscript_documents (
            document_id, project_id, title, content, chapter_id, scene_id, current_draft_artifact_id,
            version, created_at, updated_at
        )
        SELECT
            document_id, project_id, title, content, chapter_id, scene_id, current_draft_artifact_id,
            version, created_at, updated_at
        FROM manuscript_documents__legacy
        """
    )


def _copy_revision_suggestions_legacy(connection: sqlite3.Connection) -> None:
    if not _table_exists(connection, "revision_suggestions__legacy"):
        return
    connection.execute(
        """
        INSERT INTO revision_suggestions (
            suggestion_id, project_id, target_document_id, source_text, proposed_text, rationale,
            source_context_json, status, created_at, updated_at
        )
        SELECT
            suggestion_id, project_id, target_document_id, source_text, proposed_text, rationale,
            source_context_json, status, created_at, updated_at
        FROM revision_suggestions__legacy
        """
    )


def _copy_identical_schema_legacy(connection: sqlite3.Connection, table_name: str) -> None:
    """Copy rows from legacy table to current table when schema is identical."""
    legacy_name = f"{table_name}__legacy"
    if not _table_exists(connection, legacy_name):
        return
    columns = [
        row["name"]
        for row in connection.execute(f"PRAGMA table_info({legacy_name})").fetchall()
    ]
    if not columns:
        return
    cols = ", ".join(columns)
    connection.execute(
        f"INSERT OR IGNORE INTO {table_name} ({cols}) SELECT {cols} FROM {legacy_name}"
    )


def _copy_runtime_artifact_selections_legacy(connection: sqlite3.Connection) -> None:
    _copy_identical_schema_legacy(connection, "runtime_artifact_selections")


def _copy_story_flow_definitions_legacy(connection: sqlite3.Connection) -> None:
    _copy_identical_schema_legacy(connection, "story_flow_definitions")


def _copy_story_flow_stages_legacy(connection: sqlite3.Connection) -> None:
    _copy_identical_schema_legacy(connection, "story_flow_stages")


def _copy_brainstorm_items_legacy(connection: sqlite3.Connection) -> None:
    _copy_identical_schema_legacy(connection, "brainstorm_items")


def _copy_brain_dump_sessions_legacy(connection: sqlite3.Connection) -> None:
    _copy_identical_schema_legacy(connection, "brain_dump_sessions")


def _copy_foundation_profiles_legacy(connection: sqlite3.Connection) -> None:
    _copy_identical_schema_legacy(connection, "foundation_profiles")


def _copy_foundation_revisions_legacy(connection: sqlite3.Connection) -> None:
    _copy_identical_schema_legacy(connection, "foundation_revisions")


def _copy_character_profiles_legacy(connection: sqlite3.Connection) -> None:
    _copy_identical_schema_legacy(connection, "character_profiles")


def _copy_relationship_edges_legacy(connection: sqlite3.Connection) -> None:
    _copy_identical_schema_legacy(connection, "relationship_edges")


def _copy_arc_stage_maps_legacy(connection: sqlite3.Connection) -> None:
    _copy_identical_schema_legacy(connection, "arc_stage_maps")


def _copy_arc_comparisons_legacy(connection: sqlite3.Connection) -> None:
    _copy_identical_schema_legacy(connection, "arc_comparisons")


def _copy_arc_selection_comparisons_legacy(connection: sqlite3.Connection) -> None:
    _copy_identical_schema_legacy(connection, "arc_selection_comparisons")


def _copy_beat_plans_legacy(connection: sqlite3.Connection) -> None:
    _copy_identical_schema_legacy(connection, "beat_plans")


def _copy_sequence_plans_legacy(connection: sqlite3.Connection) -> None:
    _copy_identical_schema_legacy(connection, "sequence_plans")


def _copy_storyboard_cards_legacy(connection: sqlite3.Connection) -> None:
    _copy_identical_schema_legacy(connection, "storyboard_cards")


def _copy_chapter_plans_legacy(connection: sqlite3.Connection) -> None:
    _copy_identical_schema_legacy(connection, "chapter_plans")


def _copy_scene_plans_legacy(connection: sqlite3.Connection) -> None:
    _copy_identical_schema_legacy(connection, "scene_plans")


def _copy_chapter_packets_legacy(connection: sqlite3.Connection) -> None:
    _copy_identical_schema_legacy(connection, "chapter_packets")


def _copy_planning_dependencies_legacy(connection: sqlite3.Connection) -> None:
    _copy_identical_schema_legacy(connection, "planning_dependencies")


def _copy_continuity_threads_legacy(connection: sqlite3.Connection) -> None:
    _copy_identical_schema_legacy(connection, "continuity_threads")


def _copy_continuity_states_legacy(connection: sqlite3.Connection) -> None:
    _copy_identical_schema_legacy(connection, "continuity_states")


def _copy_continuity_findings_legacy(connection: sqlite3.Connection) -> None:
    _copy_identical_schema_legacy(connection, "continuity_findings")


def _copy_draft_briefs_legacy(connection: sqlite3.Connection) -> None:
    _copy_identical_schema_legacy(connection, "draft_briefs")


def _copy_drafting_context_packets_legacy(connection: sqlite3.Connection) -> None:
    _copy_identical_schema_legacy(connection, "drafting_context_packets")


def _legacy_json_list(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return [value]
    if not isinstance(parsed, list):
        return [str(parsed)]
    result: list[str] = []
    for item in parsed:
        if isinstance(item, str):
            result.append(item)
        elif item is not None:
            result.append(json.dumps(item, ensure_ascii=True, sort_keys=True))
    return result


def _rank_arc_comparison_payloads(payloads: list[dict[str, object]]) -> list[dict[str, object]]:
    ranked: list[tuple[tuple[int, int, int, int], dict[str, object], list[str]]] = []
    for payload in payloads:
        stage_map_notes = payload.get("stage_map_notes")
        fit_notes = payload.get("fit_notes")
        tags = payload.get("tags")
        name = str(payload.get("name", ""))
        summary = str(payload.get("summary", ""))
        notes = [
            f"{name}: {len(fit_notes) if isinstance(fit_notes, list) else 0} fit note(s), {len(stage_map_notes) if isinstance(stage_map_notes, list) else 0} stage-map note(s), {len(tags) if isinstance(tags, list) else 0} tag(s)."
        ]
        score = (
            len(stage_map_notes) if isinstance(stage_map_notes, list) else 0,
            len(fit_notes) if isinstance(fit_notes, list) else 0,
            len(tags) if isinstance(tags, list) else 0,
            -len(summary.split()),
        )
        ranked.append((score, dict(payload), notes))
    ranked.sort(
        key=lambda item: (
            -item[0][0],
            -item[0][1],
            -item[0][2],
            item[0][3],
            str(item[1].get("arc_id", "")),
        )
    )
    return [
        {
            "arc_id": payload.get("arc_id"),
            "rank": index,
            "score": list(score),
            "notes": notes,
            "candidate": payload,
        }
        for index, (score, payload, notes) in enumerate(ranked, start=1)
    ]


def _drop_legacy_tables(connection: sqlite3.Connection) -> None:
    for table_name in (
        "project_artifacts__legacy",
        "projects__legacy",
        "job_logs__legacy",
        "job_events__legacy",
        "jobs__legacy",
        "job_attempts__legacy",
        "checker_results__legacy",
        "checker_run_events__legacy",
        "checker_runs__legacy",
        "checker_run_attempts__legacy",
        "step_records__legacy",
        "artifact_lineage__legacy",
        "world_bible_entries__legacy",
        "arc_candidates__legacy",
        "arc_selections__legacy",
        "story_decision_nodes__legacy",
        "branch_points__legacy",
        "story_branches__legacy",
        "branch_state_refs__legacy",
        "branch_comparisons__legacy",
        "branch_merge_decisions__legacy",
        "checker_findings__legacy",
        "review_decisions__legacy",
        "inspect_run_links__legacy",
        "draft_artifacts__legacy",
        "manuscript_documents__legacy",
        "revision_suggestions__legacy",
        "runtime_artifact_selections__legacy",
        "story_flow_definitions__legacy",
        "story_flow_stages__legacy",
        "brainstorm_items__legacy",
        "brain_dump_sessions__legacy",
        "foundation_profiles__legacy",
        "foundation_revisions__legacy",
        "character_profiles__legacy",
        "relationship_edges__legacy",
        "arc_stage_maps__legacy",
        "arc_comparisons__legacy",
        "arc_selection_comparisons__legacy",
        "beat_plans__legacy",
        "sequence_plans__legacy",
        "storyboard_cards__legacy",
        "chapter_plans__legacy",
        "scene_plans__legacy",
        "chapter_packets__legacy",
        "planning_dependencies__legacy",
        "continuity_threads__legacy",
        "continuity_states__legacy",
        "continuity_findings__legacy",
        "draft_briefs__legacy",
        "drafting_context_packets__legacy",
    ):
        if _table_exists(connection, table_name):
            connection.execute(f"DROP TABLE {table_name}")


def _backfill_job_request_identity(connection: sqlite3.Connection) -> None:
    rows = connection.execute(
        "SELECT job_id, phase, project_id, payload_json, request_json FROM jobs"
    ).fetchall()
    for row in rows:
        request_payload = _normalize_job_request_payload(
            phase=row["phase"],
            payload_json=row["payload_json"],
            request_json=row["request_json"],
        )
        connection.execute(
            """
            UPDATE jobs
            SET request_json = ?, request_hash = ?, request_scope = ?
            WHERE job_id = ?
            """,
            (
                json.dumps(request_payload, ensure_ascii=True, sort_keys=True),
                request_hash(request_payload),
                job_request_scope(phase=row["phase"], project_id=row["project_id"]),
                row["job_id"],
            ),
        )


def _backfill_checker_run_request_identity(connection: sqlite3.Connection) -> None:
    rows = connection.execute(
        "SELECT run_id, request_json FROM checker_runs"
    ).fetchall()
    for row in rows:
        request_payload = json.loads(row["request_json"] or "{}")
        roles = [str(role) for role in request_payload.get("roles", [])]
        critic_profile = str(request_payload.get("critic_profile", "minimal_context"))
        connection.execute(
            """
            UPDATE checker_runs
            SET request_hash = ?, request_scope = ?
            WHERE run_id = ?
            """,
            (
                request_hash(request_payload),
                checker_request_scope(roles=roles, critic_profile=critic_profile),
                row["run_id"],
            ),
        )


def _normalize_job_request_payload(*, phase: str, payload_json: str, request_json: str) -> dict[str, object]:
    payload = json.loads(payload_json or "{}")
    request_payload = json.loads(request_json or "{}")
    if "phase" in request_payload and "payload" in request_payload:
        return request_payload
    return {
        "phase": phase,
        "payload": payload,
    }


def _table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
    row = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone()
    return row is not None


def _column_exists(connection: sqlite3.Connection, table_name: str, column_name: str) -> bool:
    rows = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    return any(row["name"] == column_name for row in rows)


def _get_user_version(connection: sqlite3.Connection) -> int:
    return int(connection.execute("PRAGMA user_version").fetchone()[0])


def _set_user_version(connection: sqlite3.Connection, version: int) -> None:
    connection.execute(f"PRAGMA user_version = {version}")
