# Documentation Enhancements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add 7 targeted enhancements to User Guide and Walkthrough docs based on review findings.

**Architecture:** Single-pass edits per task, each self-contained. Tasks 1-3 edit User Guide, tasks 4-7 edit Walkthrough. Task 8 consolidates duplicate content.

**Tech Stack:** Markdown documentation only. No code, no tests.

---

### Task 1: Quick Start section (Walkthrough)

**Files:**
- Modify: `docs/Narrative Engine User Walkthrough v1.8.0.md` — insert before Phase 1

- [ ] **Step 1: Add Quick Start section**

Insert after "Preconditions", before "Frontend Map":

```markdown
## Quick Start: Your First Project in 10 Minutes

1. Open `/` → fill New Project form (name, genre, tone, structure, POV, language) → click **Create Project**
2. Navigate to **Foundation** tab → fill Premise and Logline → click **Save Foundation**
3. Navigate to **Characters** tab → click **Add Character** → create one protagonist → click **Save Character**
4. Open Job Launch panel (right rail) → select **P-100 Architect** → click **Launch** → wait for completion
5. Select **P-300 Drafter** → click **Launch** → wait for completion → view generated chapter in Writing workspace

For a complete walkthrough with 12 chapters, 7 characters, and branching, see Phase 11.
```

- [ ] **Step 2: Verify** — section appears before Phase 1, under Preconditions

### Task 2: Consolidated Auth section (User Guide)

**Files:**
- Modify: `docs/User Guide v1.8.0.md` — add new section, remove inline mentions

- [ ] **Step 1: Add Authentication section**

Insert after "API/Auth Notes For Users", replace existing section:

```markdown
## Authentication

If the backend is configured with `NARRATIVE_API_KEY`, the following features require a matching API key:

- **Brain Dump** — session creation, AI organize
- **Canon Workshop** — all four tabs (overview, mythos, patterns, packet)
- **Story Generation** — wizard submission, run monitoring
- **Manuscript Assist** — floating toolbar actions, assist dropdown

When API key is required but not configured, the view shows a guidance banner at the top with setup instructions. To configure:
1. Generate an API key via `POST /v1/auth/keys` or the API key management interface.
2. Include the key in requests as configured by your backend (typically `Authorization: Bearer <key>` header).
3. For development, set `NARRATIVE_API_KEY` to an empty string to disable auth entirely.
```

- [ ] **Step 2: Remove inline auth mentions**

Remove "Auth Behavior" subsection from Brain Dump section (lines ~179-181) and Canon Workshop section (lines ~310-312).

- [ ] **Step 3: Verify** — auth info appears once, inline mentions removed

### Task 3: Feature dependency map (User Guide)

**Files:**
- Modify: `docs/User Guide v1.8.0.md` — insert after "Workspace Shell Behavior"

- [ ] **Step 1: Add dependency table**

Insert after "Mode navigation is stage-aware..." paragraph:

```markdown
### Feature Dependencies

Some features require upstream data before they can be used:

| Feature | Requires |
|---------|----------|
| P-100 Architect | Foundation populated |
| P-200 Sequencer | P-100 output (sequence plan) |
| P-300 Drafter | P-200 output + at least 1 character |
| P-400 Compiler | P-300 output (draft artifacts) |
| Cascade Discovery | 2+ characters + generated chapter content |
| Story Generation | 1+ character in canon scope + non-empty brief |
| Manuscript Assist | Existing manuscript content + text selection |
| Checker | At least 1 completed run or checker execution |
| Inspect deep link | Valid job ID or checker run ID |
| Project Export | At least 1 manuscript or draft artifact |
```

- [ ] **Step 2: Verify** — table renders correctly, dependencies are accurate

### Task 4: Studio Desk workflow example (Walkthrough Phase 10)

**Files:**
- Modify: `docs/Narrative Engine User Walkthrough v1.8.0.md` — insert after "Using the Desk" steps

- [ ] **Step 1: Add concrete workflow scenario**

Insert after step 6 in "Using the Desk":

```markdown
### Example Workflow: Writing with Context

1. Open Studio Desk for your project.
2. In the Project Map (left rail), select **Characters** — character list appears in left panel.
3. Click **Write** in the command bar — Suggestions panel opens in the right panel.
4. In the center editor, select a paragraph and use the floating toolbar → `Sight & color`.
5. Review the suggestion in the right panel. Accept to apply, or reject.
6. Mid-chapter, click **Capture** to switch the right panel to Ideas. Type a new plot idea.
7. Click **Write** again to return to Suggestions. Continue editing.
8. When done, click **Generate** to open the compact generation panel. Configure and launch a new generation run without leaving the desk.
```

- [ ] **Step 2: Verify** — scenario flows logically, references actual UI elements

### Task 5: Error recovery in novel walkthrough (Walkthrough Phase 11)

**Files:**
- Modify: `docs/Narrative Engine User Walkthrough v1.8.0.md` — insert after Steps 9, 10, 11

- [ ] **Step 1: Add error recovery for each Act generation**

After Step 9 (Generate Act I), add:
```markdown

#### If Act I generation fails:
- **INFERENCE_TRUNCATED:** Reduce Chapter Count to 2, generate Ch 1-2, then Ch 3-4 in a second run. Increase `NARRATIVE_MAX_TOKENS_DRAFTER=16000` in `.env`.
- **Canon contradiction (gate failure):** Check gate results panel. Relax continuity strictness to `Warn` or fix the conflicting canon entry.
- **Generic/flat output:** Improve generation brief with specific voice instructions. Add more world bible entries for richer context.
```

