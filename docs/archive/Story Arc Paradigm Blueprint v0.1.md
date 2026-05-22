# Story Arc Paradigm Blueprint v0.1

## Purpose

This document defines a planning-facing taxonomy for major story arc paradigms that Narrative-Engine can use to:

- help a writer choose a high-level story movement
- guide sequencing and chapter planning
- suggest the next best development step for a draft in progress
- keep model guidance aligned with the intended emotional shape of the story

It is intentionally written for future LLM use as well as human product design.

## Product Role

Story arc paradigms should not behave like rigid templates.

They should act as:

- planning lenses
- diagnostic frameworks
- progression heuristics
- next-step suggestion engines

They should not force identical beats across all projects using the same arc.

## LLM Usage Goals

For each story arc, the system should eventually be able to answer:

- what emotional movement defines this arc
- what early promises the story should make
- what middle-phase pressures should intensify
- what turning points are structurally important
- what kinds of scene goals typically belong next
- what failure modes indicate the story is drifting away from the chosen arc
- what kind of ending delivers on the arc's contract

## Arc Record Shape

Each supported arc should eventually be represented in a structured form that includes:

- `arc_id`
- `display_name`
- `short_definition`
- `core_movement`
- `reader_promise`
- `best_fit_genres`
- `adjacent_arcs`
- `canonical_stages`
- `stage_objectives`
- `common_turning_points`
- `supporting_cast_functions`
- `typical_antagonistic_pressure`
- `scene_goal_patterns`
- `midpoint_shift_patterns`
- `climax_requirements`
- `resolution_requirements`
- `failure_modes`
- `recovery_moves`
- `planner_next_step_rules`
- `llm_prompt_guidance`

## Canonical Stage Guidance

The exact stage names may vary by arc, but the planning system should usually reason in a sequence similar to:

1. setup or ordinary state
2. disturbance or invitation
3. commitment
4. escalation
5. reversal or revelation
6. crisis
7. climax
8. aftermath or transformed state

The point is not to impose identical structure on all arcs. The point is to give the planner a stable way to detect where the story currently is and what kind of step should come next.

## Initial Target Arc Set

The first supported planning taxonomy should include at least:

1. Hero's Journey
2. Rags to Riches
3. Quest
4. Rebirth
5. Tragic Arc
6. Icarus or Overreach
7. Man in a Hole
8. Cinderella or Rise-Fall-Rise
9. Fall or Fall from Grace
10. Overcoming the Monster

## Planning-System Expectations

The future planner should be able to use arc data in three ways:

### 1. Arc Selection Support

When the writer is still exploring:

- compare arcs against the premise
- explain which arcs fit the premise best
- identify likely thematic consequences of each choice
- suggest the most natural early plot moves for the selected arc

### 2. Arc-Adherence Guidance

When the writer already chose an arc:

- identify the current likely stage
- explain what the story has already achieved structurally
- suggest 2-4 plausible next scene or chapter moves
- warn when the draft is drifting away from the arc's emotional contract

### 3. Arc-Recovery Guidance

When the draft has lost shape:

- identify what promise is missing or underdeveloped
- suggest which turning point or pressure beat is absent
- recommend whether to reinforce the chosen arc or change to a better-fitting arc

## Writer Experience Expectations

The frontend and planning workflow should eventually let the writer:

- choose an arc deliberately
- switch arcs while preserving project notes
- see the arc's stage map in the planning view
- attach scene or chapter cards to arc stages
- ask for next-step suggestions that are explicitly grounded in the selected arc
- compare “stay in this arc” versus “pivot to another arc” recommendations

## Implementation Boundary

This blueprint does not yet require:

- runtime model integration
- persistence wiring
- UI implementation

It exists to stabilize the planning contract before arc-aware story guidance is built.

## Detailed Arc Notes

### 1. Hero's Journey

Short definition:

- A protagonist leaves the familiar world, is tested in an unfamiliar one, suffers an identity-breaking ordeal, and returns changed with something of value.

Core movement:

- comfort to disruption
- reluctance to commitment
- fear to competence
- false confidence to humility
- collapse to transformation
- return to earned authority

Reader promise:

- the protagonist will become more than they were and prove that change under pressure matters.

Best fit genres:

- fantasy
- science fiction
- mythic adventure
- epic YA
- spiritual adventure

Adjacent arcs:

- Quest
- Rebirth
- Overcoming the Monster

