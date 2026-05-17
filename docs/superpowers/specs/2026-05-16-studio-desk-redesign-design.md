# Studio Desk Redesign - Concept A

Date: 2026-05-16
Scope: Frontend UI/UX only. Reuse existing backend routes, frontend services, hooks, and components. Do not invent backend features.

## Product Intent

Concept A, "Studio Desk", turns Narrative Engine from a route-driven feature collection into a single writing workspace. The writer should spend most of the session in one place, with the manuscript or current creative artifact in the center and supporting tools sliding in only when needed.

The redesign is based on the repo's writing-software research:

- Scrivener: persistent project map plus editor plus inspector.
- Sudowrite: AI actions close to selected text, not separated into a dashboard.
- Campfire: worldbuilding and character modules are useful, but should be contextual instead of navigation-heavy.
- Plottr: visual planning is useful as an overview, but should not dominate drafting.
- Novel Factory: guided flow helps users understand process order.
- Ulysses/Reedsy: focused editor surface should stay calm and low-friction.

Narrative Engine's differentiator is not that it has more panels. It is that canon, generation, review, inspect, and lineage are available at the moment the writer needs them.

## Current Friction

The current workspace exposes capability by backend domain:

```text
/workspace/:projectId/braindump
/workspace/:projectId/plan
/workspace/:projectId/canon
/workspace/:projectId/generate
/workspace/:projectId/write
/workspace/:projectId/review
/workspace/:projectId/inspect
```

This makes implementation boundaries visible to the user. The writer must jump between routes for one natural loop:

```text
Capture idea -> structure it -> enrich canon -> generate -> edit -> review -> inspect -> revise
```

Specific friction points:

- Brain Dump and Brainstorm are separated even though both are idea capture/refinement.
- Character, World Bible, Relationships, Foundation, and Canon are split between Planning and Canon screens.
- Generation is a separate workspace even when the user is generating from manuscript context.
- Review and Inspect require route changes when they are usually support tasks for a current draft or generation run.
- Notes and jobs exist as utility surfaces but are not treated as first-class workflow panels.

## Proposed UX Model

The Studio Desk has one primary route:

```text
/workspace/:projectId/studio
```

The old routes remain available during transition. Studio becomes the default destination once stable.

### Layout

```text
+--------------------------------------------------------------------------------+
| Studio command bar: Capture | Write | Generate | Review | Inspect | Search      |
+------------+---------------------------------------------------+---------------+
| Project    |                                                   | Context       |
| Map        |              Active Work Surface                  | Panel Stack   |
|            |                                                   |               |
| Manuscripts|              Editor / selected surface            | Ideas         |
| Drafts     |                                                   | Characters    |
| Plans      |                                                   | World Bible   |
| Canon      |                                                   | Relationships |
| Jobs       |                                                   | Canon Scope   |
|            |                                                   | Generation    |
+------------+---------------------------------------------------+---------------+
| Bottom utility tray: jobs, suggestions, inspect logs, lineage, runtime status    |
+--------------------------------------------------------------------------------+
```

### Panel Behavior

The center surface should remain stable. Opening tools should not replace the center unless the user explicitly changes active work.

Panel rules:

- Left rail is for navigation within project artifacts.
- Right rail is for contextual support.
- Bottom tray is for runtime/status/provenance.
- Modals are reserved for destructive confirmation or dense existing forms that are already modal.
- Route changes should represent shareable location, not ordinary support-panel use.

### Writer Loop

```text
1. Capture
   Quick note, brain dump session, or brainstorm item.

2. Shape
   Promote idea into existing planning, foundation, character, world bible, or relationship surfaces.

3. Scope
   Choose existing canon/profile/generation context.

4. Generate
   Launch existing P-100/P-200/P-300/P-400 or story generation wizard from the Studio panel.

5. Edit
   Use the existing manuscript editor and manuscript assist actions.

6. Review
   Open existing suggestions, findings, checker results, and inspect links without leaving Studio.

7. Iterate
   Keep drafts, generated runs, decisions, and jobs visible as working material.
```

## Visual Direction

The UI should feel utilitarian, modern, and quiet. It should not look like a marketing dashboard.

Recommended visual language:

- Dense but legible workspace chrome.
- Muted slate/ink base with strong but sparse accent colors.
- Clear active-panel affordances.
- Sliding panels with visible handles and pinned/unpinned states.
- Command bar uses verbs, not feature names.
- Center editor gets the most whitespace.
- Jobs and AI actions feel operational, not decorative.

## Detailed Wireframes

### Default Studio

