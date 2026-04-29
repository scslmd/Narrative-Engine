# Prompt Optimization Review — Extraction & Generation

**Date:** 2026-04-27
**Scope:** All LLM prompts in the extraction, generation, and critic pipeline
**Files reviewed:**
- `app/services/runtime_prompts.py` (9 prompt builders)
- `app/services/scene_context.py` (SceneContext.to_prompt_string)
- `app/services/consistency_critic.py` (critic prompt via build_critic_check_request)
- `app/services/entity_intake.py` (intake prompt via build_entity_intake_request)
- `app/services/chapter_summarizer.py` (summarizer prompt via build_chapter_summarize_request)

---

## Prompt Inventory

| # | Builder | Target | Temperature | Max Tokens | Purpose |
|---|---------|--------|-------------|------------|---------|
| 1 | `build_import_analysis_request` | Story Import | 0.1 | 16,000 | Analyze completed story → structured JSON |
| 2 | `build_narrative_analysis_request` | Pattern Extraction (narrative) | 0.1 | 16,000 | Extract storytelling DNA → structured JSON |
| 3 | `build_mythos_analysis_request` | Pattern Extraction (mythology) | 0.1 | 16,000 | Extract archetypal patterns → structured JSON |
| 4 | `build_p100_architect_request` | P-100 Architect | 0.2 | 1,200 | Build story foundation as markdown |
| 5 | `build_p200_sequencer_request` | P-200 Sequencer | 0.2 | 1,200 | Build sequence plan as JSON |
| 6 | `build_p300_drafter_request` | P-300 Drafter | 0.2 | 8,000 | Draft chapter as markdown |
| 7 | `build_p400_compiler_request` | P-400 Compiler | 0.1 | 1,400 | Build story bible snapshot as JSON |
| 8 | `build_brain_dump_organize_request` | Brain Dump | 0.1 | 4,096 | Categorize brain dump items |
| 9 | `build_critic_check_request` | Consistency Critic | 0.1 | 2,048 | Check draft vs character profiles |
| 10 | `build_entity_intake_request` | Entity Intake | 0.2 | 512 | Extract new character profiles |
| 11 | `build_chapter_summarize_request` | Chapter Summarizer | 0.1 | 2,000 | Summarize chapter for context propagation |
| 12 | `SceneContext.to_prompt_string()` | P-300 context injection | (uses P-300 temp) | (uses P-300 max) | Inject character/world/context into drafter prompt |

---

## 1. JSON STRUCTURE PROMPTS (Tasks 1, 2, 3, 7, 8)

### 1.1 Current Strengths

All JSON-structured prompts follow best practices:
- Explicit key names listed in the system prompt
- Enum values specified with exact strings
- "Return ONLY the JSON object. No markdown, no explanation" instruction
- Validation checklist (story import)
- Temperature 0.1 for deterministic output

### 1.2 Issues Found

#### ISSUE 1: Redundant "No markdown" instructions

All four JSON prompts (story import, narrative, mythos, brain dump) end with:
```
"CRITICAL: Return ONLY the JSON object. No markdown, no explanation, no code blocks."
```

This is repeated 4 times with slight variations:
- Story import: "No markdown, no explanation, no code blocks."
- Narrative: "No markdown, no explanation, no code blocks."
- Mythos: "No markdown, no explanation, no code blocks."
- Brain dump: "CRITICAL: Return ONLY the JSON object. No markdown, no explanation, no code blocks."
- Critic: "Return ONLY a JSON object"
- Entity intake: "Return ONLY a JSON object"

**Problem:** The "no markdown" instruction is ineffective because the parser already handles markdown fences. The repetition wastes prompt tokens (each prompt is already ~1,000-2,000 tokens). The real issue is that LLMs sometimes add conversational framing ("Here is the analysis:\n\n") which the parser handles via JSON extraction.

**Fix:** Replace with a single, more effective instruction that addresses the actual failure mode:
```
OUTPUT FORMAT — Return a single, valid JSON object. No text before or after the JSON.
```

