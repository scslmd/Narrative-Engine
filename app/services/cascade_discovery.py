from __future__ import annotations

import json
import sqlite3
import uuid
from typing import Literal

from app.inference.base import InferenceBackend
from app.persistence.sqlite import connect as connect_sqlite
from app.services.confidence_scorer import ConfidenceScorer
from app.services.deduplication_engine import DeduplicationEngine
from app.services.discovery_jobs import CascadeJob, CascadeJobManager
from app.services.runtime_prompts import build_cascade_extraction_request
from app.services.text_chunker import TextChunker
from app.settings import settings

import logging

logger = logging.getLogger(__name__)

ScanPhase = Literal["pending", "chunking", "extracting", "deduplicating", "staging"]


class CascadeDiscoveryService:
    def __init__(self, inferencer: InferenceBackend, job_manager: CascadeJobManager) -> None:
        self._inferencer = inferencer
        self._job_manager = job_manager
        self._scorer = ConfidenceScorer()
        self._deduper = DeduplicationEngine()

    def run_scan(
        self,
        project_id: str,
        manuscript_text: str,
        chunk_size: int = 8000,
        include_types: list[str] | None = None,
    ) -> str:
        job = self._job_manager.create_job(project_id)
        try:
            self._execute(
                job,
                project_id,
                manuscript_text,
                chunk_size,
                include_types or ["character", "relationship", "world_bible"],
            )
        except Exception as exc:
            logger.error("Cascade scan failed for job %s: %s", job.job_id, exc)
            self._job_manager.fail(job.job_id, str(exc))
        return job.job_id

    def _execute(
        self,
        job: CascadeJob,
        project_id: str,
        manuscript_text: str,
        chunk_size: int,
        include_types: list[str],
    ) -> None:
        chunks = self._chunk_text(manuscript_text, chunk_size)
        self._job_manager.update_progress(job.job_id, "chunking")
        self._job_manager.update_progress(job.job_id, "extracting", total_chunks=len(chunks))

        all_results: list[dict] = []
        for i, chunk in enumerate(chunks):
            self._job_manager.update_progress(job.job_id, "extracting", chunk_index=i)
            result = self._extract_chunk(chunk, project_id)
            if result:
                all_results.append(result)

        self._job_manager.update_progress(job.job_id, "deduplicating")
        merged = self._merge_results(all_results, project_id)

        self._job_manager.update_progress(job.job_id, "staging")
        stage_id = str(uuid.uuid4())
        self._persist_staging(stage_id, project_id, merged)
        self._job_manager.complete(job.job_id, stage_id)

    # -- Chunking -----------------------------------------------------------

    def _chunk_text(self, text: str, chunk_size: int) -> list[str]:
        overlap = settings.discovery_overlap
        chunker = TextChunker(chunk_size=chunk_size, overlap=overlap)
        return chunker.chunk(text)

    # -- Extraction ---------------------------------------------------------

    def _extract_chunk(self, chunk_text: str, project_id: str) -> dict | None:
        existing_chars = self._load_existing_characters(project_id)
        char_names = [f"{c['character_id']}: {c['display_name']}" for c in existing_chars] if existing_chars else []

        request = build_cascade_extraction_request(chunk_text, existing_characters=char_names)
        response = self._inferencer.generate_text(request)
        parsed = self._parse_extraction(response.content)
        return parsed

    @staticmethod
    def _parse_extraction(raw: str) -> dict:
        text = raw.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(line.strip() for line in lines[1:])
            if text.endswith("```"):
                text = text[:-3].strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            logger.warning("JSON parse failed for extraction output, attempting brace extraction")
            start = text.index("{")
            end = text.rindex("}") + 1
            return json.loads(text[start:end])

    # -- Existing data lookup -----------------------------------------------

    def _load_existing_characters(self, project_id: str) -> list[dict]:
        try:
            db_path = settings.operations_db_path
            conn = sqlite3.connect(str(db_path))
            rows = conn.execute(
                "SELECT character_id, display_name FROM character_profiles WHERE project_id=?",
                (project_id,),
            ).fetchall()
            conn.close()
            return [{"character_id": r[0], "display_name": r[1]} for r in rows] if rows else []
        except Exception:
            return []

    # -- Merging ------------------------------------------------------------

    def _merge_results(self, results: list[dict], project_id: str) -> dict:
        merged: dict = {"characters": {}, "relationships": [], "world_entries": {}}

        for result in results:
            for char in result.get("characters", []):
                name = char["display_name"].lower()
                if name not in merged["characters"]:
                    merged["characters"][name] = char
                else:
                    existing = merged["characters"][name]
                    for key, value in char.items():
                        if value and not existing.get(key):
                            existing[key] = value

            merged["relationships"].extend(result.get("relationships", []))
            for entry in result.get("world_entries", []):
                key = f"{entry['entry_type']}:{entry['title'].lower()}"
                if key not in merged["world_entries"]:
                    merged["world_entries"][key] = entry

        deduped_rels = self._deduper.deduplicate_relationship_pairs(
            [(r["source_character_name"], r["target_character_name"]) for r in merged["relationships"]]
        )
        rel_map = {
            (r["source_character_name"].lower(), r["target_character_name"].lower()): r
            for r in merged["relationships"]
        }
        merged["relationships"] = [
            rel_map.get(
                (s.lower(), t.lower()),
                {
                    "source_character_name": s,
                    "target_character_name": t,
                    "relation_kind": "unknown",
                    "summary": "",
                    "tension": None,
                    "directionality": "directed",
                    "confidence": 0.5,
                },
            )
            for s, t in deduped_rels
        ]

        return {
            "characters": list(merged["characters"].values()),
            "relationships": merged["relationships"],
            "world_entries": list(merged["world_entries"].values()),
        }

    # -- Persistence --------------------------------------------------------

    def _persist_staging(self, stage_id: str, project_id: str, merged: dict) -> None:
        db_path = settings.operations_db_path
        conn = connect_sqlite(db_path)
        conn.execute(
            """CREATE TABLE IF NOT EXISTS discovery_staging (
                stage_id TEXT NOT NULL,
                project_id TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                entity_json TEXT NOT NULL,
                confidence REAL DEFAULT 0.5,
                approved INTEGER DEFAULT 0,
                dedup_action TEXT DEFAULT 'new',
                created_at TEXT DEFAULT (datetime('now')),
                PRIMARY KEY (stage_id, entity_type, entity_id)
            )"""
        )
        conn.execute("BEGIN IMMEDIATE")

        for char in merged.get("characters", []):
            score = self._scorer.score_character(
                display_name=char["display_name"],
                mention_count=0,
                non_empty_fields=sum(1 for v in char.values() if v),
                total_fields=len(char),
                relationship_count=0,
                llm_confidence=char.get("confidence", 0.5),
            )
            entity_id = char["display_name"].lower().replace(" ", "-")
            conn.execute(
                """INSERT INTO discovery_staging
                   (stage_id, project_id, entity_type, entity_id, entity_json, confidence, approved, dedup_action, created_at)
                   VALUES (?, ?, 'character', ?, ?, ?, 0, 'new', datetime('now'))""",
                (stage_id, project_id, entity_id, json.dumps(char), score),
            )

        for rel in merged.get("relationships", []):
            score = self._scorer.score_relationship(
                explicit_mention=bool(rel.get("summary")),
                dialogue_context=bool(rel.get("tension")),
                llm_confidence=rel.get("confidence", 0.5),
            )
            entity_id = f"rel-{rel['source_character_name'].lower()}-{rel['target_character_name'].lower()}"
            conn.execute(
                """INSERT INTO discovery_staging
                   (stage_id, project_id, entity_type, entity_id, entity_json, confidence, approved, dedup_action, created_at)
                   VALUES (?, ?, 'relationship', ?, ?, ?, 0, 'new', datetime('now'))""",
                (stage_id, project_id, entity_id, json.dumps(rel), score),
            )

        for entry in merged.get("world_entries", []):
            score = self._scorer.score_world_entry(
                mention_count=0,
                description_fields=sum(1 for v in entry.values() if v),
                total_fields=len(entry),
                llm_confidence=entry.get("confidence", 0.5),
            )
            entity_id = f"wb-{entry['entry_type']}-{entry['title'].lower().replace(' ', '-')}"
            conn.execute(
                """INSERT INTO discovery_staging
                   (stage_id, project_id, entity_type, entity_id, entity_json, confidence, approved, dedup_action, created_at)
                   VALUES (?, ?, 'world_bible', ?, ?, ?, 0, 'new', datetime('now'))""",
                (stage_id, project_id, entity_id, json.dumps(entry), score),
            )

        conn.commit()
        conn.close()