After Step 10 (Generate Act II), add:
```markdown

#### If Act II generation fails:
- **Packet too large:** Split Act II into two runs (Ch 5-6, Ch 7-8). Use prior chapter summaries for context continuity.
- **Character voice drift:** Check Moreau's Voice Notes field. Annotate it in Characters tab for strict enforcement. Re-run with `Block` continuity.
- **AURA-7 dialogue not uncanny enough:** Add specific instruction to generation brief: "AURA-7's speech is fragmented, with random pauses and occasional garbled words. It should feel like talking to a broken radio."
```

After Step 11 (Generate Act III), add:
```markdown

#### If Act III generation fails:
- **Ambiguity lost in ghost fleet:** Add to generation brief: "Do NOT confirm or deny whether the ghost fleet is real. End on ambiguity."
- **Kai's emotional impact weak:** Add Kai's relationship edge to canon scope. Increase Kai's presence in generation brief.
- **Branch comparison takes too long:** Generate main branch first. Only create alternate branch if the ending feels unsatisfactory.
```

- [ ] **Step 2: Verify** — each recovery section follows its corresponding generation step

### Task 6: Common mistakes section (Walkthrough)

**Files:**
- Modify: `docs/Narrative Engine User Walkthrough v1.8.0.md` — insert after Phase 12, before Phase 13

- [ ] **Step 1: Add Common Mistakes section**

Insert as new section:

```markdown
## Common Mistakes and Fixes

- **"I clicked Generate but nothing happened"** — The generation brief is empty or no canon entities are selected. Both are required to enable "Start Generation".
- **"My characters don't appear in the generated output"** — Characters must be selected in the canon scope (Canon Workshop Overview tab or Generation wizard). Being created in the project is not enough.
- **"Suggestions panel is empty"** — You must select text in the editor and trigger an assist action (floating toolbar or Assist dropdown). The panel doesn't auto-populate.
- **"Project won't export"** — The project needs at least 1 manuscript or draft artifact. Run P-300 Drafter or promote a draft to manuscript first.
- **"Cascade scan returns no entities"** — Manuscript text must be at least 50 characters and contain character names, interactions, or descriptive details. Very short or sparse text yields no results.
- **"Inspect shows 'run not found'"** — The job ID in the URL must match an existing checker run or pipeline job. Navigate from Review → Inspect Run Links or the Job Launch panel to get valid IDs.
- **"Checker finds no findings"** — The checker needs completed runs to analyze. Run at least one pipeline job (P-100 through P-400) before expecting findings.
```

- [ ] **Step 2: Verify** — each mistake has a clear cause and fix

### Task 7: Phase 13 concrete examples (Walkthrough)

**Files:**
- Modify: `docs/Narrative Engine User Walkthrough v1.8.0.md` — expand Phase 13

- [ ] **Step 1: Add example to each pattern**

Replace Phase 13 content:

```markdown
## Phase 13: Advanced Iteration Patterns

### Pattern A: Canon-tight revision loop
1. Write draft.
2. Checker review.
3. Inspect root causes.
4. Annotate canon fields.
5. Re-run generation.

**Example:** You wrote Ch 5. Checker finds Elara's voice drifted in paragraph 3 (too casual for the established sparse, atmospheric tone). Navigate to Characters → Elara Voss → annotate Voice Notes field for strict enforcement. Re-run P-300 for Ch 5 with `Block` continuity strictness. Checker passes on re-run.

### Pattern B: Alternate story exploration
1. Create branch.
2. Draft alternate variants.
3. Compare and decide.
4. Merge preferred direction.

**Example:** Act III ending feels rushed. Create branch `Act III - Extended`. Generate Ch 11-12 with additional world bible entries (Echo Point interior, Reyes's ship log). Compare branch output against main branch using branch comparison tool. Extended version has better pacing. Merge `Act III - Extended` into main.

### Pattern C: Forked sequel workflow
1. Select successful generation run.
2. Fork to new project.
3. Re-open planning and writing in fork.
4. Repeat quality loop.

**Example:** Act I-III of *The Last Lighthouse* is complete. Select the final generation run → click "Fork Project from Run" → name new project *The Last Lighthouse: Sequel*. Open fork → update Foundation with sequel premise → add new characters (Kai Voss arrives at the beacon) → generate sequel chapters with Act III canon as grounding context.
```

- [ ] **Step 2: Verify** — each pattern has 5 steps + concrete example

### Task 8: Consolidate duplicate workflow (Walkthrough)

**Files:**
- Modify: `docs/Narrative Engine User Walkthrough v1.8.0.md` — replace Phase 12

- [ ] **Step 1: Replace Phase 12 with cross-reference**

Replace Phase 12 content:

```markdown
## Phase 12: Full Production Workflow

For the complete production workflow order, see **End-to-End Recommended Workflow** in the [User Guide v1.8.0](User%20Guide%20v1.8.0.md). The walkthrough's Phase 11 demonstrates this workflow across a full 12-chapter novel with multi-arc planning, branching, and canon management.
```

- [ ] **Step 2: Verify** — User Guide's "End-to-End Recommended Workflow" still contains the full 14-step list

---

**Verification:** Visual review of each section for accuracy, consistency with actual UI, and no cross-reference loops.
