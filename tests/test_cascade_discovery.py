from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from app.inference.base import InferenceBackend
from app.persistence.sqlite import connect as connect_sqlite
from app.schemas.inference import InferenceProviderDescriptor, InferenceRequest, InferenceResponse
from app.services.cascade_discovery import CascadeDiscoveryService
from app.services.discovery_jobs import CascadeJobManager


class JSONStubInferenceBackend(InferenceBackend):
    """Stub that returns valid JSON for cascade extraction."""

    def __init__(self, response_body: dict | None = None) -> None:
        self._response = response_body or {
            "characters": [
                {
                    "display_name": "Test Character",
                    "aliases": [],
                    "role_in_story": "protagonist",
                    "archetype": "",
                    "external_goal": "",
                    "internal_need": "",
                    "misbelief_or_wound": "",
                    "core_fear": "",
                    "primary_strength": "",
                    "fatal_flaw_or_limitation": "",
                    "backstory_summary": "",
                    "voice_notes": "",
                    "secrets": [],
                    "values": [],
                    "taboos": [],
                    "description": "",
                    "confidence": 0.8,
                }
            ],
            "relationships": [
                {
                    "source_character_name": "Test Character",
                    "target_character_name": "Other Character",
                    "relation_kind": "friendship",
                    "summary": "They are friends.",
                    "tension": None,
                    "directionality": "directed",
                    "confidence": 0.7,
                }
            ],
            "world_entries": [
                {
                    "entry_type": "location",
                    "title": "Test City",
                    "summary": "A city.",
                    "canonical_facts": [],
                    "related_character_names": [],
                    "confidence": 0.6,
                }
            ],
        }

    @property
    def descriptor(self) -> InferenceProviderDescriptor:
        return InferenceProviderDescriptor(
            backend="stub",
            display_name="JSON Stub Runtime",
            transport="stub",
            base_url=None,
            default_model=None,
            timeout_seconds=0.0,
            supports_model_listing=False,
            supports_chat_completions=False,
            aliases=[],
        )

    def generate_text(self, request: InferenceRequest) -> InferenceResponse:
        return InferenceResponse(
            backend="stub",
            model=request.model,
            content=json.dumps(self._response),
            finish_reason="stub_completed",
            raw_response={},
        )


@pytest.fixture
def operations_db() -> Path:
    from app.settings import settings

    db_path = settings.operations_db_path
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = connect_sqlite(db_path)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS character_profiles ("
        "character_id TEXT PRIMARY KEY, project_id TEXT NOT NULL, display_name TEXT NOT NULL)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS discovery_staging ("
        "stage_id TEXT NOT NULL, project_id TEXT NOT NULL, entity_type TEXT NOT NULL,"
        "entity_id TEXT NOT NULL, entity_json TEXT NOT NULL, confidence REAL DEFAULT 0.5,"
        "approved INTEGER DEFAULT 0, dedup_action TEXT DEFAULT 'new',"
        "created_at TEXT DEFAULT (datetime('now')),"
        "PRIMARY KEY (stage_id, entity_type, entity_id))"
    )
    conn.commit()
    conn.close()
    return db_path


class TestCascadeDiscoveryService:
    def test_orchestrator_initializes(self, operations_db: Path) -> None:
        inferencer = JSONStubInferenceBackend()
        job_manager = CascadeJobManager()
        service = CascadeDiscoveryService(inferencer, job_manager)

        assert service._inferencer is inferencer
        assert service._job_manager is job_manager
        assert service._scorer is not None
        assert service._deduper is not None

    def test_parse_extraction_json(self) -> None:
        raw = '{"characters": [{"display_name": "Alice"}], "relationships": [], "world_entries": []}'
        result = CascadeDiscoveryService._parse_extraction(raw)
        assert result["characters"][0]["display_name"] == "Alice"

    def test_parse_with_markdown_fences(self) -> None:
        raw = '```json\n{"characters": [{"display_name": "Bob"}], "relationships": [], "world_entries": []}\n```'
        result = CascadeDiscoveryService._parse_extraction(raw)
        assert result["characters"][0]["display_name"] == "Bob"

    def test_chunk_and_extract_empty_text(self, operations_db: Path) -> None:
        response = {
            "characters": [],
            "relationships": [],
            "world_entries": [],
        }
        inferencer = JSONStubInferenceBackend(response)
        job_manager = CascadeJobManager()
        service = CascadeDiscoveryService(inferencer, job_manager)

        short_text = "Hello world."
        chunks = service._chunk_text(short_text, chunk_size=8000)
        assert len(chunks) == 1
        assert chunks[0] == short_text

    def test_run_scan_returns_job_id(self, operations_db: Path) -> None:
        inferencer = JSONStubInferenceBackend()
        job_manager = CascadeJobManager()
        service = CascadeDiscoveryService(inferencer, job_manager)

        job_id = service.run_scan(project_id="proj-1", manuscript_text="Once upon a time.")
        assert job_id is not None
        assert len(job_id) == 36

    def test_run_scan_persists_to_staging(self, operations_db: Path) -> None:
        from app.settings import settings

        inferencer = JSONStubInferenceBackend()
        job_manager = CascadeJobManager()
        service = CascadeDiscoveryService(inferencer, job_manager)

        service.run_scan(project_id="proj-1", manuscript_text="Once upon a time.")

        conn = connect_sqlite(settings.operations_db_path)
        rows = conn.execute("SELECT entity_type FROM discovery_staging").fetchall()
        conn.close()

        entity_types = [r[0] for r in rows]
        assert "character" in entity_types
        assert "relationship" in entity_types
        assert "world_bible" in entity_types

    def test_run_scan_marks_job_completed(self, operations_db: Path) -> None:
        inferencer = JSONStubInferenceBackend()
        job_manager = CascadeJobManager()
        service = CascadeDiscoveryService(inferencer, job_manager)

        job_id = service.run_scan(project_id="proj-1", manuscript_text="Once upon a time.")
        job = job_manager.get_job(job_id)
        assert job is not None
        assert job.status == "completed"
        assert job.stage_id is not None

    def test_run_scan_marks_job_failed_on_error(self, operations_db: Path) -> None:
        from app.settings import settings

        response = {"characters": [{"display_name": "X"}], "relationships": [], "world_entries": []}
        inferencer = JSONStubInferenceBackend(response)
        job_manager = CascadeJobManager()
        service = CascadeDiscoveryService(inferencer, job_manager)

        service.run_scan(project_id="proj-1", manuscript_text="Once upon a time.")

        conn = connect_sqlite(settings.operations_db_path)
        char_rows = conn.execute(
            "SELECT entity_json FROM discovery_staging WHERE entity_type='character'"
        ).fetchall()
        conn.close()

        assert len(char_rows) == 1
        stored = json.loads(char_rows[0][0])
        assert stored["display_name"] == "X"
