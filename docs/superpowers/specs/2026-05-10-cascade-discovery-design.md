# Cascade Discovery Engine — Design Spec

## Overview

The Cascade Discovery Engine extracts entities from manuscript text via LLM analysis, stages them for user review, and persists approved entities to the project database. It operates in two tiers:

- **Core cascade** (v1): Characters, relationships, world bible entries.
- **Extended cascade** (roadmap): Arcs, foundation updates, planning structure.

## Architecture

### Service Layer

```
CascadeDiscoveryService (orchestrator)
├── TextChunker — splits manuscript into configurable chunks with overlap
├── LLMExtractor — single-pass extraction per chunk via inference backend
├── DeduplicationEngine — fuzzy + exact matching against existing entities
├── ConfidenceScorer — heuristic-based confidence per entity
├── StagingManager — persists discovered entities to staging table
└── CascadePersister — commits approved entities in single transaction
```

### Data Flow

```
Manuscript text
  → TextChunker (8K words default, configurable)
  → LLMExtractor (one call per chunk, structured JSON output)
  → DeduplicationEngine (exact merge, fuzzy flag for review)
  → ConfidenceScorer (heuristic scoring)
  → StagingManager (discovery_staging table)
  → Frontend review UI (approve/reject per entity)
  → CascadePersister (single transaction commit)
```

### Persistence Model

**New table**: `discovery_staging` in operations DB.

| Column | Type | Description |
|--------|------|-------------|
| `stage_id` | TEXT PK | UUID for the staging session |
| `project_id` | TEXT | FK to project |
| `entity_type` | TEXT | "character", "relationship", "world_bible" |
| `entity_json` | TEXT | Full entity data as JSON |
| `confidence` | REAL | 0.0–1.0 confidence score |
| `source_excerpt` | TEXT | Manuscript passage that triggered discovery |
| `source_chunk` | INTEGER | Chunk index for traceability |
| `approved` | INTEGER | 0=pending, 1=approved, -1=rejected |
| `dedup_action` | TEXT | "new", "exact_merge", "fuzzy_merge", "enrich" |
| `created_at` | DATETIME | Timestamp |

Auto-cleanup: entries older than 24 hours are purged on service startup.

### Async Job Pattern

Follows story import pattern: `CascadeJobManager` with in-memory job store, ThreadPoolExecutor (max 2 workers), progress polling via `GET /v1/discovery/jobs/{job_id}`.

| Phase | Description |
|-------|-------------|
| `chunking` | Splitting manuscript into chunks |
| `extracting` | LLM extraction in progress (includes chunk index, total) |
| `deduplicating` | Running deduplication against existing entities |
| `staging` | Persisting to staging table |
| `completed` | Ready for review |
| `failed` | Error occurred |

## Core Cascade — Entity Extraction

### Characters

**LLM Output Schema**:
```json
{
  "characters": [
    {
      "display_name": "Annabelle",
      "aliases": ["The Woman", "Lady Annabelle"],
      "role_in_story": "protagonist",
      "archetype": "hero",
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
      "first_appearance_context": "enters the castle",
      "description": "Brief description of the character"
    }
  ]
}
```

**Deduplication**:
- Exact match (case-insensitive display name): auto-merge, enrich existing profile. Non-empty fields from discovery overwrite empty fields in existing profile; if both are non-empty, the discovery value is shown as a diff for user approval before merge.
- Fuzzy match (Levenshtein ≤ 2, or alias overlap): flag for user review with "Merge" / "Keep Separate" toggle.
- No match: mark as new character.

**Provisional IDs**: New characters receive temporary IDs (`discovery-{stage_id}-{hash(display_name)[:12]}`) before persistence. After character deduplication resolves to final IDs (existing or new), relationship references are rewritten to use resolved IDs. This ensures relationships always point to valid character IDs at commit time.

### Relationships

