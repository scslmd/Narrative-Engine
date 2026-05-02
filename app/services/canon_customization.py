from __future__ import annotations

from app.persistence.story_development import StoryDevelopmentRepository
from app.schemas.canon_customization import (
    CanonAnnotation,
    CanonAnnotationCreateRequest,
    CanonCustomizationProfile,
    CanonCustomizationProfileCreateRequest,
    CanonCustomizationProfileUpdateRequest,
)
from app.schemas.generation import CanonGenerationPacket, CanonPolicy, CanonScope, PromptBudgetSummary
from app.utils.db_inserts import hash_id


class CanonCustomizationService:
    def __init__(self, repository: StoryDevelopmentRepository) -> None:
        self.repository = repository

    def list_annotations(
        self,
        project_id: str,
        target_kind: str | None = None,
        target_id: str | None = None,
    ) -> list[CanonAnnotation]:
        return [
            CanonAnnotation.model_validate(
                {
                    "annotation_id": item.annotation_id,
                    "project_id": item.project_id,
                    "target_kind": item.target_kind,
                    "target_id": item.target_id,
                    "field_path": item.field_path,
                    "annotation_kind": item.annotation_kind,
                    "note": item.note,
                    "applies_to_modes": item.applies_to_modes,
                    "created_at": item.created_at.isoformat(),
                    "updated_at": item.updated_at.isoformat(),
                }
            )
            for item in self.repository.list_canon_annotations(project_id, target_kind, target_id)
        ]

    def save_annotation(self, payload: CanonAnnotationCreateRequest) -> CanonAnnotation:
        annotation_id = hash_id(
            "canon-annotation",
            f"{payload.project_id}:{payload.target_kind}:{payload.target_id}:{payload.field_path}:{payload.annotation_kind}",
        )
        record = self.repository.upsert_canon_annotation(
            annotation_id=annotation_id,
            project_id=payload.project_id,
            target_kind=str(payload.target_kind.value if hasattr(payload.target_kind, "value") else payload.target_kind),
            target_id=payload.target_id,
            field_path=payload.field_path,
            annotation_kind=str(payload.annotation_kind.value if hasattr(payload.annotation_kind, "value") else payload.annotation_kind),
            note=payload.note,
            applies_to_modes=payload.applies_to_modes,
        )
        return CanonAnnotation.model_validate(
            {
                "annotation_id": record.annotation_id,
                "project_id": record.project_id,
                "target_kind": record.target_kind,
                "target_id": record.target_id,
                "field_path": record.field_path,
                "annotation_kind": record.annotation_kind,
                "note": record.note,
                "applies_to_modes": record.applies_to_modes,
                "created_at": record.created_at.isoformat(),
                "updated_at": record.updated_at.isoformat(),
            }
        )

    def delete_annotation(self, project_id: str, annotation_id: str) -> None:
        record = self.repository.get_canon_annotation(annotation_id)
        if record.project_id != project_id:
            raise KeyError(annotation_id)
        self.repository.delete_canon_annotation(annotation_id)

    def create_profile(self, payload: CanonCustomizationProfileCreateRequest) -> CanonCustomizationProfile:
        profile_id = hash_id("canon-profile", f"{payload.project_id}:{payload.name}")
        return self._upsert_profile(profile_id, payload)

    def update_profile(
        self,
        profile_id: str,
        project_id: str,
        payload: CanonCustomizationProfileUpdateRequest,
    ) -> CanonCustomizationProfile:
        existing = self.repository.get_canon_customization_profile(profile_id)
        if existing.project_id != project_id:
            raise KeyError(profile_id)
        create_payload = CanonCustomizationProfileCreateRequest.model_validate(
            {
                "project_id": existing.project_id,
                "name": payload.name if payload.name is not None else existing.name,
                "description": payload.description if payload.description is not None else existing.description,
                "default_generation_mode": payload.default_generation_mode if payload.default_generation_mode is not None else existing.default_generation_mode,
                "canon_scope": payload.canon_scope if payload.canon_scope is not None else existing.canon_scope_json,
                "canon_policy": payload.canon_policy if payload.canon_policy is not None else existing.canon_policy_json,
                "generation_brief_template": payload.generation_brief_template if payload.generation_brief_template is not None else existing.generation_brief_template,
                "selected_annotation_ids": payload.selected_annotation_ids if payload.selected_annotation_ids is not None else existing.selected_annotation_ids,
                "status": payload.status if payload.status is not None else existing.status,
            }
        )
        return self._upsert_profile(profile_id, create_payload)

    def list_profiles(self, project_id: str) -> list[CanonCustomizationProfile]:
        return [self._profile_from_record(item) for item in self.repository.list_canon_customization_profiles(project_id)]

    def delete_profile(self, project_id: str, profile_id: str) -> None:
        item = self.repository.get_canon_customization_profile(profile_id)
        if item.project_id != project_id:
            raise KeyError(profile_id)
        self.repository.delete_canon_customization_profile(profile_id)

    def build_scope_from_profile(self, profile_id: str) -> CanonScope:
        item = self.repository.get_canon_customization_profile(profile_id)
        return CanonScope.model_validate(item.canon_scope_json)

    def build_policy_from_annotations(self, project_id: str, annotation_ids: list[str]) -> CanonPolicy:
        annotations = self.repository.list_canon_annotations(project_id)
        selected = [a for a in annotations if a.annotation_id in set(annotation_ids)]
        policy = CanonPolicy()
        locked = [f"{item.target_kind}.{item.field_path}" for item in selected if item.annotation_kind == "locked"]
        mutable = [f"{item.target_kind}.{item.field_path}" for item in selected if item.annotation_kind == "mutable"]
        forbidden = [item.note or f"{item.target_kind}:{item.target_id}:{item.field_path}" for item in selected if item.annotation_kind == "forbidden_contradiction"]
        policy.locked_character_fields = sorted(set(policy.locked_character_fields + [v for v in locked if v.startswith("character.")]))
        policy.locked_world_fields = sorted(set(policy.locked_world_fields + [v for v in locked if v.startswith("world_bible.")]))
        policy.allowed_character_changes = sorted(set(policy.allowed_character_changes + [v for v in mutable if v.startswith("character.")]))
        policy.allowed_world_changes = sorted(set(policy.allowed_world_changes + [v for v in mutable if v.startswith("world_bible.")]))
        policy.forbidden_contradictions = sorted(set(policy.forbidden_contradictions + forbidden))
        return policy

    def preview_packet(self, project_id: str, profile_id: str) -> CanonGenerationPacket:
        profile = self.repository.get_canon_customization_profile(profile_id)
        if profile.project_id != project_id:
            raise KeyError(profile_id)
        scope = CanonScope.model_validate(profile.canon_scope_json)
        policy = CanonPolicy.model_validate(profile.canon_policy_json)
        packet_id = hash_id("canon-packet-preview", f"{project_id}:{profile_id}")
        return CanonGenerationPacket(
            packet_id=packet_id,
            source_project_id=project_id,
            target_project_id=project_id,
            mode=profile.default_generation_mode,
            generation_brief=profile.generation_brief_template or "Generate canon-consistent output.",
            foundation_snapshot={},
            characters=[],
            relationships=[],
            world_bible=[],
            arcs=[],
            continuity_threads=[],
            continuity_findings=[],
            drafting_context_packets=[],
            mythos_entries=[entry.__dict__ for entry in self.repository.list_mythos_entries(project_id)],
            pattern_entries=[entry.__dict__ for entry in self.repository.list_pattern_entries(project_id)],
            canon_annotations=[entry.__dict__ for entry in self.repository.list_canon_annotations(project_id)],
            customization_profile_id=profile_id,
            canon_policy=policy,
            prompt_budget_summary=PromptBudgetSummary(
                estimated_prompt_chars=0,
                target_max_chars=0,
                truncated_fields=[],
                fit_to_budget=True,
            ),
            source_hashes={"profile_id": profile_id, "scope_hash": hash_id("scope", str(scope.model_dump(mode="json")))},
        )

    def _upsert_profile(
        self,
        profile_id: str,
        payload: CanonCustomizationProfileCreateRequest,
    ) -> CanonCustomizationProfile:
        record = self.repository.upsert_canon_customization_profile(
            profile_id=profile_id,
            project_id=payload.project_id,
            name=payload.name,
            description=payload.description,
            default_generation_mode=payload.default_generation_mode,
            canon_scope_json=payload.canon_scope.model_dump(mode="json"),
            canon_policy_json=payload.canon_policy.model_dump(mode="json"),
            generation_brief_template=payload.generation_brief_template,
            selected_annotation_ids=payload.selected_annotation_ids,
            status=str(payload.status.value if hasattr(payload.status, "value") else payload.status),
        )
        return self._profile_from_record(record)

    def _profile_from_record(self, item) -> CanonCustomizationProfile:
        return CanonCustomizationProfile.model_validate(
            {
                "profile_id": item.profile_id,
                "project_id": item.project_id,
                "name": item.name,
                "description": item.description,
                "default_generation_mode": item.default_generation_mode,
                "canon_scope": item.canon_scope_json,
                "canon_policy": item.canon_policy_json,
                "generation_brief_template": item.generation_brief_template,
                "selected_annotation_ids": item.selected_annotation_ids,
                "status": item.status,
            }
        )