Canonical stages:

1. ordinary world
2. call to adventure
3. refusal or hesitation
4. mentor or enabling force
5. threshold crossing
6. tests, allies, enemies
7. approach to the ordeal
8. ordeal or symbolic death
9. reward or revelation
10. road back
11. resurrection or final test
12. return with the boon

Stage objectives:

- establish the protagonist's lack, fear, and ordinary role
- make the call specific and costly
- force a choice that commits the protagonist to the unknown
- use trials to expose internal weakness, not just external incompetence
- make the ordeal destroy an old identity or coping pattern
- ensure the return tests whether change survives contact with the old world

Supporting cast functions:

- mentor: gives tools, permission, or worldview
- herald: announces the need for change
- threshold guardian: tests readiness
- allies: diversify skills and emotional mirrors
- trickster: destabilizes certainty
- shadow antagonist: embodies what the hero might become if corrupted

Typical antagonistic pressure:

- fear of inadequacy
- hostile new rules or worlds
- moral temptation
- pressure to retreat into the old self

Scene-goal patterns:

- scenes that make the ordinary world feel too small
- tests that externalize the protagonist's inner lack
- alliance scenes that redefine trust
- ordeal scenes that strip away false strategies
- return scenes that prove transformation through action

Midpoint or ordeal shift:

- the story stops being about entering adventure and becomes about surviving identity-costly truth.

Climax requirements:

- the final confrontation must require the protagonist to act differently than they would have at the beginning.

Resolution requirements:

- the boon must matter to the community, not only the protagonist.

Failure modes:

- passive protagonist
- mentor doing the work
- episodic trials with no cumulative change
- spectacle-heavy climax with no identity cost
- no meaningful return or re-entry

Planner next-step rules:

- if still in setup, increase pressure on the old life until staying is visibly costly
- if pre-threshold, force a decision scene rather than drifting into adventure
- if in the trials phase, add pressure that targets the protagonist's wound or flaw
- if nearing the ordeal, remove easy exits and require sacrifice
- if post-revelation, test whether insight survives in action
- if near the ending, bring the transformed protagonist back into contact with the starting world

LLM prompt guidance:

- Ask: what fear or lack does the protagonist still carry from the ordinary world?
- Ask: what kind of trial would expose that weakness next?
- Suggest beats that convert competence into humility, then humility into earned power.

### 2. Rags to Riches

Short definition:

- A diminished or disregarded protagonist rises into worth, recognition, status, security, or love, often after being tested by temptation, pride, or false versions of success.

Core movement:

- deprivation to hope
- obscurity to recognition
- hunger to striving
- rise to temptation
- fall to recalibration
- restoration to deservingness

Reader promise:

- hidden worth will be tested, recognized, and either fulfilled or betrayed.

Best fit genres:

- commercial fiction
- romance
- family saga
- class-mobility drama
- aspirational fantasy

Adjacent arcs:

- Cinderella or Rise-Fall-Rise
- Rebirth
- Hero's Journey

Canonical stages:

1. diminished starting life
2. glimpse of possibility
3. first effort and proof of potential
4. social or material ascent
5. complication through envy, pride, or false success
6. humiliation or fall
7. recovery through true values
8. earned elevation

Stage objectives:

- define what “rags” actually mean: material, emotional, social, or existential lack
- clarify what “riches” mean in this story: money, belonging, dignity, voice, safety, or love
- make ascent emotionally rewarding but morally risky
- ensure the fall tests whether the protagonist understands true value

Supporting cast functions:

- benefactor or patron
- rival or pretender
- gatekeeper of status
- loyal friend who preserves original values
- aspirational figure or love interest

Typical antagonistic pressure:

- class barriers
- impostor syndrome
- vanity
- envy
- public legitimacy tests

Scene-goal patterns:

- competence scenes that prove overlooked ability
- scenes of entry into a new social layer
- temptation scenes where image competes with substance
- fall scenes that strip away superficial gain
- restoration scenes grounded in recognition and moral clarity

Midpoint shift:

- the protagonist begins to ask whether they want appearance of success or rightful success.

Climax requirements:

- the final gain should align outer elevation with inner maturity.

Resolution requirements:

- the ending should reveal what kind of wealth truly matters in this story.

Failure modes:

- easy luck with no earned competence
- vague concept of riches
- no moral cost in the middle
- glamorous ending with no thematic resolution

Planner next-step rules:

