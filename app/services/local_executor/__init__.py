from __future__ import annotations

import logging
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Event, Thread
from time import sleep
from typing import Any
from uuid import UUID

from ...inference import InferenceBackend, InferenceBackendError, StubInferenceBackend
from ...persistence.story_development import StoryDevelopmentRepository
from ...persistence.steps import stable_hash_payload, stable_hash_text
from ...schemas.inference import InferenceMessage, InferenceRequest
from ...schemas.role_model_checker import RoleModelCheckStartRequest
from ...services.file_permissions import FilePermissionValidator
from ...settings import settings
from ...utils.input_validation import ValidationError, sanitize_filename
from ..job_manager import JobManager
from ..projects import ProjectService
from ..role_model_check_manager import RoleModelCheckManager
from ..role_model_checker import RoleModelCheckerService
from ..runtime_prompts import (
    build_m500_draft_generation_request,
    build_m500_manuscript_assist_request,
    build_m550_manuscript_repair_request,
    build_g200_story_generation_plan_request,
    build_g300_chapter_generation_request,
    build_g350_canon_repair_request,
    build_g400_manuscript_assembly_request,
    architect_output_path,
    build_p400_compiler_request,
    build_p300_drafter_request,
    build_p100_architect_request,
    build_p200_sequencer_request,
    chapter_output_path,
    sequence_output_path,
    story_bible_output_path,
)
from ..generation_gates import GenerationGateService
from ..step_records import StepRecordService
from ..scene_context import SceneContextService
from ..consistency_critic import ConsistencyCriticService
from ..entity_intake import EntityIntakeService
from ..chapter_summarizer import ChapterSummarizerService
from ..manuscript_assist_gates import ManuscriptAssistGateService
from .helpers import (
    checker_runtime_response as _checker_runtime_response,
    normalized_p100_job_request as _normalized_p100_job_request,
    phase_step_name as _phase_step_name,
    provider_backend_version as _provider_backend_version,
    require_supported_job_phase as _require_supported_job_phase,
    upstream_artifact_sources as _upstream_artifact_sources,
    utcnow as _utcnow,
    find_user_message_index,
    inject_scene_context,
)
from .worker_lifecycle import _WorkerLifecycleMixin
from .artifact_io import _ArtifactIOMixin
from .phase_protocol import _PhaseProtocolMixin
from .planning_phases import _PlanningPhasesMixin
from .drafting_phases import _DraftingPhasesMixin
from .generation_phases import _GenerationPhasesMixin
from .manuscript_assist_phases import _ManuscriptAssistPhasesMixin
from .checker_runtime import _CheckerRuntimeMixin

logger = logging.getLogger(__name__)


class LocalExecutor(
    _WorkerLifecycleMixin,
    _ArtifactIOMixin,
    _PhaseProtocolMixin,
    _PlanningPhasesMixin,
    _DraftingPhasesMixin,
    _GenerationPhasesMixin,
    _ManuscriptAssistPhasesMixin,
    _CheckerRuntimeMixin,
):
    pass