```text
┌────────────────────────────────────────────────────────────────────────────────┐
│ Narrative Engine / Project Name                                                │
│ [Capture] [Write] [Generate] [Review] [Inspect]        Active: Chapter 3 Draft │
├──────────────┬──────────────────────────────────────────────┬──────────────────┤
│ PROJECT MAP  │ EDITOR                                       │ CONTEXT          │
│              │                                              │                  │
│ Manuscripts  │ Chapter title                                │ Open panel:      │
│  > Chapter 1 │                                              │ Suggestions      │
│  > Chapter 2 │ It was not the storm that changed Mara...    │                  │
│  > Chapter 3 │                                              │ 3 open aids      │
│              │                                              │ 1 canon warning  │
│ Drafts       │ [selected text toolbar appears near text]    │                  │
│  alt opening │                                              │ [Accept] [Reject]│
│  variant b   │                                              │                  │
│              │                                              │ Panel tabs:      │
│ Planning     │                                              │ Ideas Characters │
│ Canon        │                                              │ World Canon Gen  │
│ Jobs         │                                              │ Review Inspect   │
└──────────────┴──────────────────────────────────────────────┴──────────────────┘
│ Jobs tray: P-300 PROCESSING | latest checker COMPLETED | logs collapsed         │
└────────────────────────────────────────────────────────────────────────────────┘
```

### Generate From Context

```text
┌──────────────┬──────────────────────────────────────────────┬──────────────────┐
│ PROJECT MAP  │ EDITOR                                       │ GENERATION       │
│              │                                              │                  │
│ Manuscripts  │ Current manuscript remains visible.           │ Existing wizard  │
│ Drafts       │ User can reference text while setting scope.  │ in compact panel │
│              │                                              │                  │
│              │                                              │ Canon scope      │
│              │                                              │ Chapter count    │
│              │                                              │ Brief            │
│              │                                              │ [Preview Fork]   │
│              │                                              │ [Start]          │
└──────────────┴──────────────────────────────────────────────┴──────────────────┘
```

### Review Without Leaving Writing

```text
┌──────────────┬──────────────────────────────────────────────┬──────────────────┐
│ PROJECT MAP  │ EDITOR                                       │ REVIEW           │
│              │                                              │                  │
│              │ Paragraph with highlighted issue.             │ Findings         │
│              │                                              │ - severity high  │
│              │                                              │ - affected char  │
│              │                                              │ - inspect link   │
│              │                                              │                  │
│              │                                              │ [Open Inspect]   │
│              │                                              │ [Mark decision]  │
└──────────────┴──────────────────────────────────────────────┴──────────────────┘
│ Inspect tray expanded: Steps | Lineage | Attempts                               │
└────────────────────────────────────────────────────────────────────────────────┘
```

## Frontend Architecture

The first implementation should be additive and reversible:

- Add `studio` to `WorkspaceMode`.
- Add `/workspace/:projectId/studio` route.
- Add `StudioView` as an opt-in route.
- Reuse existing components inside Studio panels.
- Do not remove existing routes.
- Do not rewrite `WritingView`, `PlanningView`, `CanonView`, `GenerationView`, `ReviewView`, or `InspectView` in the first pass.

### New Frontend Units

```text
frontend/src/views/StudioView.tsx
frontend/src/components/studio/StudioCommandBar.tsx
frontend/src/components/studio/StudioProjectRail.tsx
frontend/src/components/studio/StudioContextPanel.tsx
frontend/src/stores/studioStore.ts
```

### Existing Components To Reuse

```text
NotesPanel
JobLaunchPanel
BottomUtilityLayer
BrainDumpCanvas / BrainDumpView as optional future extraction
BrainstormWorkspace
CharacterBuilder
WorldBibleWorkspace
RelationshipMapGraph / RelationshipList
CanonWorkshop
GenerationView or generation subcomponents
WritingView or manuscript subcomponents
ReviewView
InspectView
```

The first pass should not attempt deep component extraction from large existing views. Use route-level composition where possible and only extract smaller components when a panel needs a focused existing surface.

## Non-Goals

- No backend API changes.
- No new story-generation capability.
- No new LLM prompt design.
- No new database fields.
- No export redesign.
- No mobile-specific redesign beyond responsive collapse behavior.
- No removal of existing routes during first implementation.

## Success Criteria

- User can open `/workspace/:projectId/studio`.
- Studio shows one stable center workspace with command bar, project rail, context panel, and bottom utility tray.
- Existing writing, notes, jobs, generation, review, inspect, planning, canon, and idea surfaces are reachable without replacing the whole app shell.
- Existing routes still work.
- Frontend lint, typecheck, build, and test pass.