- if the protagonist is still diminished, intensify their concrete longing and deprivation
- if an opportunity has appeared, force initiative rather than rescue
- if ascent is underway, widen the social cost and temptation
- if the arc is flattening, create a fall that exposes false success
- if the story is close to ending, stage recognition through identity and values, not only reward

LLM prompt guidance:

- Ask: what form of worth is the protagonist actually seeking?
- Ask: what scene would prove they can earn it?
- Suggest beats where rising external success creates internal distortion that must be corrected.

### 3. Quest

Short definition:

- A protagonist or group pursues a concrete objective across distance and adversity, discovering that the true value of the journey may differ from the original prize.

Core movement:

- intention to commitment
- anticipation to hardship
- confidence to attrition
- fragmentation to recommitment
- arrival to revelation

Reader promise:

- a meaningful destination will be pursued through escalating difficulty, and the journey will change the pursuer.

Best fit genres:

- adventure
- fantasy
- military fiction
- space opera
- heist-adjacent expedition stories

Adjacent arcs:

- Hero's Journey
- Overcoming the Monster

Canonical stages:

1. mission defined
2. stakes clarified
3. party assembled
4. departure
5. travel trials
6. midpoint revelation or route change
7. betrayal, depletion, or crisis of purpose
8. final approach
9. confrontation or retrieval
10. aftermath

Stage objectives:

- define the objective, deadline, and consequence of failure
- make travel deplete time, trust, supplies, innocence, or unity
- transform logistical pressure into moral pressure by the midpoint
- force a decision at the endpoint, not just arrival

Supporting cast functions:

- specialist companions
- skeptic
- believer
- guide
- betrayer
- endpoint guardian

Typical antagonistic pressure:

- terrain
- scarcity
- enemy pursuit
- internal group fracture
- moral ambiguity of the quest object

Scene-goal patterns:

- route problem scenes
- group-friction scenes
- worldbuilding-through-travel scenes
- sacrifice-for-progress scenes
- revelation scenes that change what the quest means

Midpoint shift:

- the quest stops being about reaching the place and becomes about whether the destination is worth the cost or what the prize really means.

Climax requirements:

- the endpoint should require judgment, renunciation, use, surrender, or reinterpretation of the prize.

Resolution requirements:

- the aftermath should account for cost, not only success.

Failure modes:

- episodic obstacle chain with no cumulative transformation
- interchangeable companions
- meaningless MacGuffin
- no decision at the destination

Planner next-step rules:

- if early, sharpen mission clarity and group role definition
- if in the road phase, vary obstacle type and depletion type
- if energy is dipping, trigger a revelation that changes the quest's meaning
- if the group is too stable, introduce fracture, betrayal, or competing priorities
- if near the end, transform the prize into a choice

LLM prompt guidance:

- Ask: what specific resource or relationship has this leg of the quest depleted?
- Ask: what truth should the journey reveal next?
- Suggest the next beat as a problem that tests both route strategy and group values.

### 4. Rebirth

Short definition:

- A protagonist trapped in bitterness, corruption, grief, denial, or numbness is awakened into renewal.

Core movement:

- deadening to disturbance
- resistance to fracture
- shame to confrontation
- collapse to surrender
- renewal to repaired action

Reader promise:

- someone who has become emotionally or morally lost may come back to life.

Best fit genres:

- literary fiction
- family drama
- redemption stories
- holiday or seasonal stories
- relationship-heavy fantasy

Adjacent arcs:

- Cinderella
- Hero's Journey
- Fall from Grace

Canonical stages:

1. stagnation or corruption
2. disruptive encounter
3. resistance
4. repeated confrontation with denied truth
5. exposure of wound, guilt, or grief
6. crisis or symbolic death
7. surrender or confession
8. renewed action and repair

Stage objectives:

- make the deadened state visible in behavior
- introduce something living the protagonist cannot fully dismiss
- ensure the change happens through surrendered behavior, not speech alone
- end with concrete repair, not only emotional realization

Supporting cast functions:

- innocent or truth-teller
- compassionate guide
- witness to past damage
- tempter back into the old self
- estranged loved one

Typical antagonistic pressure:

- self-protective numbness
- shame
- guilt
- fear of vulnerability
- institutions or habits built around the deadened self

Scene-goal patterns:

