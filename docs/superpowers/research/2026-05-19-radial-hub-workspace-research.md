# Radial Hub Workspace — Research

Date: 2026-05-19
Scope: Author writing behavior, competitive UX analysis, and workspace design research for the radial hub workspace redesign.

## Author Writing Paths

Research shows authors don't follow one linear process. They enter the writing process at different points based on how they think. A writing tool should adapt to the author's natural flow, not force a single workflow.

### 4 Author Entry Points

| Entry Point | Description | Common Genres | Primary Panels Needed |
|-------------|-------------|---------------|----------------------|
| **Idea-First (Pantser)** | Starts with a concept, scene, or "what if?" — writes organically, discovers story through writing. Most common for beginners and romance writers. | Romance, Literary Fiction | Ideas, Manuscripts, Characters |
| **Character-First** | Builds characters deeply first — their voices, motivations, relationships. Then lets characters drive the plot. Common for literary fiction and character-driven stories. | Literary Fiction, Character-Driven Drama | Characters, Relationships, Arcs, Ideas |
| **Outline-First (Plotter)** | Plans everything — structure, beats, chapter outlines — before writing a word. Common for thrillers, mysteries, and series writers. | Thriller, Mystery, Series Fiction | Structure, Chapters, Generation |
| **World-First** | Builds the world bible first — rules, geography, history, magic systems. Then creates story within that world. Dominant in fantasy and sci-fi. | Fantasy, Science Fiction | World Bible, Characters, Arcs, Structure |

### Key Insight: Authors Don't Work in Straight Lines

Authors naturally move between activities during a writing session:

- Writing a scene → realizing a character needs more backstory → building character → returning to scene
- Drafting chapter 5 → discovering a world rule conflict → updating world bible → returning to chapter
- Planning beats → having a new idea → jumping to brainstorm → coming back to plan

**Design implication:** The workspace must support fluid transitions between activities without losing context. No forced navigation. All tools accessible simultaneously.

## Story Types

Based on The Write Practice's value-based plot types. These represent the fundamental story shapes authors work within:

| Story Type | Core Value Conflict | Story Shape |
|------------|---------------------|-------------|
| **Adventure** | Life vs Death | MacGuffin quest |
| **Action** | Life vs Death | Antagonist driven |
| **Horror** | Life vs Fate Worse Than Death | Dread escalation |
| **Mystery** | Justice | Investigation → confession |
| **Romance** | Love vs Hate | Meet cute → proof of love |
| **Coming of Age** | Maturity vs Immaturity | Revelation |
| **Performance** | Accomplishment vs Failure | Competition |
| **Morality** | Right vs Wrong | Internal battle |
| **Thriller** | Monstrous crime | Hero at villain's mercy |

## Story Frameworks

### Classic Story Structure Elements

All Western story structures share five common elements (Reedsy):

1. **Exposition** — establishes protagonist's normal life and greater desires, culminates in inciting incident
2. **Rising Action** — protagonist pursues new goal, tested along the way
3. **Climax** — hero achieves goal (or so they think)
4. **Falling Action** — hero deals with consequences of achieving goal
5. **Resolution** — conclusion tying together plot, character arcs, and themes

### Built-in Frameworks (Narrative Engine)

Narrative Engine ships with 10 built-in story structure frameworks (defined in `app/schemas/enums.py::StoryStructure`):

| Framework | Origin | Beats | Best For |
|-----------|--------|-------|----------|
| **Save the Cat** | Blake Snyder, 2005 | 15 beats | Screenplay-style pacing, high-concept commercial fiction |
| **Three Act** | Aristotle / Syd Field, 1979 | 3 acts | Universal, beginner-friendly, clear stakes/progression |
| **Hero's Journey** | Joseph Campbell, 1949 / Vogler, 1992 | 12 stages | Mythic, adventure narratives, character transformation |
| **Freytag's Pyramid** | Gustav Freytag, 1863 | 5 parts | Tragedy, classical drama, Shakespearean plays |
| **Kishōtenketsu** | East Asian, ~8th century CE | 4 acts | Non-conflict narratives, contemplative works |
| **Fichtean Curve** | John Gardner, 1970s | Rising crises | Thriller, suspense, serialized fiction |
| **Seven Point Structure** | Dan Wells, 2010 | 7 beats | Character-driven stories, backward planning |
| **Seven Key Steps** | Dan Harmon, 2004 | 8 steps | Circular narratives, episodic TV, character arcs |
| **Snowflake Method** | Randy Ingermanson | Iterative (10 steps) | Methodical planners, complex multi-arc stories |
| **Brain Dump** | Organic | None | Pantsers, discovery writers |