**LLM Output Schema**:
```json
{
  "relationships": [
    {
      "source_character_name": "Annabelle",
      "target_character_name": "The Son",
      "relation_kind": "rivalry",
      "summary": "Competing for the same inheritance",
      "tension": "Unspoken resentment over family legacy",
      "directionality": "directed",
      "confidence_note": "Explicitly stated in dialogue"
    }
  ]
}
```

**Discovery Rules**:
- Only direct interactions or relationships with significant confidence.
- Indirect relationships (e.g., "both hate the same person") excluded unless explicitly stated.
- Directionality: directed by default; bidirectional if the LLM detects mutual dynamics.
- New characters referenced in relationships get provisional IDs; resolved after character deduplication.

### World Bible

**LLM Output Schema**:
```json
{
  "world_entries": [
    {
      "entry_type": "location",
      "title": "Castle of Echoes",
      "summary": "Ancient fortress where the story begins",
      "canonical_facts": ["Built in the 3rd century", "Overlooks the valley"],
      "related_character_names": ["Annabelle"],
      "confidence_note": "Described in detail, central to plot"
    }
  ]
}
```

**Entry Types**: location, organization, magic_system, technology, creature, concept, object, custom.
- LLM auto-classifies; user can edit type in review UI before approval.

## Confidence Scoring

### Heuristic Formula

```
confidence = (mention_weight * 0.3) + (description_weight * 0.3) + (interaction_weight * 0.25) + (llm_confidence * 0.15)
```

| Factor | Calculation | Weight |
|--------|-------------|--------|
| Mention count | min(mentions / 5, 1.0) — saturates at 5+ mentions | 0.30 |
| Description richness | min(non-empty fields / total fields, 1.0) | 0.30 |
| Interaction density | For characters: number of relationships involving this entity, capped at 3 | 0.25 |
| LLM self-rating | Extracted from LLM output (0–1 scale) | 0.15 |

### Confidence Thresholds

| Level | Range | Behavior |
|-------|-------|----------|
| High | ≥ 0.7 | Expanded by default, auto-approved if user selects "Approve All High" |
| Medium | 0.4–0.69 | Visible in list, requires explicit approval |
| Low | < 0.4 | Collapsed by default, requires explicit review |

## Prompt Design

### Single-Pass Extraction Prompt

System prompt instructs LLM to extract all three entity types from the provided text. Output is a single JSON object with `characters`, `relationships`, and `world_entries` arrays.

Key instructions:
- Extract only entities that appear directly in the text.
- For characters: include all names/aliases mentioned, even minor characters.
- For relationships: only direct interactions or explicitly stated dynamics.
- For world entries: locations, objects, organizations, concepts with narrative significance.
- Self-rate confidence (0–1) for each entity.
- Include source text excerpt for traceability.

**Temperature**: 0.1 (deterministic).
**Max tokens**: 12000 (extraction output can be verbose).

### Chunking Strategy

- Default: 8000 words per chunk, 500-word overlap.
- Configurable via `NARRATIVE_DISCOVERY_CHUNK_SIZE` and `NARRATIVE_DISCOVERY_OVERLAP`.
- Chunks are split at paragraph boundaries to avoid mid-sentence breaks.
- Cross-chunk entity merging happens in the deduplication phase.

## Extended Cascade — Roadmap Design

### Arcs (Phase 2)

**Approach**: After characters and relationships are staged, run arc detection on the full manuscript using discovered character data as context.

**LLM Output**:
```json
{
  "arcs": [
    {
      "character_name": "Annabelle",
      "arc_type": "transformation",
      "name": "From orphan to heir",
      "summary": "Annabelle discovers her true lineage and claims her inheritance",
      "stage_map": {
        "status_quo": "Lives as a servant, unaware of heritage",
        "inciting_incident": "Finds the letter revealing her parentage",
        "rising_action": "Discovers clues, faces opposition from rivals",
        "crisis": "The letter is destroyed; must prove identity without proof",
        "climax": "Confronts the ruling council with witness testimony",
        "resolution": "Recognized as heir, but chooses to share power"
      }
    }
  ]
}
```