- scenes that show the protagonist harming or neglecting life around them
- scenes that reactivate dormant feeling
- confrontation scenes that strip self-justification
- surrender scenes with emotional cost
- repair scenes through service, care, or responsibility

Midpoint shift:

- the protagonist stops arguing that the old self is working and begins to see the cost.

Climax requirements:

- rebirth must be proven by changed action under familiar pressure.

Resolution requirements:

- repaired bonds or renewed duty should show durable change.

Failure modes:

- purely verbal transformation
- no meaningful prior damage
- instant forgiveness
- sentimental but unearned renewal

Planner next-step rules:

- if early, clarify the protagonist's harmful closed pattern
- if disturbance has occurred, add a scene that makes avoidance fail
- if approaching breakdown, expose the underlying wound directly
- if post-surrender, generate small acts of change before large restoration
- if closing, show renewed life through duty, love, or service

LLM prompt guidance:

- Ask: what old coping pattern is still controlling the protagonist?
- Ask: what living relationship or truth should challenge it next?
- Suggest scenes that force vulnerability and then prove renewal in action.

### 5. Tragic Arc

Short definition:

- A capable protagonist moves toward loss because flaw, blindness, divided loyalty, or irreversible commitment collapses their chance to change in time.

Core movement:

- promise to pressure
- pressure to denial
- denial to narrowing options
- late recognition to catastrophe
- catastrophe to meaning-bearing aftermath

Reader promise:

- the story will show how someone who might have succeeded destroys what they meant to preserve.

Best fit genres:

- literary drama
- political fiction
- family tragedy
- crime tragedy
- prestige fantasy

Adjacent arcs:

- Fall from Grace
- Icarus or Overreach

Canonical stages:

1. stature and flaw established
2. inciting pressure
3. early flaw-driven response
4. escalation through commitment
5. warnings refused
6. recognition arrives too late
7. catastrophe
8. aftermath

Stage objectives:

- make the protagonist admirable enough that loss matters
- make the flaw specific and active
- ensure each bad choice feels understandable but misaligned
- delay recognition until reversal is nearly impossible

Supporting cast functions:

- truth-teller
- loyal enabler
- healthier foil
- pressure source or tempter
- witness or survivor

Typical antagonistic pressure:

- pride
- fear of humiliation
- duty conflict
- prophecy or fate pressure
- love distorted by possession or control

Scene-goal patterns:

- scenes that unite greatness and flaw
- scenes where the protagonist justifies a dangerous choice
- warnings that are clear but dismissible
- increasing collateral damage
- recognition scenes with emotional, not merely informational, force

Midpoint shift:

- the protagonist becomes more committed to preserving the wrong thing than to correcting course.

Climax requirements:

- the catastrophe must arise from the protagonist's own pattern, not random bad luck.

Resolution requirements:

- aftermath should clarify what was lost and why it matters.

Failure modes:

- unlucky protagonist instead of responsible one
- vague flaw
- arbitrary catastrophe
- no recognition
- misery without meaning

Planner next-step rules:

- if early, sharpen the protagonist's stature and flaw in the same scene cluster
- if escalating, make each choice more binding and harder to reverse
- if warnings are absent, add trusted voices or visible collateral damage
- if near catastrophe, force an irreversible choice
- if ending, render aftermath through survivors and institutions, not only the fallen protagonist

LLM prompt guidance:

- Ask: what admirable quality is being twisted by the protagonist's flaw?
- Ask: what choice would feel necessary to them but look disastrous to an outside observer?
- Suggest next beats that tighten consequence while preserving tragic plausibility.

### 6. Icarus or Overreach

Short definition:

- A protagonist rises through talent, ambition, appetite, or power, then exceeds the limit they should have respected and crashes.

Core movement:

- hunger to ascent
- ascent to intoxication
- intoxication to reckless expansion
- overreach to exposure
- exposure to collapse

Reader promise:

- success will become the instrument of downfall once the protagonist mistakes altitude for invulnerability.

Best fit genres:

- ambition dramas
- startup or corporate fiction
- celebrity rise-and-fall
- political thrillers
- hubris-centered fantasy

Adjacent arcs:

- Fall from Grace
- Tragic Arc

Canonical stages:

1. hunger and ambition
2. breakthrough
3. reinforcing success
4. boundary testing
5. peak intoxication
6. fatal overreach
7. collapse
8. reckoning

Stage objectives:

- make ascent exhilarating and understandable
- normalize increasingly dangerous risks
- establish visible boundaries before they are crossed
- make the final overreach feel like the protagonist's most “natural” move