### Additional Frameworks (Research Reference)

The following frameworks were identified in research but are not yet implemented. They represent potential future additions or inform the Structure panel's design. Sources: [boldly.blue](https://boldly.blue/story-structure-frameworks), [AuthorFlows](https://www.authorflows.com/blogs/story%E2%80%91structure%E2%80%91guide), [Writing With AI](https://writingwithai.com/storytelling-frameworks/).

| Framework | Origin | Key Feature | Best For |
|-----------|--------|-------------|----------|
| **Aristotle's Three-Part** | Poetics, ~335 BCE | Beginning → Middle → End; causation, not coincidence; hamartia/catharsis | Thematically dense stories, minimal structure |
| **Propp's Morphology** | Vladimir Propp, 1928 | 31 narrative functions across 7 character spheres | Quest narratives, folklore, mythic archetypes |
| **Syd Field's Paradigm** | Screenplay, 1979 | Setup (pp. 1-30) → Confrontation (pp. 30-90) → Resolution (pp. 90-120); plot points, midpoint | Page-count precision, screenplay adaptation |
| **McKee's Story** | Story, 1997 | Inciting Incident → Progressive Complications → Crisis → Climax → Resolution; value-change per scene | Literary fiction, deep scene-level construction |
| **Seger's Turning Point** | Making a Good Script Great, 1987 | Set-Up → Turning Point I → Development → Turning Point II → Climax → Resolution; central dramatic question | Diagnosing flat narratives, revision |
| **Hauge's Six-Stage** | Writing Screenplays That Sell, 1988 | Identity (protective mask) vs Essence (authentic self); 6 stages | Character-driven fiction, Identity/Essence transformation |
| **Watts' 8-Point Arc** | Writing a Novel, 1992 | Stasis → Trigger → Quest → Surprise → Critical Choice → Climax → Reversal → Resolution; ironic reversal | Literary fiction, moral decision, unintended consequence |
| **Yorke's Five-Act** | Into the Woods, 2013 | Ignorance → Trial → Revelation → Failure/Regression → Mastery; knowledge-based | Thematically driven fiction, learning arcs |
| **In Medias Res** | Homer (Odyssey) | Starts mid-action; backstory revealed via flashbacks | Thrillers, epics, instant engagement |
| **Nonlinear / Dual Timeline** | Multiple authors | Interweaves past/present/future; framed narratives, reverse chronology | Complex themes, cause-and-effect exploration |
| **Multi-Perspective (Rashomon)** | Akira Kurosawa | Single event from multiple POVs; contradictory accounts | Deep character, theme exploration |
| **Pixar's Story Spine** | Emma Coats (Pixar) | "Once upon a time... Every day... Until one day... Because of that... Until finally..." | Children's stories, animations, cause-and-effect |
| **Dean Koontz's Five-Part** | Dean Koontz | Inciting Incident → Door Slams Shut → Progressive Complications → Darkest Moment → Dramatic Resolution | Thrillers, horror, immediate stakes |
| **Story Grid (Coyne)** | Shawn Coyne | Five commandments: Inciting Incident, Progressive Complications, Crisis, Climax, Resolution; genre conventions | Genre fiction, scene-level analysis |
| **Simon Sinek's Golden Circle** | Simon Sinek | Why → How → What; philosophical, not structural; focuses on story's purpose | Character-driven stories, thematic foundation |

### Framework Fit Guide (Per Source)