This is shorter (saves ~15 tokens per prompt) and more precise.

#### ISSUE 2: Story Import Prompt is Too Dense

The story import system prompt (lines 228-335) is ~107 lines of hardcoded JSON structure. It's the longest prompt in the codebase. Problems:
- The JSON template is verbose (100+ lines of structure description)
- POV/Structure guides add another 20+ lines
- Field value rules add 10+ lines
- Character extraction rules add 5+ lines
- Validation checklist adds 7+ lines
- Critical rules add 5+ lines

**Total estimated token count: ~2,500 tokens for a ~300-line system prompt.**

**Fix:** Condense using structured sections and remove redundancy:
```python
system_prompt = (
    "You are a story analysis AI for Narrative-Engine.\n\n"
    "Return a JSON object with EXACTLY these keys and NO others:\n"
    "project_name, genre, tone, pov, story_structure, premise, logline, "
    "thematic_spine, emotional_promise, target_audience, complexity_level, "
    "characters, world_bible, story_arcs, sequences, narrative_constraints, "
    "success_definition, raw_story_text\n\n"
    "Enum constraints (use EXACTLY these values):\n"
    "  pov: FIRST|SECOND|THIRD_LIMITED|THIRD_OMNI|THIRD_OBJECTIVE|THIRD_MULTIPLE|OTHER\n"
    "  story_structure: SAVE_THE_CAT|THREE_ACT|HERO_JOURNEY|FREYTAGS_PYRAMID|...|OTHER\n"
    "  complexity_level: LOW|MEDIUM|HIGH\n"
    "  role: protagonist|antagonist|mentor|deuteragonist|foil|supporting|minor\n\n"
    "Array rules — ALL of these must be JSON arrays [] even if empty:\n"
    "  characters[].{name,role,archetype,...,contradictions[],secrets[],values[],...}\n"
    "  world_bible[].{entry_type,title,summary,canonical_facts[],related_character_ids[]}\n"
    "  story_arcs[].{name,summary,stage_map[],tags[]}\n"
    "  sequences[].{title,summary,chapters[]}\n"
    "  narrative_constraints[]\n\n"
    "Key naming: world_bible uses entry_type+title (NOT name/description). "
    "story_arcs uses summary (NOT description), stage_map, tags (NOT type). "
    "sequences uses title (NOT name), summary (NOT description).\n\n"
    "CHARACTER RULES: Include every meaningful character. Use descriptive names for unnamed ones. "
    "Correctly identify protagonist (drives plot) and antagonist (opposes).\n\n"
    "OUTPUT — Single valid JSON object. No text before or after."
)
```

This reduces the system prompt from ~2,500 to ~900 tokens — a 64% reduction. The actual content (enum values, field rules, validation instructions) is preserved but denser.

#### ISSUE 3: Narrative and Mythos Prompts Lack "What If I Don't Know" Guidance

Both narrative and mythos analysis prompts (Tasks 2 & 3) don't explicitly state what to do when the LLM can't determine a field. The story import prompt handles this well: "If you cannot infer a value, use empty string '' for strings or [] for arrays."

**Fix:** Add this clarification to both prompts:
```
MISSING DATA: Use empty strings "" for optional string fields you cannot determine.
Use empty arrays [] for array fields. Do not omit keys.
```

#### ISSUE 4: Narrative Prompt Doesn't Validate Entity Relationships Format

The narrative analysis prompt specifies `entity_relationships` as an array of objects with `source`, `target`, `relationship_type`, `description`. But the `_build_analysis` method (pattern_extraction.py:379-388) treats these as `Relationship` objects which are imported from `mythos_extraction.py` schemas. The `source` and `target` fields here refer to entity *names* (strings), not IDs. This is ambiguous in the prompt.

**Fix:** Clarify in the prompt:
```
entity_relationships: Array of objects with "source" (entity name), "target" (entity name),
"relationship_type" (describes the relationship), "description" (free text).
```

---

## 2. P-100 ARCHITECT PROMPT (Task 4)

### 2.1 Current State