Supporting cast functions:

- mentor of ascent
- cautious friend
- rival
- audience or institution that rewards excess until it punishes it
- victim or beneficiary of the protagonist's excess

Typical antagonistic pressure:

- praise
- scale
- ego
- public scrutiny
- appetites sharpened by success

Scene-goal patterns:

- first-win intoxication scenes
- scenes where praise erodes caution
- scenes where restraint feels emotionally unbearable
- public overreach scenes
- collapse scenes where former strengths become liabilities

Midpoint shift:

- the protagonist stops seeking success and starts assuming exemption.

Climax requirements:

- the collapse should be tied directly to the ignored limit.

Resolution requirements:

- the story should decide whether the reckoning lands in humility, bitterness, warning, or annihilation.

Failure modes:

- weak ascent
- abrupt overreach
- underpowered warnings
- arbitrary collapse
- preachy aftermath

Planner next-step rules:

- if early, define exactly what “altitude” means to this protagonist
- if reinforcing success, raise stakes and praise simultaneously
- if boundaries are too soft, add explicit limits from mentors, institutions, or nature
- if nearing the turn, engineer one decisive act of scale, ego, or exposure
- if post-collapse, choose whether the reckoning is cautionary, tragic, or partially redemptive

LLM prompt guidance:

- Ask: what limit is the protagonist persuading themselves they no longer need to respect?
- Ask: what success beat would make them feel untouchable?
- Suggest scenes where reward and danger grow together until they cannot distinguish them.

### 7. Man in a Hole

Short definition:

- A protagonist falls into trouble, worsens the situation through failed fixes, hits bottom, then climbs out by changing strategy and self-understanding.

Core movement:

- stability to disruption
- disruption to entrapment
- entrapment to bottom
- bottom to adaptive climb
- climb to changed emergence

Reader promise:

- the story will keep worsening the problem until the protagonist earns a real way out.

Best fit genres:

- thrillers
- survival stories
- crime stories
- relationship crisis stories
- comedy of escalating problems

Adjacent arcs:

- Rebirth
- Quest

Canonical stages:

1. baseline
2. drop into trouble
3. failed quick fix
4. deepening entrapment
5. bottom
6. reorientation
7. climb
8. new equilibrium

Stage objectives:

- define the normal the protagonist stands to lose
- make each attempted fix reveal misunderstanding
- widen consequences causally, not randomly
- ensure the climb depends on changed behavior

Supporting cast functions:

- helper
- skeptic or antagonist
- dependent
- mirror character who stays stuck
- gatekeeper who forces earned progress

Typical antagonistic pressure:

- time
- scarcity
- legal danger
- shame
- escalating collateral damage

Scene-goal patterns:

- drop scenes that instantly destabilize the status quo
- backfire scenes
- scenes that spread damage into more life domains
- bottom scenes that reveal the real problem
- climb scenes built from smaller corrective steps

Midpoint shift:

- the protagonist realizes the original fix strategy was fundamentally wrong.

Climax requirements:

- the breakthrough should convert survival into recovery through changed behavior.

Resolution requirements:

- the new normal should show scar tissue and earned capability.

Failure modes:

- shallow hole
- random complications
- unearned escape
- helpers doing the work
- reset ending with no cost

Planner next-step rules:

- if early, make the drop concrete and immediate
- if in the middle, propose a fix that backfires for a specific reason
- if the story feels repetitive, widen the damage into new relationships or systems
- if near the bottom, surface the protagonist's contribution to the problem
- if climbing out, generate smaller wins that prove changed strategy

LLM prompt guidance:

- Ask: what is the protagonist still misunderstanding about the hole they are in?
- Ask: what attempted fix would plausibly worsen matters next?
- Suggest progress through causal escalation rather than unrelated obstacles.

### 8. Cinderella or Rise-Fall-Rise

Short definition:

- A constrained or undervalued protagonist is lifted into possibility, loses that rise, then earns a more durable second rise grounded in true identity rather than temporary glamour.

Core movement:

- deprivation to hope
- hope to ascent
- ascent to fragility
- fragility to loss
- loss to endurance
- endurance to recognition and restoration

Reader promise:

- the protagonist's true worth will survive humiliation and be recognized on firmer terms.

Best fit genres:

- romance
- fairy-tale retellings
- coming-of-age
- class-transcending drama

