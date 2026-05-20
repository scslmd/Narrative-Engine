# Form Entry Optimization — Design Spec

Date: 2026-05-19
Scope: Frontend data entry forms. Fix required/optional field mismatch, add progressive disclosure, guide authors on what matters for story generation.

## Problem Statement

Three data entry forms have usability issues that block efficient author workflow:

1. **Character Bio** — 9 optional backend fields are forced required by frontend `canSave`, preventing basic character creation. No visual distinction between required/optional. No progressive disclosure. All 20 fields in one flat scroll.
2. **World Bible** — Correct required/optional split, but flat editor with no guidance on what matters for story generation. No type-specific field hints.
3. **Arcs** — Panel doesn't exist yet. Needs to be created with proper required/optional flow.
4. **Relationships** — Minor: required field `*` markers inconsistent.

## Character Bio — Current vs Required

| Field | Backend Required | Frontend Required | Fix |
|-------|-----------------|-------------------|-----|
| `character_id` | Yes (`min_length=1`) | Yes (`canSave`) | Keep required |
| `display_name` | Yes (`min_length=1`) | Yes (`canSave`) | Keep required |
| `role_in_story` | Yes (`min_length=1`) | Yes (`canSave`) | Keep required |
| `archetype` | No (default `""`) | Yes (`canSave`) | **Make optional** |
| `external_goal` | No (default `""`) | Yes (`canSave`) | **Make optional** |
| `internal_need` | No (default `""`) | Yes (`canSave`) | **Make optional** |
| `misbelief_or_wound` | No (default `""`) | No | Keep optional |
| `core_fear` | No (default `""`) | No | Keep optional |
| `primary_strength` | No (default `""`) | No | Keep optional |
| `fatal_flaw_or_limitation` | No (default `""`) | Yes (`canSave`) | **Make optional** |
| `contradictions` | No (default `[]`) | No | Keep optional |
| `backstory_summary` | No (default `""`) | Yes (`canSave`) | **Make optional** |
| `voice_notes` | No (default `""`) | Yes (`canSave`) | **Make optional** |
| `secrets` | No (default `[]`) | No | Keep optional |
| `values` | No (default `[]`) | No | Keep optional |
| `taboos` | No (default `[]`) | No | Keep optional |
| `change_axis` | No (default `""`) | Yes (`canSave`) | **Make optional** |
| `arc_stage_notes` | No (default `[]`) | No | Keep optional |
| `continuity_facts` | No (default `[]`) | No | Keep optional |
| `writer_notes` | No (default `null`) | No | Keep optional |

## Design Decisions

### Character Bio: Progressive Disclosure with Sections

Replace flat 20-field form with collapsible sections. Author sees 3 required fields + 2 recommended fields upfront. Remaining fields in collapsible sections.

**Section order:**
1. **Core Identity** (always visible, 3 required): `character_id`, `display_name`, `role_in_story`
2. **Motivation** (always visible, 4 recommended, ⚡ badge): `archetype`, `external_goal`, `internal_need`, `change_axis`
3. **Psychological Depth** (collapsible): `misbelief_or_wound`, `core_fear`, `primary_strength`, `fatal_flaw_or_limitation`, `contradictions`
4. **Context** (collapsible): `backstory_summary`, `voice_notes`, `secrets`, `values`, `taboos`
5. **Tracking** (collapsible): `arc_stage_notes`, `continuity_facts`, `writer_notes`

**Visual indicators:**
- Required fields: red `*` after label
- Recommended fields: "⚡ Used by story generation" badge (orange)
- Optional fields: no indicator (gray "(optional)" after label)

### World Bible: Field Guidance

Keep current required/optional split (correct). Add:
- "📖 Canon context" badge on `canonical_facts` and `summary` (consumed by P-300 SceneContext)
- Group fields: **Core** (title, summary, type) → **Canon** (canonical facts, continuity warnings) → **Notes** (writer notes)

### Arcs: New Panel

Create `StudioArcsPanel.tsx` + `ArcBuilder.tsx`:
- Required: `arc_id`, `name`, `summary`
- Optional: `stage_map_notes`, `fit_notes`, `tags`
- List view with cards, create/edit modes (matches CharacterBuilder pattern)

### Relationships: Consistent Required Markers

- Add `*` to "From" and "To" character selects and "Relationship Type"
- Keep existing `*` on "Summary"

## Implementation Plan

### Task 1: CharacterBuilder — Fix `canSave`, add section grouping
- File: `frontend/src/components/characters/CharacterBuilder.tsx`
- Change `canSave` to require only 3 fields: `character_id`, `display_name`, `role_in_story`
- Reorganize into 5 sections with collapsible panels for sections 3-5
- Add required/recommended/optional visual indicators

### Task 2: WorldBibleEntryEditor — Add field grouping and badges
- File: `frontend/src/components/bible/WorldBibleWorkspace.tsx`
- Group fields into Core → Canon → Notes sections
- Add "📖 Canon context" badge on `canonical_facts` and `summary`

### Task 3: Relationships — Consistent required markers
- File: `frontend/src/components/characters/RelationshipForm.tsx`
- Add `*` to all required fields

### Task 4: Arcs — Create StudioArcsPanel and ArcBuilder
- New files: `frontend/src/components/studio/StudioArcsPanel.tsx`, `frontend/src/components/characters/ArcBuilder.tsx`
- Follow CharacterBuilder pattern: list → create → edit modes
- Required: `arc_id`, `name`, `summary`. Optional: rest.

### Task 5: Validation
- `cd frontend && npm run lint`
- `cd frontend && npm run typecheck`
- `cd frontend && npm run build`
- `cd frontend && npm run test`
