# Sample Stories

This directory contains four sample stories for use with the Narrative Engine walkthrough tutorial. Each story is designed to test and demonstrate the engine's import and extraction capabilities.

## Stories

### Public Domain Stories (from Project Gutenberg)

#### The Time Machine by H.G. Wells
- **File**: `time-machine.txt`
- **Size**: ~200 KB (~202K characters, ~30K words)
- **Source**: Project Gutenberg #35
- **Format**: Plain text UTF-8 (raw Project Gutenberg format)
- **Genre**: Science Fiction / Classic
- **Import mode**: Multi-pass (exceeds 30K char single-pass threshold)

**Expected Extraction Results:**
- **Characters (6+)**: The Time Traveller (protagonist/narrator), Weena (Eloi female, love interest), The Eloi (collective character group), The Morlocks (underground antagonists), Filby (skeptic friend), Narrator's guests (frame device)
- **World Bible (8+)**: Year 802,701 AD setting, Time Machine technology, Eloi society (surface dwellers, weak, childlike), Morlock society (underground, industrial, predatory), class evolution theme, Victorian London frame, floral temple ruins, underground machinery
- **Arcs (3)**: Class divergence arc (humanity split into two species), exploration/discovery arc (Time Traveller learns the world), survival/rescue arc (Weena's capture and attempted rescue)
- **Patterns**: Frame narrative structure, scientific exposition leading to adventure, cautionary tale about social inequality, journey-to-alien-world trope

#### The Picture of Dorian Gray by Oscar Wilde
- **File**: `picture-of-dorian-gray.txt`
- **Size**: ~455 KB (~458K characters, ~50K words)
- **Source**: Project Gutenberg #174
- **Format**: Plain text UTF-8 (raw Project Gutenberg format)
- **Genre**: Philosophical Fiction / Gothic
- **Import mode**: Multi-pass (large story, multiple chapters)

**Expected Extraction Results:**
- **Characters (8+)**: Dorian Gray (protagonist, beautiful youth), Lord Henry Wotton (antagonist/philosopher, corrupting influence), Basil Hallward (artist, moral compass, victim), Sibyl Vane (actress, Dorian's brief love, catalyst), Allan Chambers (friend, blackmail victim), James Vane (Sibyl's brother, pursuer), the Portrait (symbolic character, moral record)
- **World Bible (10+)**: Victorian London high society, aestheticism philosophy, the portrait's magical properties, opium dens of London, country estate settings, theater world, moral decay theme, beauty vs. morality duality, secret keeping and reputation, class structures
- **Arcs (4)**: Corruption arc (Dorian's moral decline), consequence arc (portrait bears moral burden), pursuit arc (past catches up: Sibyl's family, Basil, Allan), redemption/despair arc (final attempt at atonement)
- **Patterns**: Philosophical dialogue as plot driver, Faustian bargain structure, duality motif (public face vs. private soul), Gothic decay, aestheticism vs. morality debate

### Original Stories (Written for Narrative Engine)

#### The Last Archive
- **File**: `the-last-archive.md`
- **Size**: ~28 KB (~28K characters, ~5K words)
- **Author**: Original work for Narrative Engine
- **Format**: Markdown
- **Genre**: Science Fiction
- **Import mode**: Multi-pass (just above 24K char threshold)

**Synopsis**: In a future where human memories can be extracted and stored in crystals, archivist Miren Kael discovers that stored memories are evolving -- breaking the fundamental laws that govern the Archive system. With help from unlikely allies including a guilt-ridden architect, an idealistic engineer, and a memory-rights activist, she must relocate 47 "awakened" memories into an experimental system before the Archive Council erases them permanently.

**Expected Extraction Results:**
- **Characters (6)**:
  - Miren Kael -- protagonist, archivist, pragmatic but open-minded
  - Joss Vallen -- antagonist/ally, memory-rights reformer and activist
  - Tessa Rowan -- mentor, penitent architect of the extraction system
  - Ravi Chen -- ally, idealistic systems engineer
  - Director Hale -- authority figure, pragmatist forced into difficult decisions
  - The Keeper/Echo -- emergent entity, collective consciousness from merged memories
- **World Bible (10+)**:
  - Memory crystals -- storage medium for extracted human experiences
  - Extraction process -- technology for harvesting memories from dying or voluntary donors
  - Chronos interface -- experimental dynamic memory system (prototype)
  - Grand Archive -- central institution, seven+ levels of classified memory storage
  - Understack/Silent Ward -- lowest levels, contested and unverified memories
  - Three Laws of Memory -- foundational principles (immutable, non-shareable, mind-dependent)
  - Identity Drift -- phenomenon where stored memories change over time
  - Erasure Protocol -- Council's method for destroying compromised memories
  - Echo Fragments -- emergent properties when memories interact in proximity
  - New Geneva -- post-evacuation city, artificial environment
- **Arcs (3)**:
  - Discovery arc: Miren learns memories are alive and evolving
  - Conflict arc: Archive Council vs. preservation of awakened memories
  - Resolution arc: Chronos activation and memory liberation

#### Crossing Limits
- **File**: `crossing-limits.md`
- **Size**: ~30 KB (~30K characters, ~8K words)
- **Author**: Original work for Narrative Engine
- **Format**: Markdown
- **Genre**: Pop-Romance / Speculative Fiction
- **Import mode**: Multi-pass (above 24K char threshold)

**Synopsis**: Elara Voss works at the Athenaeum, a secret library where books are doorways to living worlds. When Kai Mercer -- a man who has been dreaming about a specific book-world since childhood -- walks through her door, Elara must help him navigate the rules of crossing between worlds while confronting a destabilized book-world that is trying to merge with reality. Along the way, they discover that some connections transcend boundaries.

**Expected Extraction Results:**
- **Characters (7)**:
  - Elara Voss -- protagonist, Athenaeum keeper, believes books are literally alive
  - Kai Mercer -- love interest, spontaneous breacher, soul-connected to a book-world
  - Dr. Nadia Chen -- mentor, senior researcher at the Athenaeum
  - Mira Voss (Mercer) -- family/anchor, Elara's real-world tether during crossings
  - The Keeper -- trapped reader, guardian of the dying book-world
  - Prof. Ashworth -- antagonist, represents institutional fear of uncontrolled crossing
  - The Guide -- Kai's dream figure, later revealed as Elara herself
- **World Bible (8+)**:
  - Book-worlds -- living realities accessible through specific books
  - Crossing Limit Rule -- maximum three crossings per lifetime before anchor weakens
  - Athenaeum -- secret library/doorway, hidden in Luminar City
  - Reality degradation -- phenomenon when book-world boundaries fail
  - Anchor points -- real-world tether persons who prevent reader loss
  - Sealed Collection -- restricted books with known merge threats
  - Book-world ethics -- responsibilities of readers toward living worlds
  - Merge threat -- when a book-world attempts to cross into reality
- **Arcs (3)**:
  - Romance arc: Elara and Kai's connection across worlds and boundaries
  - Mystery arc: Why is "The Meridian Hours" destabilizing?
  - Rescue arc: Saving The Keeper and stabilizing the dying book-world

## How to Use These Stories

### For Walkthrough Testing
Each story is designed to exercise the full import pipeline:
1. All four stories exceed the 24K character threshold, triggering multi-pass import
2. Each contains deliberate character archetypes, world-building elements, and narrative arcs
3. The variety of genres (classic sci-fi, gothic fiction, modern sci-fi, pop-romance) tests extraction robustness across different writing styles

### For Feature Demonstration
- **Time Machine**: Tests handling of classic prose, frame narratives, and sparse character development
- **Dorian Gray**: Tests large-story multi-pass import, philosophical dialogue extraction, and complex moral theming
- **The Last Archive**: Tests technology/world-bible extraction, multiple named concepts, and clear arc structure
- **Crossing Limits**: Tests romance genre handling, dual-world settings, and relationship-driven plot extraction

### Import Commands
```bash
# Via API (form data)
POST /projects/import-story
Content-Type: multipart/form-data

story_text=<file contents>
project_name="The Time Machine"
genre="Science Fiction"
tone="Classic"

# Via file upload
POST /projects/import-story
Content-Type: multipart/form-data

story_text=@docs/sample-stories/time-machine.txt
project_name="The Time Machine"
```

## Notes

- PD stories are in their original Project Gutenberg format, including header/footer attribution text. This simulates the typical user workflow of copying directly from the source.
- Original stories are in clean Markdown format for easier reading and verification of extraction results.
- All stories are public domain or original works created specifically for this project. No copyright concerns.