| Framework | Use When | Avoid When |
|-----------|----------|------------|
| **Hero's Journey** | Clear main character with significant internal growth | Large ensemble cast, introspective tone |
| **Freytag's Pyramid** | Single high point, literary fiction, short pieces | Many twists, subplots, or nonlinear events |
| **Story Spine** | Establishing story logic; preventing wandering in drafts | Complex, multi-threaded stories |
| **Three-Act** | Unsure where to start; any genre; flexible foundation | Need detailed beat-level guidance (Act 2 often sags) |
| **Save the Cat** | Plot-driven fiction; need precise beat timing | Character-focused storytelling; discovery writing |
| **Golden Circle** | Character-driven story; need thematic foundation | Need help with pacing or event sequencing |
| **Fichtean Curve** | Fast-paced genres: thriller, mystery, action fantasy | Stories requiring emotional beats and quiet moments |
| **Seven-Point** | Major reveals or reversals; backward planning from ending | No outline before writing; discovery drafting |

### Framework Selection Guide

Research (AuthorFlows, Reedsy) identifies factors for choosing the right framework:

| Factor | Guideline |
|--------|-----------|
| **Genre** | Action/fantasy → Hero's Journey or Three-Act. Literary → Nonlinear or Yorke's Five-Act. Thriller → Fichtean Curve or Koontz's Five-Part |
| **Story Length** | Short stories → In Medias Res or compressed Three-Act. Epics → Five-Act or Snowflake Method |
| **Focus** | Character-driven → Hero's Journey or Story Circle. Plot-driven → Fichtean Curve or Save the Cat |
| **Writer Style** | Planners → Snowflake or Save the Cat. Discovery writers → Story Circle or Seven-Point |
| **Cultural Tradition** | Western → conflict-driven structures. East Asian → Kishōtenketsu. Indigenous → circular/spiral |

## Competitive UX Analysis

Based on comprehensive review of 8 writing tools (documented in `docs/writing_software_review/comparison.md`):

### Key Findings

1. **No tool offers a truly fluid workspace.** Every competitor uses either:
   - Route-based navigation (Reedsy, Sudowrite) — forces context switching
   - Fixed panels (Scrivener, Campfire) — limited flexibility
   - Single-pane focus (Ulysses) — hides supporting tools

2. **Scrivener's three-pane model (Binder/Editor/Inspector) is the closest** to what authors need, but it's rigid: panels can't be repositioned, resized freely, or torn off into separate windows.

3. **Photoshop's workspace model is the industry standard** for fluid, multi-panel creative work:
   - Draggable, resizable panels
   - Tear-off into floating windows
   - Multi-monitor support
   - User-defined layouts with presets
   - No forced navigation — all tools accessible simultaneously

4. **Campfire's modular approach** (18 worldbuilding modules) shows authors want many tools available, but Campfire's navigation-heavy UI makes it slow to switch between them.

### Design Decisions Informed by Research

| Decision | Research Basis |
|----------|----------------|
| Radial hub layout | Authors need central writing surface + surrounding tools (Scrivener model, improved) |
| Photoshop-style panels | Only proven model for fluid multi-panel creative work |
| 12 available panels | Covers all current backend capabilities without overwhelming |
| User chooses visible panels | Different author types need different tools (4 entry points) |
| Hover to preview | Reduces clicks to access information (Campfire lesson) |
| Tear-off floating windows | Multi-monitor support for power users (Photoshop pattern) |
| No forced navigation | Authors move between activities fluidly (key research insight) |

## Visual Mockups

Interactive mockups were created during brainstorming and served at `http://localhost:49892`:
- `current-architecture.html` — current route-based views (for comparison)
- `radial-hub.html` — radial hub workspace with Photoshop-style panels
- `writing-paths.html` — author entry points and story types

## References

### Local
- `docs/writing_software_review/comparison.md` — full 8-tool comparison
- `backend/app/schemas/enums.py` — `StoryStructure` enum with framework definitions
- `backend/app/services/runtime_prompts.py` — story structure definitions (lines 742-755)

### External Sources
- **boldly.blue** — 20 story structure frameworks, comprehensive guide with case studies: https://boldly.blue/story-structure-frameworks
- **Reedsy Blog** — 7 story structures every writer should know: https://reedsy.com/blog/guide/story-structure
- **AuthorFlows** — 10 powerful story structure frameworks with comparison table: https://www.authorflows.com/blogs/story%E2%80%91structure%E2%80%91guide
- **Writing With AI** — 8 storytelling frameworks with fit guide: https://writingwithai.com/storytelling-frameworks/
- **Masterclass** — how to write a book (403 blocked, content not captured): https://www.masterclass.com/articles/how-to-write-a-book
- The Write Practice — value-based plot types (9 story types)
