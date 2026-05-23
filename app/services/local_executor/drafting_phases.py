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
from ..runtime_prompts import build_p300_drafter_request, chapter_output_path
from .helpers import provider_backend_version as _provider_backend_version, utcnow as _utcnow, inject_scene_context

logger = logging.getLogger(__name__)



class _DraftingPhasesMixin:

    def _run_multi_chapter_draft(
        self,
        *,
        job_id: UUID,
        started_at: datetime,
        current_phase: str,
        attempt: dict[str, Any],
        request_payload: dict[str, object],
        project_id: str,
        chapter_ids: list[str],
    ) -> None:
        """Run sequential P-300 jobs for multiple chapters with prior context propagation.

        Each chapter is drafted, summarized, and the summary is injected into subsequent chapters.
        Prior chapters list is capped at last 3 to avoid prompt bloat.
        """
        from ..schemas.story_development import PriorChapterSummary

        project = self._project_service.get_project(project_id)
        payload = dict(request_payload.get("payload", {}))
        prior_chapters: list[PriorChapterSummary] = []
        completed_count = 0
        failed_chapters: list[str] = []

        _repo = StoryDevelopmentRepository(settings.operations_db_path)
        _chars = _repo.list_character_profiles(project_id)

        for idx, chapter_id in enumerate(chapter_ids):
            logger.info(
                "Drafting chapter %d/%d: %s",
                idx + 1,
                len(chapter_ids),
                chapter_id,
            )

            # Sanitize chapter_id
            safe_chapter_id = chapter_id
            try:
                safe_chapter_id = sanitize_filename(chapter_id)
            except ValidationError:
                logger.warning("Invalid chapter_id, skipping: %r", chapter_id)
                failed_chapters.append(chapter_id)
                continue

            # Get active characters for this chapter
            active_chars: list[str] | None = None
            if self._scene_context:
                try:
                    _repo_ctx = self._scene_context._repository
                    chapter_plan = _repo_ctx.get_chapter_plan(safe_chapter_id)
                    active_chars = chapter_plan.active_character_ids if chapter_plan else None
                except KeyError:
                    pass

            # Resolve upstream artifacts
            selected_inputs = self._resolve_runtime_artifact_inputs(
                job_id=job_id,
                attempt=attempt,
                project_id=project_id,
                step_name="drafter",
            )
            sequence_output = selected_inputs.get("sequence")
            architect_output = selected_inputs.get("architect_output")

            # Build inference request
            inference_request = build_p300_drafter_request(
                manifest=project.manifest,
                payload=payload,
                sequence_output=sequence_output,
                architect_output=architect_output,
                default_model=self._inferencer.descriptor.default_model,
                chapter_id=safe_chapter_id,
            )

            # Inject scene context with prior chapters
            if self._scene_context:
                try:
                    ctx = self._scene_context.assemble_context(
                        project_id=project_id,
                        active_character_ids=active_chars,
                        prior_chapters=prior_chapters if prior_chapters else None,
                    )
                    context_prompt = ctx.to_prompt_string()
                    if context_prompt:
                        inference_request = inject_scene_context(inference_request, context_prompt)
                except Exception as exc:
                    logger.warning("Context assembly failed for %s: %s", safe_chapter_id, exc)

            # Update job status
            self._job_manager.update_job(
                job_id,
                current_phase=current_phase,
                current_step=f"drafter-{safe_chapter_id}",
                detail=f"Drafting {safe_chapter_id}.",
            )

            # Run LLM
            try:
                inference_response = self._inferencer.generate_text(inference_request)
            except InferenceBackendError as exc:
                logger.error("Drafting failed for %s: %s", safe_chapter_id, exc)
                failed_chapters.append(safe_chapter_id)
                continue

            # Process output
            output_path = chapter_output_path(Path(project.project_dir), chapter_id=safe_chapter_id)
            output_text = inference_response.content.strip()
            if output_text:
                output_text += "\n"

            # Consistency critic check
            rewrite_needed = False
            critic_result = None
            if self._consistency_critic:
                try:
                    bios = {c.display_name: f"archetype: {c.archetype}; voice: {c.voice_notes}" for c in _chars if c.display_name}
                    critic_result = self._consistency_critic.check(output_text, bios)

                    if not critic_result.passed and critic_result.violations:
                        rewrite_needed = True
                        logger.info("Critic flagged %d violations, triggering rewrite", len(critic_result.violations))
                except Exception as exc:
                    logger.warning("Critic check failed for %s: %s", safe_chapter_id, exc)

            if rewrite_needed and critic_result:
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
                        logger.info("Rewrite applied for %s", safe_chapter_id)
                except Exception as exc:
                    logger.warning("Rewrite failed for %s, keeping original draft: %s", safe_chapter_id, exc)

            # Entity intake
            if self._entity_intake:
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
                    logger.warning("Entity intake failed for %s: %s", safe_chapter_id, exc)

            # Write chapter file and finalize
            staged_output_path = self._write_staged_output(output_path=output_path, output_text=output_text)
            normalized_finish_reason = inference_response.finish_reason or "completed"
            backend_version = _provider_backend_version(inference_response.raw_response)
            input_artifact_refs = ["manifest"]
            source_content_hashes = [stable_hash_payload(project.manifest.model_dump(mode="json"))]
            step_input_payload = {
                "job_request": request_payload,
                "manifest": project.manifest.model_dump(mode="json"),
                "chapter_id": safe_chapter_id,
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
            artifact_role = f"chapter_{safe_chapter_id}"

            self._finalize_generated_job_phase(
                job_id=job_id,
                current_phase=current_phase,
                attempt=attempt,
                project_id=project_id,
                step_name=f"drafter-{safe_chapter_id}",
                detail=f"Drafted {safe_chapter_id}.",
                model_id=inference_response.model or inference_request.model,
                backend_name=self._inferencer.descriptor.display_name,
                backend_version=backend_version,
                input_payload=step_input_payload,
                output_payload=step_output_payload,
                prompt_payload=inference_request.model_dump(mode="json"),
                input_artifact_refs=input_artifact_refs,
                output_artifact_refs=[artifact_role],
                started_at=started_at,
                finished_at=_utcnow(),
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

            # Auto-create DraftArtifact + ManuscriptDocument for this chapter
            try:
                from .drafting import DraftingService
                _drafting_service = DraftingService(repository=_repo)
                chapter_title = f"Chapter {safe_chapter_id}"
                try:
                    _cp = _repo.get_chapter_plan(safe_chapter_id)
                    chapter_title = _cp.title or chapter_title
                except KeyError:
                    pass

                draft_artifact_id = f"draft-{project_id}-ch{safe_chapter_id}"
                artifact = _drafting_service.register_draft_artifact(
                    project_id=project_id,
                    artifact_id=draft_artifact_id,
                    title=chapter_title,
                    content=output_text,
                    provenance_note=f"Generated by drafter phase (P-300)",
                    status="DRAFT",
                )

                _drafting_service.save_manuscript_document(
                    project_id=project_id,
                    document_id=f"ms-{project_id}-ch{safe_chapter_id}",
                    content=output_text,
                    title=chapter_title,
                    chapter_id=safe_chapter_id,
                    current_draft_artifact_id=artifact.artifact_id,
                )
            except Exception as exc:
                logger.warning("Draft/Manuscript creation failed for %s: %s", safe_chapter_id, exc)

            # Summarize chapter for prior context propagation
            if self._chapter_summarizer:
                try:
                    character_names = [c.display_name for c in _chars if c.display_name]
                    summary = self._chapter_summarizer.summarize(
                        chapter_id=safe_chapter_id,
                        chapter_text=output_text,
                        character_names=character_names,
                    )
                    if summary:
                        prior_chapters.append(summary)
                        if len(prior_chapters) > 3:
                            prior_chapters = prior_chapters[-3:]
                except Exception as exc:
                    logger.warning("Summarization failed for %s: %s", safe_chapter_id, exc)

            completed_count += 1

        # Final job status
        if completed_count == 0:
            self._job_manager.update_job(
                job_id,
                status="FAILED",
                current_phase=current_phase,
                detail=f"All {len(chapter_ids)} chapters failed.",
            )
        else:
            self._job_manager.update_job(
                job_id,
                status="COMPLETED",
                current_phase=current_phase,
                detail=f"Completed {completed_count}/{len(chapter_ids)} chapters.",
            )