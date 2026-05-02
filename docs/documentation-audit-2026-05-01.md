# Documentation Audit Results

Date: 2026-05-01
Purpose: Post-implementation docs cleanup after story generation orchestration feature

## Summary

| Action | Count | Rationale |
|--------|-------|-----------|
| ARCHIVE (move to `docs/archive/`) | 30 | Completed features, implemented blueprints, resolved analyses |
| KEEP (stay in `docs/`) | 10 | Forward-looking blueprints, active references, end-user guides |
| DELETE (remove entirely) | 7 | Superseded v1.1 versions where v1.3 exists |

## Files to Archive (30)

### Story Import - Completed Feature (14 files)
- `Story Import - Implementation Task List.md` - completed task list
- `Story Import Capability Hardening v0.1.md` - hardening pass done
- `Story Import Full Implementation Task List.md` - all 12 tasks checked off
- `Story Import Implementation Plan v1.0.md` - implemented
- `Story Import Implementation Research.md` - historical, feature shipped
- `Story Import Research & Architecture.md` - superseded by AGENTS.md section
- `story-import-battle-hardening-2026-04-30.md` - hardening completed
- `story-import-battle-hardening-task-list-2026-04-30.md` - all 9 tasks checked off
- `story-import-continuity-and-drafting-execution-checklist-2026-04-30.md` - tasks completed
- `story-import-continuity-and-drafting-spec-2026-04-30.md` - spec implemented, P0 fixed
- `story-import-continuity-and-drafting-task-list-2026-04-30.md` - tasks completed
- `story-import-full-digestion-hardening-2026-04-30.md` - hardening done
- `story-import-full-digestion-task-list-2026-04-30.md` - all 27 tasks checked off
- `story-import-review-2026-04-30.md` - review findings addressed

### v0.1 Blueprints - Implemented (9 files)
- `Async Protocol Blueprint v0.1.md` - in AGENTS.md
- `Failure Mode Test Matrix v0.1.md` - outdated test matrix
- `Inference Runtime Blueprint v0.1.md` - in AGENTS.md
- `Runtime Error Mapping Blueprint v0.1.md` - implemented
- `Runtime Telemetry Contract v0.1.md` - implemented
- `Step and Lineage API Projection Blueprint v0.1.md` - in AGENTS.md
- `Step and Lineage API Test Matrix v0.1.md` - implemented
- `Step Record Blueprint v0.1.md` - implemented
- `BACKEND_API_REFERENCE.md` - outdated vs AGENTS.md, missing story-generation/braindump

### Completed Plans & Reviews (5 files)
- `Code Review - Story Import Issues.md` - historical review, issues addressed
- `production-v1-readiness-review-2026-05-01.md` - P0 blockers fixed
- `production-v1-readiness-task-list-2026-05-01.md` - all tasks checked off
- `Integration Audit & Implementation Tasks v0.1.md` - 98% complete, findings addressed
- `Manuscript Word Processor Plan v1.0.md` - "ALL TASKS COMPLETE"
- `Manuscript Word Processor Tasks.md` - WP-01 through WP-11 complete
- `PlanningView_Refactor_Plan.md` - refactor completed
- `Test Failure Analysis v0.2.md` - all 29 failures fixed

### Superseded User Specs (4 files)
- `Feature Reference v1.3.md` - duplicated by AGENTS.md API patterns
- `Narrative SRS v1.3.md` - backend SRS now in AGENTS.md
- `Story Development Canonical Contract v1.3.md` - AGENTS.md is current truth
- `Story Development Product Spec v1.3.md` - most features implemented, AGENTS.md is working reference

### Feature Survey (1 file)
- `story-generation-feature-survey-2026-05-01.md` - post-implementation audit of completed blueprint

## Files to Keep (10)

| File | Reason |
|------|--------|
| `Frontend Workspace Behavior Contract v0.1.md` | Specific frontend rules complementing AGENTS.md |
| `frontend-canon-customization-enhancement-blueprint-2026-05-02.md` | Future feature blueprint, not yet implemented |
| `manuscript-editor-llm-assist-blueprint-2026-05-02.md` | Future feature blueprint, not yet implemented |
| `Narrative Engine User Walkthrough v1.3.md` | End-user walkthrough for onboarding |
| `Orchestrator Deterministic Task Spec v0.1.md` | Process template for task decomposition |
| `QUALITY_GUIDELINES.md` | Active scoring rubrics for code reviews |
| `story-generation-orchestration-blueprint-2026-05-02.md` | Architecture reference for implemented feature |
| `Story Arc Paradigm Blueprint v0.1.md` | Domain knowledge, not yet implemented as feature |
| `STRUCTURE.md` | Repository orientation guide |
| `User Guide v1.3.md` | End-user guide for onboarding |

## Files to Delete (7)

Superseded v1.1 versions where v1.3 exists and no archival value:
- `Feature Reference v1.1.md`
- `Narrative Engine User Walkthrough v1.1.md`
- `Narrative SRS v1.1.md`
- `Story Development Canonical Contract v1.1.md`
- `Story Development Product Spec v1.1.md`
- `User Guide v1.1.md`
- `Test Failure Analysis v0.1.md` (explicitly superseded by v0.2)

## Remaining docs/ After Cleanup

```
docs/
  archive/                    # 30 archived files moved here
  Frontend Workspace Behavior Contract v0.1.md
  frontend-canon-customization-enhancement-blueprint-2026-05-02.md
  manuscript-editor-llm-assist-blueprint-2026-05-02.md
  Narrative Engine User Walkthrough v1.3.md
  Orchestrator Deterministic Task Spec v0.1.md
  QUALITY_GUIDELINES.md
  story-generation-orchestration-blueprint-2026-05-02.md
  Story Arc Paradigm Blueprint v0.1.md
  STRUCTURE.md
  User Guide v1.3.md
  superpowers/
```
