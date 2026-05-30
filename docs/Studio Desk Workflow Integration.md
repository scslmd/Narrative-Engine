# Studio Desk Workflow Integration — Recommendations

## Overview

The Studio Desk left rail currently shows 6 stage sections (Ideation, Planning, Research, Drafting, Revision, Polish) with panel items. This document recommends enhancements to make the writing workflow visible, trackable, and navigable.

## Recommendations

### 1. Writing Progress Indicator (High Priority)

**What:** Compact progress visualization at the top of the left rail showing current stage position in the 6-stage workflow.

**Why:** Authors need to know where they are in the writing process at a glance. The research shows authors loop between stages — a progress indicator makes non-linear navigation intentional rather than accidental.

**Design:**
- Horizontal row of 6 numbered dots (1-6)
- Completed stages: filled green dot
- Current stage: blue dot with glow
- Upcoming stages: empty outlined dots
- Connecting lines between dots (filled for completed, empty for upcoming)
- Label below: "Stage 4 of 6 — Drafting"
- Click any dot to scroll rail to that stage section

**Implementation:**
- New component: `StudioWorkflowProgress`
- Props: `currentStage: number` (derived from active panel)
- State: track which stages have been visited (localStorage persistence)
- Mount: top of `StudioProjectRail`, below header

### 2. Stage-Colored Active States (Medium Priority)

**What:** Active panel gets a left accent bar colored to match its stage.

**Why:** Visual reinforcement of which stage the user is working in. The 6 stage colors already exist in the research (blue, purple, cyan, green, orange, pink).

**Design:**
- 3px left bar on active rail item
- Color matches stage color
- Subtle background tint on active item (e.g., `rgba(59, 130, 246, 0.1)` for blue)

**Implementation:**
- CSS in `StudioProjectRail.tsx`
- Existing `.active` class gets `::before` pseudo-element with stage color
- Each `.stage-N` section defines its own color

### 3. Entity Count Badges (Medium Priority)

**What:** Small count badges on rail items showing how many entities exist in each panel.

**Why:** Authors need visibility into project scope without opening every panel. A badge showing "Characters · 7" or "Chapters · 12" provides at-a-glance project health.

**Design:**
- Right-aligned badge on rail item
- Small pill: `font-size: 10px`, `padding: 1px 6px`, `border-radius: 999px`
- Background: `rgba(255,255,255,0.08)`, text: `var(--text-muted)`
- Only show badge if count > 0

**Implementation:**
- Each panel component already has entity count from React Query
- Pass count as prop to rail item (or derive from store)
- Badge component: `RailItemBadge` (or inline)
- For panels that don't have counts (Research, Notes, Ideas), omit badge

### 4. Stage Quick-Jump Navigation (Low Priority)

**What:** Click the stage header to expand/collapse that stage section.

**Why:** When working in a specific stage, collapsing other stages reduces rail clutter. Useful for focused drafting sessions.

**Design:**
- Stage header is clickable
- Default: all expanded
- Click: collapse/expand that section
- State persists in localStorage

**Implementation:**
- Add `expanded` state to each rail section
- Toggle on header click
- CSS transition for expand/collapse animation

## Priority Order

| Priority | Feature | Effort | Impact |
|----------|---------|--------|--------|
| High | Writing Progress Indicator | Medium | High — core workflow visibility |
| Medium | Stage-Colored Active States | Low | Medium — visual clarity |
| Medium | Entity Count Badges | Medium | Medium — project scope visibility |
| Low | Stage Quick-Jump | Low | Low — nice-to-have |

## Files to Modify

| File | Changes |
|------|---------|
| `StudioProjectRail.tsx` | Add progress indicator, stage colors, badges, expand/collapse |
| `studioStore.ts` | Track visited stages, expanded sections |
| `StudioWorkflowProgress.tsx` (new) | Progress indicator component |
| `StudioView.tsx` | Wire progress indicator to active panel |

## Acceptance Criteria

- Progress indicator shows correct stage based on active panel
- Clicking a progress dot scrolls rail to that stage section
- Active panel has stage-colored left accent bar
- Entity count badges show correct counts
- Stage sections can be expanded/collapsed
- State persists across page refresh via localStorage
- No regression in existing rail behavior