Adjacent arcs:

- Rags to Riches
- Rebirth

Canonical stages:

1. constrained world
2. glimpse of transformation
3. threshold into possibility
4. temporary ascent
5. exposure or collapse
6. exile or return to ashes
7. proof of identity or worth
8. final restoration

Stage objectives:

- make the starting injustice palpable
- make the first rise wondrous but unstable
- separate first ascent from final belonging
- ensure the final rise depends on recognition of true identity or worth

Supporting cast functions:

- oppressors
- benefactor or catalyst
- gatekeepers
- aspirational or romantic figure
- rival or false claimant
- validating witnesses

Typical antagonistic pressure:

- hierarchy
- disguise limitations
- social illegitimacy
- shame
- envy

Scene-goal patterns:

- humiliation scenes
- wonder or transformation scenes
- precarious belonging scenes
- collapse through exposure, timing, betrayal, or structural inequality
- recognition scenes that bind truth to belonging

Midpoint shift:

- the dream feels genuinely attainable, which makes the collapse devastating.

Climax requirements:

- restoration should come through identity, courage, or moral worth, not pure rescue.

Resolution requirements:

- the final belonging should feel stable in a way the first rise did not.

Failure modes:

- easy ascent
- arbitrary fall
- passive protagonist
- second rise no different from the first

Planner next-step rules:

- if in the ashes, clarify the desired better world vividly
- if at the invitation stage, define the cost or limitation of transformation
- if in the temporary rise, add fragility or a countdown
- if the arc needs pain, design a collapse that removes hope as well as status
- if nearing the end, create a recognition mechanism that rewards true self rather than performance alone

LLM prompt guidance:

- Ask: what part of the protagonist's rise is currently dependent on disguise, borrowed status, or fragile luck?
- Ask: what proof of true worth could matter later?
- Suggest next beats that make restoration more durable than first ascent.

### 9. Fall or Fall from Grace

Short definition:

- A protagonist begins in strength, innocence, legitimacy, or promise and descends through temptation, compromise, corruption, or misjudgment.

Core movement:

- promise to compromise
- compromise to rationalization
- rationalization to deterioration
- deterioration to exposure
- exposure to ruin or bitter clarity

Reader promise:

- the story will track how decline happens choice by choice and what that decline destroys.

Best fit genres:

- crime
- political drama
- moral thrillers
- prestige family drama

Adjacent arcs:

- Tragic Arc
- Icarus

Canonical stages:

1. elevated or promising beginning
2. pressure or temptation
3. first compromise
4. temporary gain
5. progressive deterioration
6. fracture of key bonds
7. exposure or consequence
8. ruin, confession, exile, or painful clarity

Stage objectives:

- define what the protagonist has to lose
- stage each compromise as a real choice
- reward bad choices just enough to sustain them
- convert the accumulated damage into unavoidable exposure

Supporting cast functions:

- tempter
- loyal confidant
- victims or dependents
- rival or nemesis
- witnesses
- judgment figure

Typical antagonistic pressure:

- ambition
- humiliation
- desire
- ideology
- self-justification

Scene-goal patterns:

- temptation scenes
- rationalization scenes
- scenes where reward masks rot
- bond-breaking scenes
- exposure scenes that remove self-deception

Midpoint shift:

- the protagonist can still turn back, but the cost of turning back becomes psychologically harder than continuing.

Climax requirements:

- the consequence should reflect the specific pattern of corruption.

Resolution requirements:

- the ending should clearly define the moral and emotional shape of the fall.

Failure modes:

- already-corrupt starting point
- sudden decline
- no seductive reward
- consequence without buildup

Planner next-step rules:

- if early, clarify what makes the protagonist worth watching before the fall
- if temptation is weak, increase the cost of refusal
- if decline is too fast, insert a reward scene that reinforces compromise
- if nearing exposure, strip away the relationship or institution that shielded them
- if ending, choose among tragedy, caution, hollow victory, confession, or late redemptive awareness

LLM prompt guidance:

- Ask: what line has the protagonist not yet crossed, and why are they close to crossing it?
- Ask: what reward is currently making the decline feel worth it?
- Suggest scenes where each compromise feels locally rational and globally destructive.

### 10. Overcoming the Monster

Short definition:

- A threat endangers a person, community, homeland, or moral order, and the protagonist commits to confronting and defeating, containing, or surviving it.

Core movement:

