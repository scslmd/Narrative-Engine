from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Mapping

from .records import *  # noqa: F403
from .shared_utils import (
    parse_json_list as _parse_json_list,
    parse_json_object as _parse_json_object,
    parse_json_objects as _parse_json_objects,
)

def _relationship_edge_row_to_record(row) -> RelationshipEdgeRecord:
    return RelationshipEdgeRecord(
        edge_id=row["edge_id"],
        project_id=row["project_id"],
        source_character_id=row["source_character_id"],
        target_character_id=row["target_character_id"],
        relation_kind=row["relation_kind"],
        summary=row["summary"],
        tension=row["tension"],
        notes=row["notes"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _arc_candidate_row_to_record(row) -> ArcCandidateRecord:
    return ArcCandidateRecord(
        arc_id=row["arc_id"],
        project_id=row["project_id"],
        name=row["name"],
        summary=row["summary"],
        stage_map_notes=_parse_json_list(row["stage_map_notes_json"]),
        fit_notes=_parse_json_list(row["fit_notes_json"]),
        tags=_parse_json_list(row["tags_json"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _arc_stage_map_row_to_record(row) -> ArcStageMapRecord:
    return ArcStageMapRecord(
        arc_stage_map_id=row["arc_stage_map_id"],
        project_id=row["project_id"],
        arc_id=row["arc_id"],
        stage_kinds=_parse_json_list(row["stage_kinds_json"]),
        notes=row["notes"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _arc_selection_row_to_record(row, *, repository: StoryDevelopmentRepository | None = None) -> ArcSelectionRecord:
    selected_arc = _arc_candidate_record_from_json(row["selected_arc_json"])
    comparison_record_ids = repository._arc_selection_comparison_ids(row["selection_id"]) if repository is not None else []
    stage_map = None
    if repository is not None and row["stage_map_id"] is not None:
        try:
            stage_map = repository.get_arc_stage_map(row["project_id"], arc_id=selected_arc.arc_id)
        except KeyError:
            stage_map = None
    return ArcSelectionRecord(
        selection_id=row["selection_id"],
        project_id=row["project_id"],
        selected_arc_id=row["selected_arc_id"],
        selected_arc=selected_arc,
        rejected_arc_ids=_parse_json_list(row["rejected_candidate_ids_json"]),
        comparison_notes=_parse_json_list(row["comparison_notes_json"]),
        comparison_record_ids=comparison_record_ids,
        stage_map_id=row["stage_map_id"],
        stage_map=stage_map,
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _story_decision_node_link_records(value: str | None) -> list[StoryDecisionNodeLinkRecord]:
    return [
        StoryDecisionNodeLinkRecord(
            object_type=str(item.get("object_type") or item.get("subject_type") or item.get("object_kind") or ""),
            object_id=str(item.get("object_id") or item.get("subject_id") or ""),
            relation_kind=str(item.get("relation_kind") or "related"),
        )
        for item in _parse_json_objects(value)
    ]


def _branch_point_row_to_record(row) -> BranchPointRecord:
    return BranchPointRecord(
        branch_point_id=row["branch_point_id"],
        project_id=row["project_id"],
        source_node_id=row["source_node_id"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _story_branch_row_to_record(row) -> StoryBranchRecord:
    return StoryBranchRecord(
        branch_id=row["branch_id"],
        project_id=row["project_id"],
        branch_point_id=row["branch_point_id"],
        branch_name=row["branch_name"],
        branch_state=StoryBranchState[row["branch_state"]],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _branch_state_ref_row_to_record(row) -> BranchStateRefRecord:
    return BranchStateRefRecord(
        branch_state_ref_id=row["branch_state_ref_id"],
        project_id=row["project_id"],
        branch_id=row["branch_id"],
        state_object_type=StoryObjectType[row["state_object_type"]],
        state_object_id=row["state_object_id"],
        decision_node_id=row["decision_node_id"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _branch_comparison_row_to_record(row) -> BranchComparisonRecord:
    return BranchComparisonRecord(
        comparison_id=row["comparison_id"],
        project_id=row["project_id"],
        source_branch_id=row["source_branch_id"],
        target_branch_id=row["target_branch_id"],
        review_notes=_parse_json_list(row["review_notes_json"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _branch_merge_decision_row_to_record(row) -> BranchMergeDecisionRecord:
    return BranchMergeDecisionRecord(
        merge_decision_id=row["merge_decision_id"],
        project_id=row["project_id"],
        source_branch_id=row["source_branch_id"],
        target_branch_id=row["target_branch_id"],
        merge_rationale=row["merge_rationale"],
        resulting_decision_node_ids=_parse_json_list(row["resulting_decision_node_ids_json"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _story_decision_node_row_to_record(row) -> StoryDecisionNodeRecord:
    return StoryDecisionNodeRecord(
        node_record_id=row["node_record_id"],
        node_id=row["node_id"],
        project_id=row["project_id"],
        node_type=row["node_type"],
        change_type=row["change_type"],
        subject_type=row["subject_type"],
        subject_id=row["subject_id"],
        parent_node_id=row["parent_node_id"],
        branch_id=row["branch_id"],
        summary=row["summary"],
        prior_state_ref=row["prior_state_ref"],
        prior_state_summary=row["prior_state_summary"],
        new_state_ref=row["new_state_ref"],
        new_state_summary=row["new_state_summary"],
        reason_or_note=row["reason_or_note"],
        decision_made_at=datetime.fromisoformat(row["decision_made_at"]),
        made_by=row["made_by"],
        related_object_links=_story_decision_node_link_records(row["related_object_links_json"]),
        informing_object_links=_story_decision_node_link_records(row["informing_object_links_json"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _checker_finding_row_to_record(row) -> CheckerFindingRecord:
    return CheckerFindingRecord(
        finding_id=row["finding_id"],
        project_id=row["project_id"],
        source_object_id=row["source_object_id"],
        source_object_kind=row["source_object_kind"],
        severity=row["severity"],
        summary=row["summary"],
        details=row["details"],
        source_context=_parse_json_list(row["source_context_json"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _review_decision_row_to_record(row) -> ReviewDecisionRecord:
    return ReviewDecisionRecord(
        decision_id=row["decision_id"],
        project_id=row["project_id"],
        target_id=row["target_id"],
        target_kind=row["target_kind"],
        decision=row["decision"],
        notes=row["notes"],
        source_context=_parse_json_list(row["source_context_json"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _inspect_run_link_row_to_record(row) -> InspectRunLinkRecord:
    attempt_number = row["attempt_number"]
    return InspectRunLinkRecord(
        link_id=row["link_id"],
        project_id=row["project_id"],
        object_kind=row["object_kind"],
        object_id=row["object_id"],
        logical_run_id=row["logical_run_id"],
        run_id=row["run_id"],
        run_kind=row["run_kind"],
        attempt_number=int(attempt_number) if attempt_number is not None else None,
        label=row["label"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _draft_artifact_row_to_record(row) -> DraftArtifactRecord:
    return DraftArtifactRecord(
        artifact_id=row["artifact_id"],
        project_id=row["project_id"],
        title=row["title"],
        content=row["content"],
        source_plan_ids=_parse_json_list(row["source_plan_ids_json"]),
        source_context=_parse_json_list(row["source_context_json"]),
        provenance_note=row["provenance_note"],
        status=StoryArtifactLifecycleState(row["status"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _manuscript_document_row_to_record(row) -> ManuscriptDocumentRecord:
    return ManuscriptDocumentRecord(
        document_id=row["document_id"],
        project_id=row["project_id"],
        title=row["title"],
        display_title=row["display_title"],
        content=row["content"],
        chapter_id=row["chapter_id"],
        scene_id=row["scene_id"],
        current_draft_artifact_id=row["current_draft_artifact_id"],
        version=int(row["version"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _revision_suggestion_row_to_record(row) -> RevisionSuggestionRecord:
    return RevisionSuggestionRecord(
        suggestion_id=row["suggestion_id"],
        project_id=row["project_id"],
        target_document_id=row["target_document_id"],
        source_text=row["source_text"],
        proposed_text=row["proposed_text"],
        rationale=row["rationale"],
        source_context=_parse_json_list(row["source_context_json"]),
        status=StorySuggestionLifecycleState(row["status"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _arc_candidate_record_to_mapping(record: ArcCandidateRecord) -> dict[str, Any]:
    return {
        "arc_id": record.arc_id,
        "project_id": record.project_id,
        "name": record.name,
        "summary": record.summary,
        "stage_map_notes": list(record.stage_map_notes),
        "fit_notes": list(record.fit_notes),
        "tags": list(record.tags),
        "created_at": record.created_at.isoformat(),
        "updated_at": record.updated_at.isoformat(),
    }


def _arc_candidate_record_from_mapping(value: Mapping[str, Any]) -> ArcCandidateRecord:
    candidate_payload = {
        key: value[key]
        for key in ("arc_id", "project_id", "name", "summary", "stage_map_notes", "fit_notes", "tags")
        if key in value
    }
    candidate = ArcCandidate.model_validate(candidate_payload)
    return ArcCandidateRecord(
        arc_id=candidate.arc_id,
        project_id=candidate.project_id,
        name=candidate.name,
        summary=candidate.summary,
        stage_map_notes=list(candidate.stage_map_notes),
        fit_notes=list(candidate.fit_notes),
        tags=list(candidate.tags),
        created_at=datetime.fromisoformat(str(value["created_at"])) if "created_at" in value else datetime.now(timezone.utc),
        updated_at=datetime.fromisoformat(str(value["updated_at"])) if "updated_at" in value else datetime.now(timezone.utc),
    )


def _arc_candidate_record_from_json(value: str) -> ArcCandidateRecord:
    return _arc_candidate_record_from_mapping(json.loads(value))


def _arc_comparison_candidate_record_to_mapping(record: ArcComparisonCandidateRecord) -> dict[str, Any]:
    return {
        "candidate": _arc_candidate_record_to_mapping(record.candidate),
        "rank": record.rank,
        "score": list(record.score),
        "notes": list(record.notes),
    }


def _arc_comparison_candidate_record_from_mapping(value: Mapping[str, Any]) -> ArcComparisonCandidateRecord:
    if "candidate" in value and isinstance(value["candidate"], Mapping):
        candidate_mapping = value["candidate"]
    else:
        candidate_mapping = value
    candidate = _arc_candidate_record_from_mapping(candidate_mapping)
    rank = int(value.get("rank", 0))
    score_raw = value.get("score", (0, 0, 0, 0))
    if isinstance(score_raw, (list, tuple)):
        score_values = list(score_raw)
    else:
        score_values = [score_raw]
    score = tuple(int(item) for item in score_values)
    if len(score) != 4:
        raise ValueError("score must contain four integers")
    notes = _parse_notes(value.get("notes", []))
    return ArcComparisonCandidateRecord(
        candidate=candidate,
        rank=rank,
        score=score,  # type: ignore[arg-type]
        notes=notes,
    )


def _arc_comparison_row_to_record(row) -> ArcComparisonRecord:
    candidate_set = [
        _arc_candidate_record_from_mapping(item)
        for item in _parse_json_objects(row["candidate_set_json"])
    ]
    ranked_candidates = [
        _arc_comparison_candidate_record_from_mapping(item)
        for item in _parse_json_objects(row["ranked_candidates_json"])
    ]
    return ArcComparisonRecord(
        comparison_id=row["comparison_id"],
        project_id=row["project_id"],
        candidate_ids=_parse_json_list(row["candidate_ids_json"]),
        candidate_set=candidate_set,
        ranked_candidates=ranked_candidates,
        review_notes=_parse_json_list(row["review_notes_json"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _coerce_arc_candidate(project_id: str, candidate: ArcCandidate | ArcCandidateRecord | Mapping[str, Any]) -> ArcCandidateRecord:
    if isinstance(candidate, ArcCandidateRecord):
        if candidate.project_id != project_id:
            raise ValueError("candidate.project_id must match the selected project")
        return candidate
    if isinstance(candidate, ArcCandidate):
        if candidate.project_id != project_id:
            raise ValueError("candidate.project_id must match the selected project")
        return ArcCandidateRecord(
            arc_id=candidate.arc_id,
            project_id=candidate.project_id,
            name=candidate.name,
            summary=candidate.summary,
            stage_map_notes=list(candidate.stage_map_notes),
            fit_notes=list(candidate.fit_notes),
            tags=list(candidate.tags),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
    normalized = ArcCandidate.model_validate(
        {
            key: candidate[key]
            for key in ("arc_id", "project_id", "name", "summary", "stage_map_notes", "fit_notes", "tags")
            if key in candidate
        }
    )
    if normalized.project_id != project_id:
        raise ValueError("candidate.project_id must match the selected project")
    return ArcCandidateRecord(
        arc_id=normalized.arc_id,
        project_id=normalized.project_id,
        name=normalized.name,
        summary=normalized.summary,
        stage_map_notes=list(normalized.stage_map_notes),
        fit_notes=list(normalized.fit_notes),
        tags=list(normalized.tags),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


def _coerce_arc_comparison_candidate(
    project_id: str,
    candidate: ArcComparisonCandidateRecord | Mapping[str, Any],
) -> ArcComparisonCandidateRecord:
    if isinstance(candidate, ArcComparisonCandidateRecord):
        if candidate.candidate.project_id != project_id:
            raise ValueError("candidate.project_id must match the selected project")
        return candidate
    normalized = _arc_comparison_candidate_record_from_mapping(candidate)
    if normalized.candidate.project_id != project_id:
        raise ValueError("candidate.project_id must match the selected project")
    return normalized


def _rank_arc_comparison_candidates(candidates: Sequence[ArcCandidateRecord]) -> list[ArcComparisonCandidateRecord]:
    scored = [
        (
            _candidate_score(candidate),
            candidate,
            _candidate_notes(candidate),
        )
        for candidate in _unique_arc_candidate_records(list(candidates))
    ]
    scored.sort(key=lambda item: (-item[0][0], -item[0][1], -item[0][2], item[0][3], item[1].arc_id))
    return [
        ArcComparisonCandidateRecord(candidate=candidate, rank=index, score=score, notes=list(notes))
        for index, (score, candidate, notes) in enumerate(scored, start=1)
    ]


def _unique_arc_candidate_records(candidates: Sequence[ArcCandidateRecord]) -> list[ArcCandidateRecord]:
    unique: dict[str, ArcCandidateRecord] = {}
    for candidate in candidates:
        unique.setdefault(candidate.arc_id, candidate)
    return list(unique.values())


def _unique_arc_comparison_ranked_candidates(
    candidates: Sequence[ArcComparisonCandidateRecord],
) -> list[ArcComparisonCandidateRecord]:
    unique: dict[str, ArcComparisonCandidateRecord] = {}
    ordered = sorted(candidates, key=lambda item: (item.rank, item.candidate.arc_id))
    for candidate in ordered:
        unique.setdefault(candidate.candidate.arc_id, candidate)
    return list(unique.values())


def _candidate_score(candidate: ArcCandidateRecord) -> tuple[int, int, int, int]:
    return (
        len(candidate.stage_map_notes),
        len(candidate.fit_notes),
        len(candidate.tags),
        -len(candidate.summary.split()),
    )


def _candidate_notes(candidate: ArcCandidateRecord) -> tuple[str, ...]:
    notes = [
        f"{candidate.name}: {len(candidate.fit_notes)} fit note(s), {len(candidate.stage_map_notes)} stage-map note(s), {len(candidate.tags)} tag(s)."
    ]
    if candidate.fit_notes:
        notes.append(f"Fit notes: {', '.join(candidate.fit_notes)}")
    if candidate.stage_map_notes:
        notes.append(f"Stage map notes: {', '.join(candidate.stage_map_notes)}")
    if candidate.tags:
        notes.append(f"Tags: {', '.join(candidate.tags)}")
    return tuple(notes)


def _normalize_text_list(values: Sequence[str] | None, *, field_name: str) -> list[str]:
    if values is None:
        return []
    normalized: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not isinstance(value, str):
            raise TypeError(f"{field_name} must be a list of strings")
        stripped = value.strip()
        if not stripped:
            raise ValueError(f"{field_name} must not contain blank values")
        if stripped in seen:
            continue
        seen.add(stripped)
        normalized.append(stripped)
    return normalized


def _parse_notes(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def _coerce_arc_stage_map(
    project_id: str,
    stage_map: ArcStageMap | ArcStageMapRecord | Mapping[str, Any],
) -> ArcStageMapRecord:
    if isinstance(stage_map, ArcStageMapRecord):
        if stage_map.project_id != project_id:
            raise ValueError("stage_map.project_id must match the selected project")
        return stage_map
    if isinstance(stage_map, ArcStageMap):
        if stage_map.project_id != project_id:
            raise ValueError("stage_map.project_id must match the selected project")
        return ArcStageMapRecord(
            arc_stage_map_id=stage_map.arc_stage_map_id,
            project_id=stage_map.project_id,
            arc_id=stage_map.arc_id,
            stage_kinds=list(stage_map.stage_kinds),
            notes=stage_map.notes,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
    normalized = ArcStageMap.model_validate(
        {
            key: stage_map[key]
            for key in ("arc_stage_map_id", "project_id", "arc_id", "stage_kinds", "notes")
            if key in stage_map
        }
    )
    if normalized.project_id != project_id:
        raise ValueError("stage_map.project_id must match the selected project")
    return ArcStageMapRecord(
        arc_stage_map_id=normalized.arc_stage_map_id,
        project_id=normalized.project_id,
        arc_id=normalized.arc_id,
        stage_kinds=list(normalized.stage_kinds),
        notes=normalized.notes,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


def _beat_plan_row_to_record(row) -> BeatPlanRecord:
    return BeatPlanRecord(
        beat_id=row["beat_id"],
        project_id=row["project_id"],
        objective=row["objective"],
        conflict=row["conflict"],
        stakes=row["stakes"],
        dependency_ids=_parse_json_list(row["dependency_ids_json"]),
        arc_stage=row["arc_stage"],
        active_character_ids=_parse_json_list(row["active_character_ids_json"]),
        continuity_requirements=_parse_json_list(row["continuity_requirements_json"]),
        unresolved_questions=_parse_json_list(row["unresolved_questions_json"]),
        status=row["status"],
        position=int(row["position"]),
        provenance_note=row["provenance_note"],
        confidence_score=float(row["confidence_score"] or 0.0),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _sequence_plan_row_to_record(row) -> SequencePlanRecord:
    return SequencePlanRecord(
        sequence_id=row["sequence_id"],
        project_id=row["project_id"],
        title=row["title"],
        summary=row["summary"],
        beat_ids=_parse_json_list(row["beat_ids_json"]),
        chapter_ids=_parse_json_list(row["chapter_ids_json"]),
        status=row["status"],
        position=int(row["position"]),
        provenance_note=row["provenance_note"],
        confidence_score=float(row["confidence_score"] or 0.0),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _chapter_plan_row_to_record(row) -> ChapterPlanRecord:
    return ChapterPlanRecord(
        chapter_id=row["chapter_id"],
        project_id=row["project_id"],
        sequence_id=row["sequence_id"],
        title=row["title"],
        summary=row["summary"],
        objective=row["objective"],
        conflict=row["conflict"],
        stakes=row["stakes"],
        active_character_ids=_parse_json_list(row["active_character_ids_json"]),
        continuity_requirements=_parse_json_list(row["continuity_requirements_json"]),
        unresolved_questions=_parse_json_list(row["unresolved_questions_json"]),
        status=row["status"],
        position=int(row["position"]),
        provenance_note=row["provenance_note"],
        confidence_score=float(row["confidence_score"] or 0.0),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
        target_word_count=row["target_word_count"],
    )


def _scene_plan_row_to_record(row) -> ScenePlanRecord:
    return ScenePlanRecord(
        scene_id=row["scene_id"],
        project_id=row["project_id"],
        chapter_id=row["chapter_id"],
        title=row["title"],
        summary=row["summary"],
        objective=row["objective"],
        conflict=row["conflict"],
        stakes=row["stakes"],
        active_character_ids=_parse_json_list(row["active_character_ids_json"]),
        continuity_requirements=_parse_json_list(row["continuity_requirements_json"]),
        unresolved_questions=_parse_json_list(row["unresolved_questions_json"]),
        status=row["status"],
        position=int(row["position"]),
        provenance_note=row["provenance_note"],
        confidence_score=float(row["confidence_score"] or 0.0),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _chapter_packet_row_to_record(row) -> ChapterPacketRecord:
    return ChapterPacketRecord(
        packet_id=row["packet_id"],
        project_id=row["project_id"],
        chapter_id=row["chapter_id"],
        included_reference_ids=_parse_json_list(row["included_reference_ids_json"]),
        constraints=_parse_json_list(row["constraints_json"]),
        scene_goals=_parse_json_list(row["scene_goals_json"]),
        status=row["status"],
        provenance_note=row["provenance_note"],
        confidence_score=float(row["confidence_score"] or 0.0),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _planning_dependency_row_to_record(row) -> PlanningDependencyRecord:
    return PlanningDependencyRecord(
        dependency_id=row["dependency_id"],
        project_id=row["project_id"],
        upstream_id=row["upstream_id"],
        downstream_id=row["downstream_id"],
        dependency_kind=row["dependency_kind"],
        reason=row["reason"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _continuity_thread_row_to_record(row) -> ContinuityThreadRecord:
    return ContinuityThreadRecord(
        thread_id=row["thread_id"],
        project_id=row["project_id"],
        title=row["title"],
        summary=row["summary"],
        status=row["status"],
        chapter_ids=_parse_json_list(row["chapter_ids_json"]),
        character_ids=_parse_json_list(row["character_ids_json"]),
        evidence=_parse_json_list(row["evidence_json"]),
        provenance_note=row["provenance_note"],
        confidence_score=float(row["confidence_score"] or 0.0),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _continuity_state_row_to_record(row) -> ContinuityStateRecord:
    return ContinuityStateRecord(
        state_id=row["state_id"],
        project_id=row["project_id"],
        chapter_id=row["chapter_id"],
        summary=row["summary"],
        active_threads=_parse_json_list(row["active_threads_json"]),
        resolved_threads=_parse_json_list(row["resolved_threads_json"]),
        character_states=dict(json.loads(row["character_states_json"] or "{}")),
        world_facts=_parse_json_list(row["world_facts_json"]),
        unresolved_questions=_parse_json_list(row["unresolved_questions_json"]),
        contradictions=_parse_json_list(row["contradictions_json"]),
        status=row["status"],
        provenance_note=row["provenance_note"],
        confidence_score=float(row["confidence_score"] or 0.0),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _continuity_finding_row_to_record(row) -> ContinuityFindingRecord:
    return ContinuityFindingRecord(
        finding_id=int(row["finding_id"]),
        project_id=row["project_id"],
        finding_key=row["finding_key"],
        overall_confidence=float(row["overall_confidence"] or 0.0),
        status=row["status"],
        contradictions=_parse_json_list(row["contradictions_json"]),
        unresolved_questions=_parse_json_list(row["unresolved_questions_json"]),
        provenance_note=row["provenance_note"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _draft_brief_row_to_record(row) -> DraftBriefRecord:
    return DraftBriefRecord(
        brief_id=row["brief_id"],
        project_id=row["project_id"],
        chapter_id=row["chapter_id"],
        objective=row["objective"],
        emotional_turn=row["emotional_turn"],
        continuity_obligations=_parse_json_list(row["continuity_obligations_json"]),
        required_callbacks=_parse_json_list(row["required_callbacks_json"]),
        forbidden_contradictions=_parse_json_list(row["forbidden_contradictions_json"]),
        voice_guidance=row["voice_guidance"],
        status=row["status"],
        provenance_note=row["provenance_note"],
        confidence_score=float(row["confidence_score"] or 0.0),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _drafting_context_packet_row_to_record(row) -> DraftingContextPacketRecord:
    return DraftingContextPacketRecord(
        packet_id=row["packet_id"],
        project_id=row["project_id"],
        brief_id=row["brief_id"],
        character_anchors=_parse_json_list(row["character_anchors_json"]),
        world_constraints=_parse_json_list(row["world_constraints_json"]),
        prior_summaries=_parse_json_list(row["prior_summaries_json"]),
        pattern_guidance=dict(json.loads(row["pattern_guidance_json"] or "{}")),
        status=row["status"],
        provenance_note=row["provenance_note"],
        confidence_score=float(row["confidence_score"] or 0.0),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _canon_generation_run_row_to_record(row) -> CanonGenerationRunRecord:
    return CanonGenerationRunRecord(
        generation_id=row["generation_id"],
        source_project_id=row["source_project_id"],
        target_project_id=row["target_project_id"],
        mode=row["mode"],
        request_json=dict(json.loads(row["request_json"] or "{}")),
        canon_scope_json=dict(json.loads(row["canon_scope_json"] or "{}")),
        canon_policy_json=dict(json.loads(row["canon_policy_json"] or "{}")),
        status=row["status"],
        gate_status=row["gate_status"],
        warnings=_parse_json_list(row["warnings_json"]),
        created_job_ids=_parse_json_list(row["created_job_ids_json"]),
        created_artifacts=_parse_json_objects(row["created_artifacts_json"]),
        idempotency_key=row["idempotency_key"],
        request_hash=row["request_hash"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _canon_generation_packet_row_to_record(row) -> CanonGenerationPacketRecord:
    return CanonGenerationPacketRecord(
        packet_id=row["packet_id"],
        generation_id=row["generation_id"],
        source_project_id=row["source_project_id"],
        target_project_id=row["target_project_id"],
        packet_json=dict(json.loads(row["packet_json"] or "{}")),
        source_hashes_json=dict(json.loads(row["source_hashes_json"] or "{}")),
        prompt_budget_json=dict(json.loads(row["prompt_budget_json"] or "{}")),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _generation_gate_result_row_to_record(row) -> GenerationGateResultRecord:
    return GenerationGateResultRecord(
        gate_result_id=row["gate_result_id"],
        generation_id=row["generation_id"],
        project_id=row["project_id"],
        artifact_kind=row["artifact_kind"],
        artifact_id=row["artifact_id"],
        gate_name=row["gate_name"],
        passed=bool(row["passed"]),
        severity=row["severity"],
        reasons=_parse_json_list(row["reasons_json"]),
        repair_attempted=bool(row["repair_attempted"]),
        repair_job_id=row["repair_job_id"],
        created_at=datetime.fromisoformat(row["created_at"]),
    )


def _manuscript_assist_run_row_to_record(row) -> ManuscriptAssistRunRecord:
    return ManuscriptAssistRunRecord(
        assist_id=row["assist_id"],
        project_id=row["project_id"],
        document_id=row["document_id"],
        assist_kind=row["assist_kind"],
        request_json=dict(json.loads(row["request_json"] or "{}")),
        status=row["status"],
        summary=row["summary"] or "",
        created_draft_artifact_id=row["created_draft_artifact_id"],
        created_branch_id=row["created_branch_id"],
        created_manuscript_document_id=row["created_manuscript_document_id"],
        job_ids=_parse_json_list(row["job_ids_json"]),
        warnings=_parse_json_list(row["warnings_json"]),
        idempotency_key=row["idempotency_key"],
        request_hash=row["request_hash"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _manuscript_assist_suggestion_row_to_record(row) -> ManuscriptAssistSuggestionRecord:
    return ManuscriptAssistSuggestionRecord(
        suggestion_id=row["suggestion_id"],
        assist_id=row["assist_id"],
        project_id=row["project_id"],
        target_document_id=row["target_document_id"],
        suggestion_kind=row["suggestion_kind"],
        source_text=row["source_text"],
        proposed_text=row["proposed_text"],
        rationale=row["rationale"],
        range_json=_parse_json_object(row["range_json"]),
        canon_risk=row["canon_risk"],
        confidence_score=float(row["confidence_score"] or 0.0),
        source_context=_parse_json_list(row["source_context_json"]),
        status=row["status"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _manuscript_assist_gate_result_row_to_record(row) -> ManuscriptAssistGateResultRecord:
    return ManuscriptAssistGateResultRecord(
        gate_result_id=row["gate_result_id"],
        assist_id=row["assist_id"],
        project_id=row["project_id"],
        document_id=row["document_id"],
        gate_name=row["gate_name"],
        passed=bool(row["passed"]),
        severity=row["severity"],
        reasons=_parse_json_list(row["reasons_json"]),
        created_at=datetime.fromisoformat(row["created_at"]),
    )


def _canon_annotation_row_to_record(row) -> CanonAnnotationRecord:
    return CanonAnnotationRecord(
        annotation_id=row["annotation_id"],
        project_id=row["project_id"],
        target_kind=row["target_kind"],
        target_id=row["target_id"],
        field_path=row["field_path"],
        annotation_kind=row["annotation_kind"],
        note=row["note"] or "",
        applies_to_modes=_parse_json_list(row["applies_to_modes_json"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _canon_customization_profile_row_to_record(row) -> CanonCustomizationProfileRecord:
    return CanonCustomizationProfileRecord(
        profile_id=row["profile_id"],
        project_id=row["project_id"],
        name=row["name"],
        description=row["description"] or "",
        default_generation_mode=row["default_generation_mode"],
        canon_scope_json=dict(json.loads(row["canon_scope_json"] or "{}")),
        canon_policy_json=dict(json.loads(row["canon_policy_json"] or "{}")),
        generation_brief_template=row["generation_brief_template"] or "",
        selected_annotation_ids=_parse_json_list(row["selected_annotation_ids_json"]),
        status=row["status"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _mythos_entry_row_to_record(row) -> MythosEntryRecord:
    return MythosEntryRecord(
        mythos_id=row["mythos_id"],
        project_id=row["project_id"],
        entry_type=row["entry_type"],
        name=row["name"],
        summary=row["summary"] or "",
        canonical_facts=_parse_json_list(row["canonical_facts_json"]),
        pattern_notes=_parse_json_list(row["pattern_notes_json"]),
        source_corpus=row["source_corpus"],
        generation_guidance=row["generation_guidance"] or "",
        visibility_scope=row["visibility_scope"],
        writer_notes=row["writer_notes"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _pattern_entry_row_to_record(row) -> PatternEntryRecord:
    return PatternEntryRecord(
        pattern_id=row["pattern_id"],
        project_id=row["project_id"],
        pattern_type=row["pattern_type"],
        name=row["name"],
        summary=row["summary"] or "",
        source_type=row["source_type"],
        generation_modes=_parse_json_list(row["generation_modes_json"]),
        beats=_parse_json_list(row["beats_json"]),
        constraints=_parse_json_list(row["constraints_json"]),
        transposition_notes=row["transposition_notes"] or "",
        writer_notes=row["writer_notes"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _stage_row_to_record(row) -> StoryFlowStageRecord:
    return StoryFlowStageRecord(
        stage_id=int(row["stage_id"]),
        project_id=row["project_id"],
        stage_key=row["stage_key"],
        stage_kind=row["stage_kind"],
        is_custom=bool(row["is_custom"]),
        display_name=row["display_name"],
        description=row["description"],
        position=int(row["position"]),
        depends_on=_parse_json_list(row["depends_on_json"]),
        stage_configuration_state=StoryFlowStageConfigurationState(row["stage_configuration_state"]),
        stage_progress_state=StoryFlowStageProgressState(row["stage_progress_state"]),
        writer_notes=row["writer_notes"],
        custom_prompt_guidance=row["custom_prompt_guidance"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _brainstorm_row_to_record(row) -> BrainstormItemRecord:
    return BrainstormItemRecord(
        item_id=int(row["item_id"]),
        project_id=row["project_id"],
        cluster_key=row["cluster_key"],
        content=row["content"],
        item_state=row["item_state"],
        tags=_parse_json_list(row["tags_json"]),
        source_artifact_refs=_parse_json_list(row["source_artifact_refs_json"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _foundation_revision_row_to_record(row) -> FoundationRevisionRecord:
    return FoundationRevisionRecord(
        revision_id=int(row["revision_id"]),
        project_id=row["project_id"],
        revision_number=int(row["revision_number"]),
        premise=row["premise"],
        logline=row["logline"],
        thematic_spine=row["thematic_spine"],
        emotional_promise=row["emotional_promise"],
        tone_direction=row["tone_direction"],
        target_audience=row["target_audience"],
        narrative_constraints=_parse_json_list(row["narrative_constraints_json"]),
        complexity_level=row["complexity_level"],
        success_definition=row["success_definition"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _character_row_to_record(row) -> CharacterProfileRecord:
    return CharacterProfileRecord(
        character_id=row["character_id"],
        project_id=row["project_id"],
        display_name=row["display_name"],
        role_in_story=row["role_in_story"],
        archetype=row["archetype"],
        external_goal=row["external_goal"],
        internal_need=row["internal_need"],
        misbelief_or_wound=row["misbelief_or_wound"],
        core_fear=row["core_fear"],
        primary_strength=row["primary_strength"],
        fatal_flaw_or_limitation=row["fatal_flaw_or_limitation"],
        contradictions=_parse_json_list(row["contradictions_json"]),
        backstory_summary=row["backstory_summary"],
        voice_notes=row["voice_notes"],
        relationship_map=_parse_json_list(row["relationship_map_json"]),
        secrets=_parse_json_list(row["secrets_json"]),
        values=_parse_json_list(row["values_json"]),
        taboos=_parse_json_list(row["taboos_json"]),
        change_axis=row["change_axis"],
        arc_stage_notes=row["arc_stage_notes"],
        continuity_facts=_parse_json_list(row["continuity_facts_json"]),
        writer_notes=row["writer_notes"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _world_bible_row_to_record(row) -> WorldBibleEntryRecord:
    return WorldBibleEntryRecord(
        entry_id=int(row["entry_id"]),
        project_id=row["project_id"],
        entry_type=row["entry_type"],
        title=row["title"],
        summary=row["summary"],
        canonical_facts=_parse_json_list(row["canonical_facts_json"]),
        related_character_ids=_parse_json_list(row["related_character_ids_json"]),
        visibility_scope=row["visibility_scope"],
        source_artifacts=_parse_json_list(row["source_artifacts_json"]),
        continuity_warnings=_parse_json_list(row["continuity_warnings_json"]),
        writer_notes=row["writer_notes"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _research_item_row_to_record(row) -> ResearchItemRecord:
    return ResearchItemRecord(
        item_id=row["item_id"],
        project_id=row["project_id"],
        title=row["title"],
        content=row["content"],
        source_url=row["source_url"],
        source_type=row["source_type"],
        genre_tags=_parse_json_list(row["genre_tags_json"]),
        status=row["status"],
        citations=_parse_json_list(row["citations_json"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _storyboard_card_row_to_record(row) -> StoryboardCardRecord:
    return StoryboardCardRecord(
        card_id=row["card_id"],
        project_id=row["project_id"],
        title=row["title"],
        content=row["content"],
        card_type=row["card_type"],
        column_id=row["column_id"],
        position=int(row["position"]),
        tags=_parse_json_list(row["tags"]),
        character_ids=_parse_json_list(row["character_ids"]),
        dependencies=_parse_json_list(row["dependencies"]),
        metadata=_parse_json_object(row["metadata"]) or {},
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _brain_dump_session_row_to_record(row) -> BrainDumpSessionRecord:
    return BrainDumpSessionRecord(
        session_id=int(row["session_id"]),
        project_id=row["project_id"],
        title=row["title"],
        raw_text=row["raw_text"],
        state=row["state"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _polish_report_row_to_record(row) -> PolishReportRecord:
    return PolishReportRecord(
        report_id=row["report_id"],
        project_id=row["project_id"],
        document_id=row["document_id"],
        readability_score=float(row["readability_score"] or 0.0),
        word_count=int(row["word_count"]),
        sentence_count=int(row["sentence_count"]),
        avg_sentence_length=float(row["avg_sentence_length"] or 0.0),
        passive_voice_count=int(row["passive_voice_count"]),
        repetitive_words=_parse_json_list(row["repetitive_words_json"]),
        style_issues=_parse_json_list(row["style_issues_json"]),
        generated_at=datetime.fromisoformat(row["generated_at"]),
    )


def _export_status_row_to_record(row) -> ExportStatusRecord:
    return ExportStatusRecord(
        export_id=row["export_id"],
        project_id=row["project_id"],
        document_id=row["document_id"],
        format=row["format"],
        status=row["status"],
        artifact_path=row["artifact_path"],
        error_message=row["error_message"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _revision_checklist_item_row_to_record(row) -> RevisionChecklistItemRecord:
    return RevisionChecklistItemRecord(
        item_id=row["item_id"],
        label=row["label"],
        done=bool(row["done"]),
    )


def _revision_pass_row_to_record(row) -> RevisionPassRecord:
    raw = json.loads(row["checklist_json"] or "[]")
    checklist = [
        RevisionChecklistItemRecord(
            item_id=item["item_id"],
            label=item["label"],
            done=bool(item["done"]),
        )
        for item in raw
    ]
    return RevisionPassRecord(
        pass_id=row["pass_id"],
        project_id=row["project_id"],
        pass_type=row["pass_type"],
        status=row["status"],
        checklist=checklist,
        notes=row["notes"],
        created_at=datetime.fromisoformat(row["created_at"]),
        completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
    )


__all__ = [
    name
    for name, value in globals().items()
    if name.startswith("_")
    and callable(value)
    and getattr(value, "__module__", None) == __name__
]
