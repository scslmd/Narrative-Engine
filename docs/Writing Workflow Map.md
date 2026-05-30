# Narrative Engine — Writing Workflow Map

> 6-stage process derived from writer research. Non-linear: authors loop, backtrack, and iterate between stages.

## Stage Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        WRITING PROCESS (6 STAGES)                          │
│                                                                             │
│  Stage 1        Stage 2       Stage 3       Stage 4       Stage 5       Stage 6       │
│  IDEATION  →  PLANNING  →   RESEARCH   →   DRAFTING   →   REVISION   →    POLISH      │
│                                                                             │
│  Ideas, Notes   Characters    Research      Manuscripts   Revision        Polish       │
│               World Bible   Reference       Drafts        Suggestions   Formatting     │
│               Relationships Generation      (P-100/300)   Review        Export         │
│               Arcs          Just-in-time    Assist        Inspect                               │
│               Structure                               Canon                                    │
│               Chapters                                Jobs                                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Panel-to-Stage Mapping

| Stage | Rail Section | Panels | Walkthrough Phase |
|-------|-------------|--------|-------------------|
| 1. Ideation | Ideation | Ideas, Notes | Phase 4b |
| 2. Planning | Planning | Characters, World Bible, Relationships, Arcs, Structure, Chapters | Phase 3 |
| 3. Research | Research | Research | Phase 5 |
| 4. Drafting | Drafting | Manuscripts, Drafts, Generation | Phase 6, 10 |
| 5. Revision | Revision | Revision, Suggestions, Review, Inspect | Phase 7, 8 |
| 6. Polish | Polish | Polish, Canon, Jobs | Phase 9, 12 |

## Non-Linear Navigation

Authors do not follow a strict linear path. The workflow supports:

```
  ┌─────────────────────────────────────────────────────────────────┐
  │                    NON-LINEAR FLOW PATTERNS                     │
  │                                                                 │
  │  IDEATION ──→ PLANNING ──→ RESEARCH ──→ DRAFTING                │
  │    ↑              ↑            ↑            │                    │
  │    │              │            │            ↓                    │
  │    │              │            │         REVISION ──→ POLISH     │
  │    │              │            │            ↑         │          │
  │    │              │            │            │         │          │
  │    └───────┘      │            └───────┘    │         │          │
  │                   │                        │         │          │
  │    Mid-draft idea  │    Just-in-time        │  Canon-tight       │
  │    capture →       │    research →          │  loop →            │
  │    promote to      │                       │  regenerate →      │
  │    planning        │                       │                    │
  │                                                                 │
  │  Key loops:                                                     │
  │  1. Draft → discover gap → Research → fill → back to Draft      │
  │  2. Draft → Revision → find issue → modify Canon → Regenerate   │
  │  3. Revision → Checker → Inspect → annotate → Regenerate        │
  │  4. Polish → discover problem → back to any stage               │
  └─────────────────────────────────────────────────────────────────┘
```

## Iteration Patterns

### Pattern A: Generate → Change → Regenerate

```
  1. GENERATE: Run generation for chapter(s)
  2. DISCOVER: Read output, find issue (e.g., character voice drift)
  3. CHANGE:   Modify canon (e.g., update Voice Notes, add World Bible entry)
  4. REGENERATE: Re-run generation with updated canon
  5. VERIFY:   Read revised output, confirm fix
  6. CONTINUE: Move to next chapter or move to Revision stage
```

**Example:** Generate Ch 7 → AURA-7 sounds too coherent → Update AURA-7 Voice Notes → Re-run Ch 7 → AURA-7 speaks in fragments → Move to Ch 8

### Pattern B: Multi-Layer Revision

```
  Layer 1: Structural (big picture) → timeline, pacing, arcs
  Layer 2: Character (development)  → voice, motivation, consistency
  Layer 3: Scene (pacing)           → dialogue, transitions, sensory detail
  Layer 4: Line Edit (prose)        → word choice, repetition, variety
  Layer 5: Copy Edit (mechanics)    → grammar, spelling, punctuation
```

### Pattern C: Branch Exploration

```
  1. CREATE: Create branch for alternate direction
  2. DRAFT:  Generate alternate version
  3. COMPARE: Evaluate against main branch
  4. DECIDE: Merge preferred or keep both
```

## Route Map

| Route | Stage | Description |
|-------|-------|-------------|
| `/` | — | Project list and creation |
| `/setup-wizard` | Ideation | Conversational setup |
| `/workspace/:projectId/plan` | Planning | Planning workspace (12 tabs) |
| `/workspace/:projectId/braindump` | Ideation | Brain dump sessions |
| `/workspace/:projectId/studio` | All | Studio Desk (floating-panel workspace) |
| `/workspace/:projectId/review` | Revision | Review workspace (checker findings) |
| `/workspace/:projectId/inspect` | Revision | Inspect workspace (job/run inspection) |
| `/workspace/:projectId/canon` | Polish | Canon Workshop (profiles, scope) |
| `/workspace/:projectId/generate` | Drafting | Story Generation (wizard, runs) |

## Studio Desk Rail Layout

```
┌─────────────────────┐
│  STUDIO DESK RAIL   │
├─────────────────────┤
│  IDEATION           │
│  ├─ Ideas           │
│  └─ Notes           │
├─────────────────────┤
│  PLANNING           │
│  ├─ Characters      │
│  ├─ World Bible     │
│  ├─ Relationships   │
│  ├─ Arcs            │
│  ├─ Structure       │
│  └─ Chapters        │
├─────────────────────┤
│  RESEARCH           │
│  └─ Research        │
├─────────────────────┤
│  DRAFTING           │
│  ├─ Manuscripts     │
│  ├─ Drafts          │
│  └─ Generation      │
├─────────────────────┤
│  REVISION           │
│  ├─ Revision        │
│  ├─ Suggestions     │
│  ├─ Review          │
│  └─ Inspect         │
├─────────────────────┤
│  POLISH             │
│  ├─ Polish          │
│  ├─ Canon           │
│  └─ Jobs            │
└─────────────────────┘
```

## End-to-End Flow (17 Steps)

```
  Part 1:   Project Foundation (Steps 1-2)
  Part 1b:  Ideation Capture (Step 2b)
  Part 2:   Character Architecture (Step 3)
  Part 3:   Research (Step 5)
  Part 4:   World Bible (Step 6)
  Part 5:   Arc Planning (Step 7)
  Part 6:   Structure Planning (Step 8)
  Part 7:   Canon Management (Step 9)
  Part 8:   Multi-Run Generation (Steps 10-12)
  Part 9:   Revision (Step 13)
  Part 10:  Polish (Step 14)
  Part 11:  Export and Archive (Step 17)
```

## UI Integration

The workflow is integrated into the Studio Desk left rail as 6 stage sections with a **Writing Progress** indicator at the top. See `Studio Desk Workflow Mockup.html` for a visual mockup showing:

- **Progress dots** at rail top — clickable stage navigation, shows current stage
- **Stage-colored active states** — left bar on active panel matches stage color
- **Entity count badges** — item counts on panels (e.g., "Characters · 7")
- **Non-linear access** — any stage accessible from any other stage via rail

## Research Sources

This workflow is based on research from 6 authoritative sources covering 23-step proven processes, revision methodology, character development, worldbuilding, and writing pedagogy. See `docs/superpowers/research/2026-05-23-writers-process-research.md` for full source list and findings.