```
system: "You are the Architect role for Narrative-Engine. Produce the P-100 story architecture
        foundation as deterministic markdown. Use these exact headings in order:
        ## Logline, ## Core Premise, ## Story Engine, ## World Anchors,
        ## Character Arcs, ## Constraints, ## Open Questions."
user:   [pattern_context] + [project_context JSON]
```

### 2.2 Issues

#### ISSUE 5: No Output Format Guardrails

Unlike the JSON prompts, the P-100 architect prompt doesn't specify:
- What each heading should contain (length, scope)
- What NOT to include (no preamble, no code blocks)
- How to handle uncertain information

**Fix:** Add explicit output constraints:
```python
system_prompt = (
    "You are the Architect role for Narrative-Engine. Produce the P-100 story architecture
     foundation as deterministic markdown.\n\n"
     "Use these EXACT headings in this EXACT order (no extra headings, no preamble):\n"
     "## Logline\n"          → One sentence, ≤40 words\n"
     "## Core Premise\n"     → 2-4 sentences describing the story's engine\n"
     "## Story Engine\n"     → What drives the plot forward (conflict mechanism)\n"
     "## World Anchors\n"    → 3-5 immutable world facts the story cannot contradict\n"
     "## Character Arcs\n"   → Per-character: starting state → ending state\n"
     "## Constraints\n"      → Rules the story must obey (tone, POV, themes)\n"
     "## Open Questions\n"   → Unresolved questions to guide subsequent chapters\n\n"
     "Return ONLY markdown with these headings. No code fences. No introduction text."
)
```

#### ISSUE 6: Pattern Context Block is Fragile

`_build_pattern_context_block` (lines 426-530) uses `getattr(pc, ...)` everywhere because `pc: Any`. This means:
- If a field is renamed, the prompt builder silently gets `None`
- No IDE autocomplete for field names
- No type checking

**Fix:** Change parameter type to `PatternExtractionAnalysis`:
```python
def _build_pattern_context_block(pc: PatternExtractionAnalysis) -> str:
```

Then use direct attribute access instead of `getattr`:
```python
# Instead of:
mode = getattr(pc, "generation_mode", "same_world") or "same_world"
# Use:
mode = pc.generation_mode or "same_world"
```

#### ISSUE 7: Pattern Context Block Adds Content but Doesn't Specify LLM Behavior

The pattern context block provides raw data but doesn't tell the LLM *what to do with it*. The LLM might just repeat the patterns back rather than integrating them.

**Fix:** Add a clear instruction at the end of each mode block:
```python
# Same world mode:
lines.append("Apply these archetypes, rules, and voice guidelines to the P-100 foundation.")

# New characters mode:
lines.append("Fill these archetypal roles with original characters in this world.")

# Transposed mode:
lines.append("Map each pattern and structure to an equivalent in your new setting.")
```

---

## 3. P-300 DRAFTER PROMPT (Task 6)

### 3.1 Current State

```
system: "You are the Drafter role for Narrative-Engine. Produce the P-300 {chapter_label} draft
        as deterministic markdown. Preserve chapter flow, continuity, and stable section ordering."
user:   [scene_context.to_prompt_string()] + [project_context JSON]
```

### 3.2 Issues

#### ISSUE 8: No Chapter Length or Style Guidance

The P-300 prompt doesn't specify:
- Target chapter length
- Style guidelines (prose density, dialogue ratio)
- How to handle pacing

**Impact:** Chapters may vary wildly in length and quality across a book.

**Fix:** Add to system prompt:
```
TARGET LENGTH: Write {target_word_count} words (±10%).
PACING: Match the pacing profile from the architect foundation.
CONTINUITY: Maintain character consistency with the profiles below.
```

(The `{target_word_count}` would be injected from payload or manifest config.)

#### ISSUE 9: Scene Context Injection is Fragile

In `local_executor.py:1118-1128`, the scene context is injected by creating a new `InferenceMessage`:
```python
new_messages = list(inference_request.messages)
new_messages[1] = InferenceMessage(
    role=new_messages[1].role,
    content=f"{existing_content}\n\n{context_prompt}",
)
inference_request = inference_request.model_copy(update={"messages": new_messages})
```