**Dependencies**: Requires characters to be persisted first (arc references character IDs).

### Foundation Updates (Phase 2)

**Approach**: Compare discovered entities against existing foundation profile. Suggest updates to premise, thematic spine, tone direction based on new discoveries.

**LLM Output**:
```json
{
  "foundation_suggestions": {
    "premise_update": "Suggested revised premise incorporating new characters",
    "thematic_additions": ["Identity and belonging", "Power and sacrifice"],
    "tone_shift": "Slightly darker than current foundation suggests",
    "rationale": "The manuscript introduces themes of..."
  }
}
```

**UI**: Diff view showing current vs. suggested foundation fields, with per-field approve/reject.

### Planning Structure (Phase 2)

**Approach**: Analyze discovered content to suggest sequence/chapter structure.

**LLM Output**:
```json
{
  "sequences": [
    {
      "name": "Act I: Discovery",
      "chapters": [
        {
          "title": "The Servant's Life",
          "summary": "Annabelle's daily routine in the castle",
          "active_character_names": ["Annabelle", "The Son"],
          "scene_hints": ["Morning routine", "Overhearing conversation"]
        }
      ]
    }
  ]
}
```

**Dependencies**: Requires characters and arcs to be persisted first.

## UI/UX Design

### Entry Point

"Scan Manuscript" button in PlanningView, visible on Characters and Relationships tabs. Also accessible from WritingView as an action dropdown item.

Button triggers modal: text input area (paste or select chapter), chunk size config, "Start Scan" button.

### Review Dialog

Full-screen modal with three tabs: **Characters** / **Relationships** / **World Bible**.

Each tab shows summary counts at top:
- "3 new characters · 1 enrichment · 0 conflicts"
- "5 relationships found · 2 involving new characters"
- "2 locations · 1 concept discovered"

### Entity Rows

Each row displays:
- Entity name/title
- Brief description (truncated, expandable)
- Confidence badge (high/medium/low color-coded)
- Source text excerpt (collapsed by default, expandable)
- Approve / Reject buttons
- For fuzzy matches: "Merge with [existing]?" toggle

Low-confidence entities collapsed by default, behind "Show 3 more" expander.

### Bulk Actions

Per-tab header: "Approve All" / "Reject All" / "Approve High Confidence Only".

Global footer: "Apply X changes" button showing total count across all tabs.

### Post-Apply Summary

Toast notification: "Added 3 characters, 2 relationships, 1 location · Undo".

Undo reverts the entire batch by rolling back the transaction and cleaning staging entries.

## API Endpoints

| Method | Path | Status | Description |
|--------|------|--------|-------------|
| `POST` | `/v1/discovery/scan` | 202 | Submit manuscript for cascade discovery |
| `GET` | `/v1/discovery/jobs/{job_id}` | 200 | Get job progress and results |
| `GET` | `/v1/discovery/staging/{stage_id}` | 200 | Get staged entities for review |
| `PATCH` | `/v1/discovery/staging/{stage_id}/entities` | 200 | Update entity approval status |
| `POST` | `/v1/discovery/staging/{stage_id}/apply` | 200 | Commit approved entities |
| `POST` | `/v1/discovery/staging/{stage_id}/undo` | 200 | Revert last applied batch |
| `DELETE` | `/v1/discovery/staging/{stage_id}` | 200 | Discard staging session |

### Request/Response Schemas

**Scan Request**:
```json
{
  "project_id": "uuid",
  "manuscript_text": "...",
  "chunk_size": 8000,
  "include_types": ["character", "relationship", "world_bible"]
}
```

**Job Progress Response**:
```json
{
  "job_id": "uuid",
  "status": "extracting",
  "phase": "extracting",
  "chunk_index": 2,
  "total_chunks": 5,
  "stage_id": null,
  "error": null
}
```

