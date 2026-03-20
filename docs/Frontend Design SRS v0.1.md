# Frontend Design SRS v0.3

## 1. Purpose

The frontend should feel like a writer workspace, not a generic admin panel.

It should help the user:

- create or open a project
- shape premise and story context
- inspect generated artifacts
- launch backend work
- monitor exact progress
- review checker outcomes before changing models or workflow settings

## 2. Core UX Principles

- project-first workflow
- clear authoring context
- backend-driven status
- visible artifact inspection
- practical model and checker controls
- honest representation of implemented behavior

## 3. Primary User Flow

The intended user journey is:

1. create or open a project
2. review premise, constraints, and story context
3. add working notes for character, world, and continuity
4. inspect existing artifacts such as manifest, sequence, and chapter draft
5. stage a chapter packet
6. launch a backend job
7. monitor exact job status and logs
8. run the role-model checker when adjusting workflow configuration

## 4. Main Surface Areas

The UI should include:

- project list and creation flow
- active project detail and health cues
- workspace notes for story development
- artifact preview for manifest, sequence, and chapter
- chapter packet assembly
- job monitor and logs
- workflow guidance and role-model checker controls

## 5. Persistence Expectations

Canonical project and runtime state must come from the backend.

Local browser storage is acceptable for temporary workspace notes as long as the UI clearly treats it as personal workspace context rather than canonical backend state.

## 6. Artifact Review

Artifact review is important because the user should be able to inspect current story state before launching downstream steps.

The frontend should support direct review of:

- manifest
- sequence
- chapter-1

## 7. Async Behavior

The contract is backend-driven progress. Even if some flows currently complete quickly, the UI must be built to poll and render exact status.

Required patterns:

- job and checker starts return immediately
- status is read from polling endpoints
- terminal success and failure states are clearly visible
- logs and result details remain inspectable after completion

## 8. Current Implementation Status

Implemented now:

- project creation and listing
- project detail display
- local workspace notes
- artifact preview for manifest, sequence, and chapter-1
- chapter packet assembly
- backend status polling
- role-model checker model selection and result display

Deferred:

- deeper browser-side editing workflows
- production-grade orchestration UX
- richer drafting review surfaces
- full runtime parity with the target execution model