**Problems:**
1. Uses index-based access (`new_messages[1]`) — brittle if message count changes
2. String concatenation on large prompts can create memory issues
3. No length limiting on the injected context — if SceneContext is very long, the user content grows

**Fix:** Use a more robust approach:
```python
context_str = scene_context.to_prompt_string()
if context_str:
    # Append context after project JSON, before final instruction
    user_msg = inference_request.messages[1]
    # Split at the JSON boundary and insert context
    separator = "Build the P-300 drafter foundation"
    parts = user_msg.content.split(separator)
    if len(parts) == 2:
        user_msg = InferenceMessage(
            role=user_msg.role,
            content=f"{parts[0]}\n\n{context_str}\n\n{separator}{parts[1]}",
        )
    inference_request = inference_request.model_copy(update={
        "messages": [inference_request.messages[0], user_msg],
    })
```

But the current approach works. The real issue is **prompt bloat** — when SceneContext accumulates many characters, world facts, and prior chapters, the user content can exceed token limits.

#### ISSUE 10: Pattern Guidance Rendering is Redundant

`SceneContext.to_prompt_string()` (scene_context.py:49-110) renders pattern guidance in a flat text format:
```
PATTERN GUIDANCE:
Voice style: X, sentence rhythm: Y, descriptive density: Z
World rules:
  - Rule 1
  - Rule 2
Thematic constraints:
  - Theme 1
  - Theme 2
```

This is fine but could be more structured. The voice profile rendering (lines 84-94) joins all voice fields with `, ` on a single line, which makes it hard for the LLM to parse individual fields.

**Fix:** Render each voice profile field on its own line:
```python
if pg.voice_profile:
    vp = pg.voice_profile
    lines.append("Voice Profile:")
    if vp.narrative_voice:
        lines.append(f"  - narrative voice: {vp.narrative_voice}")
    if vp.sentence_rhythm:
        lines.append(f"  - sentence rhythm: {vp.sentence_rhythm}")
    # ... etc
```

---

## 4. CONSISTENCY CRITIC PROMPT (Task 9)

### 4.1 Current State

```python
system_prompt = (
    "You are a consistency critic for Narrative-Engine. "
    "Check whether each character's dialogue and actions match their profile.\n\n"
    "Return ONLY a JSON object with these keys:\n"
    '{\n  "passed": true or false,\n  "violations": [\n'
    '    {"character": "<name>", "issue": "<what is wrong>", "suggestion": "<how to fix>"}\n'
    '  ]\n}\n\n'
    "If the character behaves consistently with their profile, set passed=true and violations=[].\n"
    "Check: voice (word choice, sentence style), behavior (goals, fears, traits), knowledge (what they should know)."
)
```

### 4.2 Issues

#### ISSUE 11: Critic Prompt is Too Brief

The critic prompt lacks:
- Specific criteria for what constitutes a violation vs. creative choice
- Guidance on how to distinguish "out-of-character" from "in-character development"
- Weight guidance (which violations are critical vs. minor)

**Fix:**
```python
system_prompt = (
    "You are a consistency critic for Narrative-Engine. "
    "Check whether characters' dialogue and actions align with their defined profiles.\n\n"
    "Return ONLY a JSON object:\n"
    '{\n  "passed": true/false,\n  "violations": [\n'
    '    {"character": "name", "issue": "description", "suggestion": "fix"}\n'
    '  ]\n}\n\n'
    "CHECK FOR:\n"
    "  1. VOICE: Does word choice, sentence length, and vocabulary match the character?\n"
    "  2. BEHAVIOR: Do goals, fears, and traits drive the character's actions?\n"
    "  3. KNOWLEDGE: Does the character only know what they should know?\n"
    "  4. CONFLICT: Is the character's stance consistent with their values?\n\n"
    "NOT VIOLATIONS:\n"
    "  - Natural character growth or emotional shifts (these are arc progressions)\n"
    "  - Understatement or subtlety (not all feelings are expressed openly)\n"
    "  - Cultural or background-appropriate behavior differences\n\n"
    "Only flag CLEAR contradictions between profile and draft. Be conservative."
)
```

