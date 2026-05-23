from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from ...inference import InferenceBackendError
from ...persistence.story_development import StoryDevelopmentRepository
from ...persistence.steps import stable_hash_payload, stable_hash_text
from ...schemas.inference import InferenceMessage, InferenceRequest
from ...settings import settings
from ...utils.input_validation import ValidationError, sanitize_filename
from ..runtime_prompts import (
    build_p100_architect_request,
    build_p200_sequencer_request,
    build_p300_drafter_request,
    build_p400_compiler_request,
    architect_output_path,
    chapter_output_path,
    sequence_output_path,
    story_bible_output_path,
)
from .helpers import (
    normalized_p100_job_request as _normalized_p100_job_request,
    provider_backend_version as _provider_backend_version,
    utcnow as _utcnow,
    inject_scene_context,
)

logger = logging.getLogger(__name__)



class _PlanningPhasesMixin:

    def _run_architect_phase(
        self,
        *,
        job_id: UUID,
        started_at: datetime,
        current_phase: str,
        attempt: dict[str, Any],
        request_payload: dict[str, object],
        project_id: str | None,
    ) -> None:
        if not project_id:
            raise ValueError("P-100 requires payload.project_id.")
        try:
            project = self._project_service.get_project(project_id)
        except FileNotFoundError:
            self._project_service.reconcile_projects()
            project = self._project_service.get_project(project_id)
        payload = dict(request_payload.get("payload", {}))
        job_request = _normalized_p100_job_request(request_payload)
        inference_request = build_p100_architect_request(
            manifest=project.manifest,
            payload=payload,
            default_model=self._inferencer.descriptor.default_model,
        )
        self._job_manager.update_job(
            job_id,
            current_phase=current_phase,
            current_step="architect",
            detail="Architect inference running.",
        )
        try:
            inference_response = self._inferencer.generate_text(inference_request)
        except InferenceBackendError as exc:
            self._job_manager.update_job(
                job_id,
                status="FAILED",
                current_phase=current_phase,
                current_step="architect",
                error=exc.code,
                error_category=exc.category,
                detail=str(exc),
                finish_reason=exc.finish_reason,
                failure_stage="inference",
                retryable=exc.retryable,
            )
            self._step_records.create_step_record(
                logical_run_id=str(attempt["logical_run_id"]),
                run_id=job_id,
                run_kind="pipeline_job",
                attempt_number=int(attempt["attempt_number"]),
                step_name="architect",
                step_index=1,
                state="FAILED",
                project_id=project_id,
                model_id=inference_request.model,
                critic_profile=None,
                backend_name=self._inferencer.descriptor.display_name,
                backend_version=None,
                input_hash=stable_hash_payload({
                    "job_request": job_request,
                    "manifest": project.manifest.model_dump(mode="json"),
                }),
                output_hash=None,
                prompt_hash=stable_hash_payload(inference_request.model_dump(mode="json")),
                input_artifact_refs=["manifest"],
                output_artifact_refs=[],
                started_at=started_at,
                finished_at=_utcnow(),
                finish_reason=exc.finish_reason,
                error_code=exc.code,
                error_category=exc.category,
                executor_id="job-worker-local",
                lease_owner=str(attempt.get("lease_owner") or "job-worker-local"),
            )
            return
        output_path = architect_output_path(Path(project.project_dir))
        output_text = inference_response.content.strip()
        if output_text:
            output_text += "\n"
        staged_output_path = self._write_staged_output(output_path=output_path, output_text=output_text)
        normalized_finish_reason = inference_response.finish_reason or "completed"
        backend_version = _provider_backend_version(inference_response.raw_response)
        step_input_payload = {
            "job_request": job_request,
            "manifest": project.manifest.model_dump(mode="json"),
        }
        step_output_payload = {
            "backend": inference_response.backend,
            "model": inference_response.model or inference_request.model,
            "content": output_text,
            "finish_reason": normalized_finish_reason,
            "usage": inference_response.usage.model_dump(mode="json"),
            "artifact_path": str(output_path),
        }
        finished_at = _utcnow()
        self._finalize_generated_job_phase(
            job_id=job_id,
            current_phase=current_phase,
            attempt=attempt,
            project_id=project_id,
            step_name="architect",
            detail="Architect phase finished.",
            model_id=inference_response.model or inference_request.model,
            backend_name=self._inferencer.descriptor.display_name,
            backend_version=backend_version,
            input_payload=step_input_payload,
            output_payload=step_output_payload,
            prompt_payload=inference_request.model_dump(mode="json"),
            input_artifact_refs=["manifest"],
            output_artifact_refs=["architect_output"],
            started_at=started_at,
            finished_at=finished_at,
            finish_reason=normalized_finish_reason,
            prompt_tokens=inference_response.usage.prompt_tokens,
            completion_tokens=inference_response.usage.completion_tokens,
            total_tokens=inference_response.usage.total_tokens,
            artifact_role="architect_output",
            artifact_kind="markdown",
            output_path=output_path,
            staged_output_path=staged_output_path,
            content_hash_source=output_text,
            source_content_hashes=[stable_hash_payload(project.manifest.model_dump(mode="json"))],
            project_artifact_name="architect_p100",
        )
    def _run_sequencer_phase(
        self,
        *,
        job_id: UUID,
        started_at: datetime,
        current_phase: str,
        attempt: dict[str, Any],
        request_payload: dict[str, object],
        project_id: str | None,
    ) -> None:
        if not project_id:
            raise ValueError("P-200 requires payload.project_id.")
        project = self._project_service.get_project(project_id)
        payload = dict(request_payload.get("payload", {}))
        selected_inputs = self._resolve_runtime_artifact_inputs(
            job_id=job_id,
            attempt=attempt,
            project_id=project_id,
            step_name="sequencer",
        )
        architect_output = selected_inputs.get("architect_output")
        inference_request = build_p200_sequencer_request(
            manifest=project.manifest,
            payload=payload,
            architect_output=architect_output,
            default_model=self._inferencer.descriptor.default_model,
        )
        self._job_manager.update_job(
            job_id,
            current_phase=current_phase,
            current_step="sequencer",
            detail="Sequencer inference running.",
        )
        try:
            inference_response = self._inferencer.generate_text(inference_request)
        except InferenceBackendError as exc:
            self._job_manager.update_job(
                job_id,
                status="FAILED",
                current_phase=current_phase,
                current_step="sequencer",
                error=exc.code,
                error_category=exc.category,
                detail=str(exc),
                finish_reason=exc.finish_reason,
                failure_stage="inference",
                retryable=exc.retryable,
            )
            step_input_payload = {
                "job_request": request_payload,
                "manifest": project.manifest.model_dump(mode="json"),
            }
            if architect_output is not None:
                step_input_payload["architect_output"] = architect_output
            self._step_records.create_step_record(
                logical_run_id=str(attempt["logical_run_id"]),
                run_id=job_id,
                run_kind="pipeline_job",
                attempt_number=int(attempt["attempt_number"]),
                step_name="sequencer",
                step_index=1,
                state="FAILED",
                project_id=project_id,
                model_id=inference_request.model,
                critic_profile=None,
                backend_name=self._inferencer.descriptor.display_name,
                backend_version=None,
                input_hash=stable_hash_payload(step_input_payload) if step_input_payload else None,
                output_hash=None,
                prompt_hash=stable_hash_payload(inference_request.model_dump(mode="json")),
                input_artifact_refs=["manifest"] + (["architect_output"] if architect_output is not None else []),
                output_artifact_refs=[],
                started_at=started_at,
                finished_at=_utcnow(),
                finish_reason=exc.finish_reason,
                error_code=exc.code,
                error_category=exc.category,
                executor_id="job-worker-local",
                lease_owner=str(attempt.get("lease_owner") or "job-worker-local"),
            )
            return
        output_path = sequence_output_path(Path(project.project_dir))
        output_text = inference_response.content.strip()
        if output_text:
            output_text += "\n"
        staged_output_path = self._write_staged_output(output_path=output_path, output_text=output_text)
        normalized_finish_reason = inference_response.finish_reason or "completed"
        backend_version = _provider_backend_version(inference_response.raw_response)
        input_artifact_refs = ["manifest"]
        source_content_hashes = [stable_hash_payload(project.manifest.model_dump(mode="json"))]
        step_input_payload = {
            "job_request": request_payload,
            "manifest": project.manifest.model_dump(mode="json"),
        }
        if selected_inputs:
            step_input_payload["selected_input_artifacts"] = {
                key: stable_hash_text(value) for key, value in selected_inputs.items()
            }
        if architect_output is not None:
            input_artifact_refs.append("architect_output")
            source_content_hashes.append(stable_hash_payload(architect_output))
            step_input_payload["architect_output"] = architect_output
        step_output_payload = {
            "backend": inference_response.backend,
            "model": inference_response.model or inference_request.model,
            "content": output_text,
            "finish_reason": normalized_finish_reason,
            "usage": inference_response.usage.model_dump(mode="json"),
            "artifact_path": str(output_path),
        }
        finished_at = _utcnow()
        self._finalize_generated_job_phase(
            job_id=job_id,
            current_phase=current_phase,
            attempt=attempt,
            project_id=project_id,
            step_name="sequencer",
            detail="Sequencer phase finished.",
            model_id=inference_response.model or inference_request.model,
            backend_name=self._inferencer.descriptor.display_name,
            backend_version=backend_version,
            input_payload=step_input_payload,
            output_payload=step_output_payload,
            prompt_payload=inference_request.model_dump(mode="json"),
            input_artifact_refs=input_artifact_refs,
            output_artifact_refs=["sequence"],
            started_at=started_at,
            finished_at=finished_at,
            finish_reason=normalized_finish_reason,
            prompt_tokens=inference_response.usage.prompt_tokens,
            completion_tokens=inference_response.usage.completion_tokens,
            total_tokens=inference_response.usage.total_tokens,
            artifact_role="sequence",
            artifact_kind="json",
            output_path=output_path,
            staged_output_path=staged_output_path,
            content_hash_source=output_text,
            source_content_hashes=source_content_hashes,
            project_artifact_name="sequence",
        )
    def _run_drafter_phase(
        self,
        *,
        job_id: UUID,
        started_at: datetime,
        current_phase: str,
        attempt: dict[str, Any],
        request_payload: dict[str, object],
        project_id: str | None,
    ) -> None:
        if not project_id:
            raise ValueError("P-300 requires payload.project_id.")
        project = self._project_service.get_project(project_id)
        payload = dict(request_payload.get("payload", {}))
        chapter_id = str(payload.get("chapter_id") or "").strip() or None
        if chapter_id:
            try:
                chapter_id = sanitize_filename(chapter_id)
            except ValidationError:
                logger.warning("Invalid chapter_id, falling back to default output path: %r", chapter_id)
                chapter_id = None
        # Check for multi-chapter mode
        chapter_ids_list = payload.get("chapter_ids")
        if isinstance(chapter_ids_list, list) and chapter_ids_list:
            self._run_multi_chapter_draft(
                job_id=job_id,
                started_at=started_at,
                current_phase=current_phase,
                attempt=attempt,
                request_payload=request_payload,
                project_id=project_id,
                chapter_ids=[str(cid) for cid in chapter_ids_list],
            )
            return
        selected_inputs = self._resolve_runtime_artifact_inputs(
            job_id=job_id,
            attempt=attempt,
            project_id=project_id,
            step_name="drafter",
        )
        sequence_output = selected_inputs.get("sequence")
        architect_output = selected_inputs.get("architect_output")
        inference_request = build_p300_drafter_request(
            manifest=project.manifest,
            payload=payload,
            sequence_output=sequence_output,
            architect_output=architect_output,
            default_model=self._inferencer.descriptor.default_model,
            chapter_id=chapter_id,
        )
        # Context injection: assemble character anchors and world constraints
        if self._scene_context:
            try:
              # Try to get active_character_ids from the chapter plan
                active_chars: list[str] | None = None
                if chapter_id:
                    try:
                        _repo = self._scene_context._repository
                        chapter_plan = _repo.get_chapter_plan(chapter_id)
                        active_chars = chapter_plan.active_character_ids if chapter_plan else None
                    except KeyError:
                        pass  # No chapter plan found, use all characters

                ctx = self._scene_context.assemble_context(
                    project_id=project_id,
                    active_character_ids=active_chars,
                    prior_chapters=None,  # Will be populated by orchestrator
                )
                context_prompt = ctx.to_prompt_string()
                if context_prompt:
                    inference_request = inject_scene_context(inference_request, context_prompt)
            except Exception as exc:
                logger.warning("Context assembly failed, proceeding without: %s", exc)
        self._job_manager.update_job(
            job_id,
            current_phase=current_phase,
            current_step="drafter",
            detail="Drafter inference running.",
        )
        try:
            inference_response = self._inferencer.generate_text(inference_request)
        except InferenceBackendError as exc:
            self._job_manager.update_job(
                job_id,
                status="FAILED",
                current_phase=current_phase,
                current_step="drafter",
                error=exc.code,
                error_category=exc.category,
                detail=str(exc),
                finish_reason=exc.finish_reason,
                failure_stage="inference",
                retryable=exc.retryable,
            )
            step_input_payload = {
                "job_request": request_payload,
                "manifest": project.manifest.model_dump(mode="json"),
            }
            input_artifact_refs = ["manifest"]
            if sequence_output is not None:
                step_input_payload["sequence"] = sequence_output
                input_artifact_refs.append("sequence")
            if architect_output is not None:
                step_input_payload["architect_output"] = architect_output
                input_artifact_refs.append("architect_output")
            self._step_records.create_step_record(
                logical_run_id=str(attempt["logical_run_id"]),
                run_id=job_id,
                run_kind="pipeline_job",
                attempt_number=int(attempt["attempt_number"]),
                step_name="drafter",
                step_index=1,
                state="FAILED",
                project_id=project_id,
                model_id=inference_request.model,
                critic_profile=None,
                backend_name=self._inferencer.descriptor.display_name,
                backend_version=None,
                input_hash=stable_hash_payload(step_input_payload) if step_input_payload else None,
                output_hash=None,
                prompt_hash=stable_hash_payload(inference_request.model_dump(mode="json")),
                input_artifact_refs=input_artifact_refs,
                output_artifact_refs=[],
                started_at=started_at,
                finished_at=_utcnow(),
                finish_reason=exc.finish_reason,
                error_code=exc.code,
                error_category=exc.category,
                executor_id="job-worker-local",
                lease_owner=str(attempt.get("lease_owner") or "job-worker-local"),
            )
            return
        output_path = chapter_output_path(Path(project.project_dir), chapter_id=chapter_id)
        output_text = inference_response.content.strip()
        if output_text:
            output_text += "\n"

        # Shared repository for critic check and entity intake
        _repo = StoryDevelopmentRepository(settings.operations_db_path) if project_id else None
        _chars = _repo.list_character_profiles(project_id) if _repo else []

        # Consistency critic check
        rewrite_needed = False
        critic_result = None
        if self._consistency_critic and project_id:
            try:
                bios = {c.display_name: f"archetype: {c.archetype}; voice: {c.voice_notes}" for c in _chars if c.display_name}
                critic_result = self._consistency_critic.check(output_text, bios)

                if not critic_result.passed and critic_result.violations:
                    rewrite_needed = True
                    logger.info("Critic flagged %d violations, triggering rewrite", len(critic_result.violations))
            except Exception as exc:
                logger.warning("Critic check failed, proceeding with draft: %s", exc)

        if rewrite_needed and critic_result:
            # Build rewrite prompt and execute single retry
            try:
                violation_lines = []
                for v in critic_result.violations[:3]:
                    if v.line_start is not None and v.quote is not None:
                        violation_lines.append(
                            f"- {v.character} (lines {v.line_start}-{v.line_end}): {v.issue}\n"
                            f'  Quote: "{v.quote}"\n'
                            f"  Fix: {v.suggestion}"
                        )
                    else:
                        violation_lines.append(f"- {v.character}: {v.issue} -> {v.suggestion}")
                violation_summary = "\n".join(violation_lines)
                rewrite_prompt = f"The following issues were found in the draft:\n{violation_summary}\n\nPlease rewrite the problematic passages while preserving the overall story flow."
                rewrite_request = InferenceRequest(
                    model=inference_request.model,
                    temperature=0.1,
                    max_tokens=inference_request.max_tokens,
                    messages=[
                        InferenceMessage(role="system", content="You are a narrative editor. Rewrite only the flagged passages to fix consistency issues while preserving story flow."),
                        InferenceMessage(role="user", content=f"Original draft:\n{output_text}\n\n{rewrite_prompt}"),
                    ],
                )
                rewrite_response = self._inferencer.generate_text(rewrite_request)
                rewritten = rewrite_response.content.strip()
                if rewritten:
                    output_text = rewritten + "\n"
                    logger.info("Rewrite applied")
            except Exception as exc:
                logger.warning("Rewrite failed, keeping original draft: %s", exc)

        # Entity intake: detect and persist new characters in the draft
        if self._entity_intake and project_id:
            try:
                known = {c.display_name: c.character_id for c in _chars if c.display_name}
                new_entities = self._entity_intake.intake_new_entities(output_text, known)
                for entity in new_entities:
                    entity_id = f"auto-{entity.name.lower().replace(' ', '-')}"
                    _repo.upsert_character_profile(
                        project_id=project_id,
                        character_id=entity_id,
                        display_name=entity.name,
                        role_in_story="supporting",
                        archetype=entity.inferred_archetype or "unknown",
                        external_goal=entity.inferred_goal or "",
                        internal_need="",
                        core_fear="",
                        writer_notes=f"Auto-detected from draft: {entity.raw_evidence[:200]}",
                    )
                if new_entities:
                    logger.info("Detected and persisted %d new entities in draft", len(new_entities))
            except Exception as exc:
                logger.warning("Entity intake failed: %s", exc)

        staged_output_path = self._write_staged_output(output_path=output_path, output_text=output_text)
        normalized_finish_reason = inference_response.finish_reason or "completed"
        backend_version = _provider_backend_version(inference_response.raw_response)
        input_artifact_refs = ["manifest"]
        source_content_hashes = [stable_hash_payload(project.manifest.model_dump(mode="json"))]
        step_input_payload = {
            "job_request": request_payload,
            "manifest": project.manifest.model_dump(mode="json"),
        }
        if selected_inputs:
            step_input_payload["selected_input_artifacts"] = {
                key: stable_hash_text(value) for key, value in selected_inputs.items()
            }
        if sequence_output is not None:
            input_artifact_refs.append("sequence")
            source_content_hashes.append(stable_hash_payload(sequence_output))
            step_input_payload["sequence"] = sequence_output
        if architect_output is not None:
            input_artifact_refs.append("architect_output")
            source_content_hashes.append(stable_hash_payload(architect_output))
            step_input_payload["architect_output"] = architect_output
        step_output_payload = {
            "backend": inference_response.backend,
            "model": inference_response.model or inference_request.model,
            "content": output_text,
            "finish_reason": normalized_finish_reason,
            "usage": inference_response.usage.model_dump(mode="json"),
            "artifact_path": str(output_path),
        }
        artifact_role = f"chapter_{chapter_id}" if chapter_id else "chapter_1"
        finished_at = _utcnow()
        self._finalize_generated_job_phase(
            job_id=job_id,
            current_phase=current_phase,
            attempt=attempt,
            project_id=project_id,
            step_name="drafter",
            detail="Drafter phase finished.",
            model_id=inference_response.model or inference_request.model,
            backend_name=self._inferencer.descriptor.display_name,
            backend_version=backend_version,
            input_payload=step_input_payload,
            output_payload=step_output_payload,
            prompt_payload=inference_request.model_dump(mode="json"),
            input_artifact_refs=input_artifact_refs,
            output_artifact_refs=[artifact_role],
            started_at=started_at,
            finished_at=finished_at,
            finish_reason=normalized_finish_reason,
            prompt_tokens=inference_response.usage.prompt_tokens,
            completion_tokens=inference_response.usage.completion_tokens,
            total_tokens=inference_response.usage.total_tokens,
            artifact_role=artifact_role,
            artifact_kind="markdown",
            output_path=output_path,
            staged_output_path=staged_output_path,
            content_hash_source=output_text,
            source_content_hashes=source_content_hashes,
            project_artifact_name=artifact_role,
        )

        # Auto-create DraftArtifact + ManuscriptDocument for single-chapter draft
        try:
            effective_chapter_id = chapter_id or "1"
            from .drafting import DraftingService
            _ms_drafting = DraftingService(repository=_repo)
            chapter_title = f"Chapter {effective_chapter_id}"
            linked_chapter_id = None
            if _repo and chapter_id:
                try:
                    _cp = _repo.get_chapter_plan(chapter_id)
                    chapter_title = _cp.title or chapter_title
                    linked_chapter_id = chapter_id
                except KeyError:
                    pass

            draft_artifact_id = f"draft-{project_id}-ch{effective_chapter_id}"
            artifact = _ms_drafting.register_draft_artifact(
                project_id=project_id,
                artifact_id=draft_artifact_id,
                title=chapter_title,
                content=output_text,
                provenance_note=f"Generated by drafter phase (P-300)",
                status="DRAFT",
            )

            _ms_drafting.save_manuscript_document(
                project_id=project_id,
                document_id=f"ms-{project_id}-ch{effective_chapter_id}",
                content=output_text,
                title=chapter_title,
                chapter_id=linked_chapter_id,
                current_draft_artifact_id=artifact.artifact_id,
            )
        except Exception as exc:
            logger.warning("Draft/Manuscript creation failed for single-chapter draft: %s", exc)
    def _run_compiler_phase(
        self,
        *,
        job_id: UUID,
        started_at: datetime,
        current_phase: str,
        attempt: dict[str, Any],
        request_payload: dict[str, object],
        project_id: str | None,
    ) -> None:
        if not project_id:
            raise ValueError("P-400 requires payload.project_id.")
        project = self._project_service.get_project(project_id)
        payload = dict(request_payload.get("payload", {}))
        selected_inputs = self._resolve_runtime_artifact_inputs(
            job_id=job_id,
            attempt=attempt,
            project_id=project_id,
            step_name="compiler",
        )
        architect_output = selected_inputs.get("architect_output")
        sequence_output = selected_inputs.get("sequence")
        chapter_output = selected_inputs.get("chapter_1")
        inference_request = build_p400_compiler_request(
            manifest=project.manifest,
            payload=payload,
            architect_output=architect_output,
            sequence_output=sequence_output,
            chapter_output=chapter_output,
            default_model=self._inferencer.descriptor.default_model,
        )
        self._job_manager.update_job(
            job_id,
            current_phase=current_phase,
            current_step="compiler",
            detail="Compiler inference running.",
        )
        try:
            inference_response = self._inferencer.generate_text(inference_request)
        except InferenceBackendError as exc:
            self._job_manager.update_job(
                job_id,
                status="FAILED",
                current_phase=current_phase,
                current_step="compiler",
                error=exc.code,
                error_category=exc.category,
                detail=str(exc),
                finish_reason=exc.finish_reason,
                failure_stage="inference",
                retryable=exc.retryable,
            )
            step_input_payload = {
                "job_request": request_payload,
                "manifest": project.manifest.model_dump(mode="json"),
            }
            input_artifact_refs = ["manifest"]
            if architect_output is not None:
                step_input_payload["architect_output"] = architect_output
                input_artifact_refs.append("architect_output")
            if sequence_output is not None:
                step_input_payload["sequence"] = sequence_output
                input_artifact_refs.append("sequence")
            if chapter_output is not None:
                step_input_payload["chapter_1"] = chapter_output
                input_artifact_refs.append("chapter_1")
            self._step_records.create_step_record(
                logical_run_id=str(attempt["logical_run_id"]),
                run_id=job_id,
                run_kind="pipeline_job",
                attempt_number=int(attempt["attempt_number"]),
                step_name="compiler",
                step_index=1,
                state="FAILED",
                project_id=project_id,
                model_id=inference_request.model,
                critic_profile=None,
                backend_name=self._inferencer.descriptor.display_name,
                backend_version=None,
                input_hash=stable_hash_payload(step_input_payload) if step_input_payload else None,
                output_hash=None,
                prompt_hash=stable_hash_payload(inference_request.model_dump(mode="json")),
                input_artifact_refs=input_artifact_refs,
                output_artifact_refs=[],
                started_at=started_at,
                finished_at=_utcnow(),
                finish_reason=exc.finish_reason,
                error_code=exc.code,
                error_category=exc.category,
                executor_id="job-worker-local",
                lease_owner=str(attempt.get("lease_owner") or "job-worker-local"),
            )
            return
        output_path = story_bible_output_path(Path(project.project_dir))
        output_text = inference_response.content.strip()
        if output_text:
            output_text += "\n"
        staged_output_path = self._write_staged_output(output_path=output_path, output_text=output_text)
        normalized_finish_reason = inference_response.finish_reason or "completed"
        backend_version = _provider_backend_version(inference_response.raw_response)
        input_artifact_refs = ["manifest"]
        source_content_hashes = [stable_hash_payload(project.manifest.model_dump(mode="json"))]
        step_input_payload = {
            "job_request": request_payload,
            "manifest": project.manifest.model_dump(mode="json"),
        }
        if selected_inputs:
            step_input_payload["selected_input_artifacts"] = {
                key: stable_hash_text(value) for key, value in selected_inputs.items()
            }
        if architect_output is not None:
            input_artifact_refs.append("architect_output")
            source_content_hashes.append(stable_hash_payload(architect_output))
            step_input_payload["architect_output"] = architect_output
        if sequence_output is not None:
            input_artifact_refs.append("sequence")
            source_content_hashes.append(stable_hash_payload(sequence_output))
            step_input_payload["sequence"] = sequence_output
        if chapter_output is not None:
            input_artifact_refs.append("chapter_1")
            source_content_hashes.append(stable_hash_payload(chapter_output))
            step_input_payload["chapter_1"] = chapter_output
        step_output_payload = {
            "backend": inference_response.backend,
            "model": inference_response.model or inference_request.model,
            "content": output_text,
            "finish_reason": normalized_finish_reason,
            "usage": inference_response.usage.model_dump(mode="json"),
            "artifact_path": str(output_path),
        }
        finished_at = _utcnow()
        self._finalize_generated_job_phase(
            job_id=job_id,
            current_phase=current_phase,
            attempt=attempt,
            project_id=project_id,
            step_name="compiler",
            detail="Compiler phase finished.",
            model_id=inference_response.model or inference_request.model,
            backend_name=self._inferencer.descriptor.display_name,
            backend_version=backend_version,
            input_payload=step_input_payload,
            output_payload=step_output_payload,
            prompt_payload=inference_request.model_dump(mode="json"),
            input_artifact_refs=input_artifact_refs,
            output_artifact_refs=["story_bible"],
            started_at=started_at,
            finished_at=finished_at,
            finish_reason=normalized_finish_reason,
            prompt_tokens=inference_response.usage.prompt_tokens,
            completion_tokens=inference_response.usage.completion_tokens,
            total_tokens=inference_response.usage.total_tokens,
            artifact_role="story_bible",
            artifact_kind="json",
            output_path=output_path,
            staged_output_path=staged_output_path,
            content_hash_source=output_text,
            source_content_hashes=source_content_hashes,
            project_artifact_name="story_bible",
        )