- fear to resolve
- resolve to preparation
- preparation to descent into danger
- dread to confrontation
- confrontation to liberation

Reader promise:

- the danger will be made vivid, and the story will earn a cathartic confrontation.

Best fit genres:

- horror
- monster fiction
- action adventure
- military or siege fiction
- resistance narratives

Adjacent arcs:

- Quest
- Hero's Journey

Canonical stages:

1. threat revealed
2. stakes clarified
3. denial or failed early response
4. commitment to fight
5. preparation
6. entry into hostile space
7. costly confrontation
8. defeat, containment, or escape
9. aftermath

Stage objectives:

- define the monster specifically
- prove ordinary systems cannot solve the threat
- bind the protagonist personally to the danger
- ensure victory comes through learned method or sacrifice rather than convenience

Supporting cast functions:

- skeptic
- victim
- mentor or specialist
- team with complementary skills
- sacrificial ally
- traitor or opportunist
- survivors who embody what must be saved

Typical antagonistic pressure:

- direct physical threat
- dread
- uncertainty
- hostile terrain
- institutions in denial

Scene-goal patterns:

- threat demonstration scenes
- failure-of-normal-protection scenes
- preparation and lore scenes
- probe encounters that reveal the monster's strength
- hostile-territory scenes
- final confrontation scenes built around the monster's weakness and the hero's cost

Midpoint shift:

- the protagonist learns the monster is worse than expected and the plan must adapt.

Climax requirements:

- the confrontation should require courage, sacrifice, and use of learned weakness.

Resolution requirements:

- the aftermath should show who was saved, what was lost, and whether the threat is fully gone.

Failure modes:

- vague monster
- weak preparation
- arbitrary win
- static monster
- no aftermath

Planner next-step rules:

- if early, show the monster's harm concretely and fast
- if denial is persisting, make the threat personal to the protagonist
- if preparing, identify missing tools, knowledge, or allies
- if in the middle, escalate through adaptive monster behavior
- if nearing the climax, force a confrontation where success depends on cost-bearing action
- if ending, make the changed world visible

LLM prompt guidance:

- Ask: what does the monster want or do, specifically?
- Ask: why can the world not simply ignore it or delegate it away?
- Suggest the next beat as either proof of threat, costly preparation, or tightened confrontation path.

## Cross-Arc Selection Heuristics

Use these quick heuristics when helping a writer choose an arc:

- choose `Hero's Journey` when the story is about identity expansion through ordeal and return
- choose `Rags to Riches` when the story is about recognition, legitimacy, and earned elevation
- choose `Quest` when the story is about pursuit, travel, endurance, and endpoint judgment
- choose `Rebirth` when the story is about awakening from emotional or moral deadness
- choose `Tragic Arc` when the story should end in inevitable, meaning-bearing loss tied to flaw
- choose `Icarus / Overreach` when ascent and excess are more central than sorrowful inevitability
- choose `Man in a Hole` when the engine is worsening trouble and earned recovery
- choose `Cinderella / Rise-Fall-Rise` when the story depends on fragile ascent, humiliating loss, and durable recognition
- choose `Fall / Fall from Grace` when the central fascination is progressive corruption or decline
- choose `Overcoming the Monster` when a concrete threat must be faced and defeated

## Planner Diagnostics

When using arc paradigms to guide next steps, the future planner should ask:

- what exact stage is the story most likely in right now?
- what promise has the story already made to the reader?
- what pressure or turn has not yet been paid off?
- what kind of next scene would deepen the selected arc rather than merely continue plot motion?
- is the draft still inside the chosen arc, or has it drifted into another paradigm?

## Arc Drift Rules

The planner should also detect when a story appears mismatched:

- if the writer claims `Hero's Journey` but the story is mostly escalating trouble and recovery, suggest `Man in a Hole`
- if the writer claims `Rags to Riches` but the middle is dominated by moral decline, suggest `Fall from Grace`
- if the writer claims `Quest` but the real engine is confronting a central external threat, suggest `Overcoming the Monster`
- if the writer claims `Rebirth` but the ending is clearly catastrophic and flaw-driven, suggest `Tragic Arc`

## Future Product Use

This blueprint can later feed:

- project setup arc selection
- chapter and scene planning guidance
- arc-stage labels on planning cards
- next-step suggestion prompts
- continuity checks against intended emotional movement
- “stay in this arc” versus “pivot arc” diagnostics