#### ISSUE 12: Critic Rewrite Prompt is Weak

In `local_executor.py:1181`, the rewrite prompt is:
```
"You are a narrative editor. Rewrite only the flagged passages to fix consistency issues
while preserving story flow."
```

This is too vague. The rewrite LLM call receives the full draft plus violations but doesn't know:
- Where the violations occur in the text
- How severe the violations are
- Whether to preserve dialogue, descriptions, or both

**Fix:** Include violation locations (line numbers or surrounding context) in the rewrite prompt. Currently this isn't implemented — the critic only returns character name, issue, and suggestion.

---

## 5. ENTITY INTAKE PROMPT (Task 10)

### 5.1 Current State

```python
system_prompt = (
    "You are an entity extraction AI for Narrative-Engine. "
    "From the draft passage below, extract a character profile for the named character.\n\n"
    "Return ONLY a JSON object with these keys:\n"
    '{\n  "name": "<string>",\n  "archetype": "<string>",\n  "goal": "<string>"\n}\n\n'
    "Infer archetype and goal from the character's dialogue, actions, and behavior in the passage."
)
```

### 5.2 Issues

#### ISSUE 13: Entity Intake is Too Shallow

The intake only extracts 3 fields: `name`, `archetype`, `goal`. But the character profile schema has 20+ fields. The shallow extraction creates skeletal profiles that may miss critical information.

**However:** This is intentional — the intake is a lightweight detection step, not a full profile creation. The "skeletal" nature is by design (see `entity_intake.py` line 1209: `writer_notes=f"Auto-detected from draft: {entity.raw_evidence[:200]}"`).

**Verdict:** No change needed. The prompt matches its purpose.

---

## 6. CHAPTER SUMMARIZER PROMPT (Task 11)

### 6.1 Current State

```python
system_prompt = (
    "You are a chapter summarizer for Narrative-Engine. "
    "Extract structured context from the completed chapter below.\n\n"
    "Return ONLY a JSON object with these keys:\n"
    '{\n  "chapter_id": "<id>",\n  "title": "<title>",\n'
    '  "key_events": ["<event 1>", ...],\n'
    '  "character_states": {"<name>": "<condition>"},\n'
    '  "unresolved_threads": ["<thread 1>"]\n}\n\n'
    "Extract up to 10 key events, 10 character states, and 5 unresolved threads.\n"
    "Focus on plot-critical information for continuity in subsequent chapters."
)
```

### 6.2 Issues

#### ISSUE 14: No Guidance on Event Granularity

The prompt says "up to 10 key events" but doesn't define what counts as "key." This could lead to:
- Too granular: listing every scene transition
- Too coarse: one summary per entire chapter

**Fix:** Add granularity guidance:
```
KEY EVENTS: Major plot turns, character revelations, or pivotal decisions.
Each event should be a single sentence describing WHAT happened and WHY it matters.
```

#### ISSUE 15: Character States Missing Action/Goal Context

`character_states` is `{"name": "condition"}` which is very brief. Better:
```
CHARACTER STATES: {"name": "Current goal + emotional state + key change since last chapter"}
```

#### ISSUE 16: Chapter ID is Redundant

The summarizer prompt includes `chapter_id` in the system prompt's JSON structure, but the chapter_id is already passed as a parameter and known to the caller. This wastes ~50 tokens per summarization call.

**Fix:** Remove `chapter_id` from the expected JSON output. The caller already has it.

---

## 7. BRAIN DUMP ORGANIZER PROMPT (Task 8)

### 7.1 Issues

#### ISSUE 17: Category Definitions are Ambiguous

The brain dump organizer has categories like "theme" and "world_building" which can overlap (e.g., a theme about "corruption" could be world-building or thematic). No guidance on priority or disambiguation.

**Verdict:** Acceptable for a brainstorming tool. The categories are fuzzy by design.