**Staged Entities Response**:
```json
{
  "stage_id": "uuid",
  "project_id": "uuid",
  "characters": [...],
  "relationships": [...],
  "world_bible": [...]
}
```

## Error Handling

| Error | Behavior |
|-------|----------|
| LLM timeout | Retry with same chunk (max 2 retries), mark as failed if all retries exhausted |
| Malformed JSON | Retry with narrowed scope (single entity type), then fail gracefully |
| No entities found | Return completed job with empty staging, show "No entities discovered" in UI |
| Chunk too large | Auto-split into smaller chunks, continue processing |
| Database conflict | Upsert with `ON CONFLICT DO UPDATE`, log warning for debug |

## Testing Strategy

1. **Unit tests**: Text chunker boundary cases, deduplication logic, confidence scoring, JSON parsing with malformed input.
2. **Integration tests**: Full cascade pipeline with stub inference backend, verify staging → apply flow, transaction rollback on undo.
3. **Prompt tests**: Verify LLM output matches expected JSON schema for representative manuscript excerpts.
4. **E2E tests**: Submit scan → poll job → review staging → apply → verify entities persisted correctly.

## Config Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `NARRATIVE_DISCOVERY_CHUNK_SIZE` | 8000 | Words per chunk |
| `NARRATIVE_DISCOVERY_OVERLAP` | 500 | Overlap words between chunks |
| `NARRATIVE_DISCOVERY_MAX_TOKENS` | 12000 | Max tokens per LLM call |
| `NARRATIVE_DISCOVERY_STAGING_TTL_HOURS` | 24 | Auto-cleanup threshold |
| `NARRATIVE_DISCOVERY_CONFIDENCE_THRESHOLD_MEDIUM` | 0.4 | Boundary between low and medium |
| `NARRATIVE_DISCOVERY_CONFIDENCE_THRESHOLD_HIGH` | 0.7 | Boundary between medium and high |

## Dependencies

- **Inference backend**: Shared `InferenceBackend` via factory, same circuit breaker pattern.
- **StoryKnowledgeService**: For loading existing characters, relationships, world entries for deduplication.
- **CascadeJobManager**: New job management module, follows `ImportJobManager` pattern.
- **Staging table**: Created via migration in `app/persistence/sqlite.py`.

## File Structure

```
app/
├── api/
│   └── discovery.py              # Router: scan, jobs, staging, apply, undo
├── services/
│   ├── cascade_discovery.py      # Orchestrator service
│   ├── text_chunker.py           # Chunking logic with overlap
│   ├── deduplication_engine.py   # Fuzzy + exact matching
│   ├── confidence_scorer.py      # Heuristic scoring
│   └── discovery_jobs.py         # Job manager (async pattern)
├── schemas/
│   └── discovery.py              # Request/response schemas
├── persistence/
│   └── sqlite.py                 # discovery_staging table migration
└── services/
    └── runtime_prompts.py        # build_cascade_extraction_request()
```

```
frontend/src/
├── components/discovery/
│   ├── ScanDialog.tsx            # Text input + config modal
│   ├── ReviewDialog.tsx          # Full-screen review with tabs
│   ├── CharacterReviewTab.tsx    # Character entity rows
│   ├── RelationshipReviewTab.tsx # Relationship entity rows
│   └── WorldBibleReviewTab.tsx   # World Bible entity rows
├── hooks/
│   └── useCascadeDiscovery.ts    # Job polling, staging CRUD
├── services/
│   └── discovery.ts              # API client functions
└── types/
    └── discovery.ts              # TypeScript interfaces
```

## Success Criteria

- User can paste a chapter and discover characters, relationships, and world entities in one scan.
- Review UI shows all discovered entities with confidence scores and source excerpts.
- User can approve/reject per entity or bulk-approve.
- Applied entities persist correctly with proper deduplication.
- Undo reverts the entire batch cleanly.
- Extended cascade (arcs, foundation, planning) documented as concrete design ready for Phase 2.