---

## 8. PROMPT COMPARISON TABLE

| Prompt | Current Token Est. | Issue Count | Severity |
|--------|-------------------|-------------|----------|
| Story Import Analysis | ~2,500 | 3 (high) | High — biggest token consumer |
| Narrative Analysis | ~2,000 | 2 (medium) | Medium |
| Mythos Analysis | ~2,000 | 2 (medium) | Medium |
| P-100 Architect | ~400 | 3 (medium) | Medium — affects all generation |
| P-300 Drafter | ~200 + context | 3 (medium) | Medium — chapter quality |
| P-200 Sequencer | ~200 | 0 | Low |
| P-400 Compiler | ~200 | 0 | Low |
| Critic Check | ~300 | 2 (high) | High — affects rewrite quality |
| Entity Intake | ~200 | 0 | Low (intentional) |
| Chapter Summarizer | ~250 | 3 (low) | Low |
| Brain Dump Organizer | ~350 | 0 | Low |
| SceneContext injection | ~100-500 (variable) | 2 (low) | Low |

---

## 9. PROMPT OPTIMIZATION PRIORITIES

### Priority 1: Token Budget Optimization (Quick Wins)

1. **Story Import Prompt Compression** (Task F3) — Reduce from ~2,500 to ~900 tokens
   - Saves ~1,600 tokens per import call
   - All the enum values and field rules can be expressed more concisely
   - Estimated cost savings: 30-40% per import call

2. **Remove Redundant "No markdown" Instructions** — Save ~60 tokens across 4 prompts

### Priority 2: JSON Parse Reliability

3. **Add "What If I Don't Know" Guidance** to narrative/mythos prompts — Prevents hallucinated empty fields
4. **Add JSON Structural Guardrails** (trailing commas, escaping) — Prevents parse failures
5. **Clarify entity_relationships source/target semantics** — Prevents wrong data

### Priority 3: Generation Quality

6. **P-100 Output Format Guardrails** — Prevents extra headings, preamble, code fences
7. **P-300 Length/Style Guidance** — More consistent chapter quality
8. **SceneContext Voice Profile Formatting** — Better LLM parsing of individual fields
9. **Critic Prompt Expansion** — More specific violation criteria, reduces false positives/negatives
10. **Critic Rewrite Prompt Improvement** — Include violation locations for targeted fixes

### Priority 4: Minor Improvements

11. **Chapter Summarizer Granularity Guidance** — Better event extraction
12. **Remove redundant chapter_id from summarizer JSON schema** — Save tokens

---

## 10. ADDITIONAL OBSERVATIONS

### Temperature Analysis

All prompts use temperature 0.1 or 0.2:
- 0.1: import, narrative, mythos, compiler, critic, brainstorm, summarizer — appropriate for structured/deterministic output
- 0.2: architect, sequencer, drafter, entity intake — reasonable for creative tasks that still need some consistency
- 0.2 (P-300 has max_tokens=8000) — This is the highest temperature and longest output. The 0.2 temp is fine for creative drafting.

**Verdict:** Temperature choices are well-calibrated. No changes needed.

### System Prompt Position

All prompts correctly place the system prompt in the `system` role (not as a message). This is the correct FastAPI/InferenceRequest pattern.

### Prompt Versioning

There is no prompt versioning system. If a prompt needs to be updated, all existing generations become "stale." Consider adding a `prompt_version` field to the `metadata` dict in each `InferenceRequest`.

### Prompt Caching

No prompt caching is used. For repeated calls (e.g., multi-chapter drafts with the same manifest), the prompt payload is identical across chapters. Consider prompt caching APIs if the inference backend supports it.

---

## RECOMMENDATIONS SUMMARY

1. **Compress story import prompt** — Biggest ROI (1,600 token savings)
2. **Add JSON structural guardrails to all JSON prompts** — Prevents parse failures
3. **Expand critic prompt** — Reduces false positives in consistency checking
4. **Fix P-100 pattern context type** — Improves maintainability
5. **Add chapter length guidance to P-300** — More consistent output quality
