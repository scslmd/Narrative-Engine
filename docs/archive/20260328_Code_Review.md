[
  {
    "task_id": "b8a8be60-2b86-49db-8ea6-90522c597eff",
    "purpose": "Align the foundation TypeScript contract with the existing mock/data layer so `FoundationEditor` can consume `getFoundation`, `createFoundation`, and `updateFoundation` without a parallel shape fork.",
    "responsible_file": "F:/Dev/Narrative-Engine/frontend/src/types/foundation.ts",
    "knowledge_base": [
      "`FoundationProfile` in `frontend/src/services/mocks/foundationMock.ts`",
      "snake_case frontend contract rules from `AGENTS.md`",
      "existing `interface` patterns in `frontend/src/types`"
    ],
    "references_and_schema": {
      "input_data_schema": "Current mock shape in `frontend/src/services/mocks/foundationMock.ts`: `foundation_id`, `project_id`, `premise`, `logline`, `thematic_spine`, `emotional_promise`, `tone_and_voice_direction`, `target_audience`, `narrative_constraints`, `complexity_level`, `success_definition`, `version`.",
      "output_data_schema": "One exported interface set matching the existing mock/backend surface so UI code imports a single canonical foundation contract.",
      "external_refs": [
        "F:/Dev/Narrative-Engine/frontend/src/services/mocks/foundationMock.ts",
        "F:/Dev/Narrative-Engine/AGENTS.md",
        "F:/Dev/Narrative-Engine/frontend/src/types/foundation.ts"
      ]
    },
    "utilized_features": [
      "existing frontend type modules",
      "shared mock service contracts",
      "snake_case field preservation"
    ],
    "expected_outcomes": [
      "`frontend/src/types/foundation.ts` exports a shape that can be passed directly to `getFoundation` and `updateFoundation` without field remapping.",
      "Fields such as `core_concept` and `central_conflict` are removed or replaced if they are not present in the existing foundation service contract."
    ],
    "execution_constraints": {
      "mode": "parallel",
      "serial_after": [],
      "serial_notes": "This contract task must complete before the foundation editor is updated."
    },
    "guardrails": [
      "Do not change `frontend/src/services/mocks/foundationMock.ts` in this task.",
      "Do not invent new foundation fields that do not already exist in the repo.",
      "Keep this file limited to shared TypeScript contracts."
    ]
  },
  {
    "task_id": "a2f41946-7f8f-4873-adb4-454eb0750b30",
    "purpose": "Refactor `FoundationEditor` to use the canonical foundation contract and existing mock-backed save flow instead of the incompatible local field set introduced on this branch.",
    "responsible_file": "F:/Dev/Narrative-Engine/frontend/src/components/foundation/FoundationEditor.tsx",
    "knowledge_base": [
      "`FoundationEditor` local state wiring",
      "`FoundationProfile` fields from `frontend/src/types/foundation.ts`",
      "`getFoundation` and `updateFoundation` usage expectations from `frontend/src/services/mocks/foundationMock.ts`"
    ],
    "references_and_schema": {
      "input_data_schema": "Canonical foundation interface from `frontend/src/types/foundation.ts` after alignment.",
      "output_data_schema": "Editor props and local form state that read and write the existing foundation fields only.",
      "external_refs": [
        "F:/Dev/Narrative-Engine/frontend/src/components/foundation/FoundationEditor.tsx",
        "F:/Dev/Narrative-Engine/frontend/src/types/foundation.ts",
        "F:/Dev/Narrative-Engine/frontend/src/services/mocks/foundationMock.ts"
      ]
    },
    "utilized_features": [
      "existing React local state form pattern",
      "current foundation mock service contract",
      "existing save/cancel callback shape"
    ],
    "expected_outcomes": [
      "`FoundationEditor` no longer references fields absent from the canonical foundation type.",
      "`onSave` emits a payload that can be passed to the existing foundation update flow without field translation."
    ],
    "execution_constraints": {
      "mode": "serial",
      "serial_after": [
        "b8a8be60-2b86-49db-8ea6-90522c597eff"
      ],
      "serial_notes": "Run only after the foundation type contract is corrected."
    },
    "guardrails": [
      "Do not introduce new routes or workspace tabs here.",
      "Do not change the mock service file in this task.",
      "Do not leave placeholder form fields that have no backing contract."
    ]
  },
  {
    "task_id": "421cf107-583b-4aeb-b90e-a2806c67055f",
    "purpose": "Align the character TypeScript contract with `charactersMock.ts` so character UI code uses the existing repository field names and relationship structures.",
    "responsible_file": "F:/Dev/Narrative-Engine/frontend/src/types/characters.ts",
    "knowledge_base": [
      "`CharacterProfile` and `RelationshipEdge` in `frontend/src/services/mocks/charactersMock.ts`",
      "frontend type conventions",
      "snake_case contract rules"
    ],
    "references_and_schema": {
      "input_data_schema": "Current mock shape in `frontend/src/services/mocks/charactersMock.ts`: `display_name`, `role_in_story`, `external_goal`, `internal_need`, `misbelief_or_wound`, `relationship_edges`, and related fields.",
      "output_data_schema": "Canonical exported interfaces that exactly match the current character mock service surface.",
      "external_refs": [
        "F:/Dev/Narrative-Engine/frontend/src/services/mocks/charactersMock.ts",
        "F:/Dev/Narrative-Engine/frontend/src/types/characters.ts",
        "F:/Dev/Narrative-Engine/AGENTS.md"
      ]
    },
    "utilized_features": [
      "existing `interface` type modules",
      "shared mock service contracts",
      "snake_case boundary preservation"
    ],
    "expected_outcomes": [
      "`frontend/src/types/characters.ts` matches the current character mock service without a competing simplified schema.",
      "Relationship-edge typing is shared directly with character UI code."
    ],
    "execution_constraints": {
      "mode": "parallel",
      "serial_after": [],
      "serial_notes": "This contract task must complete before `CharacterBuilder.tsx` is rewritten."
    },
    "guardrails": [
      "Do not edit `frontend/src/services/mocks/charactersMock.ts` in this task.",
      "Do not introduce new fields that are not backed by existing mock or backend code.",
      "Keep this file limited to types."
    ]
  },
  {
    "task_id": "1982a23d-f9d2-4ff9-8603-fed1379061dd",
    "purpose": "Refactor `CharacterBuilder` to edit the existing character contract rather than the incompatible simplified fields added on this branch.",
    "responsible_file": "F:/Dev/Narrative-Engine/frontend/src/components/characters/CharacterBuilder.tsx",
    "knowledge_base": [
      "`CharacterBuilder` form state and callbacks",
      "canonical character interface from `frontend/src/types/characters.ts`",
      "existing character mock service fields in `frontend/src/services/mocks/charactersMock.ts`"
    ],
    "references_and_schema": {
      "input_data_schema": "Aligned character interfaces exported from `frontend/src/types/characters.ts`.",
      "output_data_schema": "Form state and callback payloads that use the repository's existing character field names.",
      "external_refs": [
        "F:/Dev/Narrative-Engine/frontend/src/components/characters/CharacterBuilder.tsx",
        "F:/Dev/Narrative-Engine/frontend/src/types/characters.ts",
        "F:/Dev/Narrative-Engine/frontend/src/services/mocks/charactersMock.ts"
      ]
    },
    "utilized_features": [
      "existing React controlled form pattern",
      "current character mock contract",
      "existing save/delete/cancel callback pattern"
    ],
    "expected_outcomes": [
      "`CharacterBuilder` no longer emits fields like `name`, `description`, or `arc` if those are not part of the canonical character contract.",
      "Saved payloads can flow into the existing character mock/update surface without adapter code."
    ],
    "execution_constraints": {
      "mode": "serial",
      "serial_after": [
        "421cf107-583b-4aeb-b90e-a2806c67055f"
      ],
      "serial_notes": "Run after the shared character type file is corrected."
    },
    "guardrails": [
      "Do not edit the character mock service in this task.",
      "Do not add relationship-management behavior outside this component's current scope.",
      "Do not leave no-op buttons or disconnected fields."
    ]
  },
  {
    "task_id": "68b5205b-a526-4532-b640-7e4159617f6d",
    "purpose": "Replace the simplified world-bible type with a contract that matches the existing mock data layer so world-bible UI can operate on `entry_id`, `entry_type`, and related fields directly.",
    "responsible_file": "F:/Dev/Narrative-Engine/frontend/src/types/bible.ts",
    "knowledge_base": [
      "`WorldBibleEntry` shape in `frontend/src/services/mocks/worldBibleMock.ts`",
      "frontend type module patterns",
      "snake_case contract rules"
    ],
    "references_and_schema": {
      "input_data_schema": "Current mock shape in `frontend/src/services/mocks/worldBibleMock.ts`: `entry_id`, `project_id`, `entry_type`, `title`, `summary`, `canonical_facts`, `related_character_ids`, `source_artifacts`, `visibility_scope`, `continuity_warnings`, `writer_notes`.",
      "output_data_schema": "A canonical world-bible type module aligned with existing mock/backend semantics.",
      "external_refs": [
        "F:/Dev/Narrative-Engine/frontend/src/services/mocks/worldBibleMock.ts",
        "F:/Dev/Narrative-Engine/frontend/src/types/bible.ts",
        "F:/Dev/Narrative-Engine/AGENTS.md"
      ]
    },
    "utilized_features": [
      "existing type modules",
      "shared mock service contracts",
      "snake_case boundary preservation"
    ],
    "expected_outcomes": [
      "`frontend/src/types/bible.ts` exports types directly compatible with `getWorldBible`, `createWorldBibleEntry`, and `updateWorldBibleEntry`.",
      "Fields like `id`, `type`, and `details` are removed or replaced if they are not part of the canonical world-bible contract."
    ],
    "execution_constraints": {
      "mode": "parallel",
      "serial_after": [],
      "serial_notes": "This contract task must complete before `WorldBibleWorkspace.tsx` is aligned."
    },
    "guardrails": [
      "Do not edit the mock service file in this task.",
      "Do not invent a second world-bible schema for UI convenience.",
      "Keep this file limited to type definitions."
    ]
  },
  {
    "task_id": "8a781345-3360-4e32-92c6-887de2cd29a6",
    "purpose": "Refactor `WorldBibleWorkspace` to consume the canonical world-bible contract and existing mock semantics instead of the incompatible simplified entry model introduced on this branch.",
    "responsible_file": "F:/Dev/Narrative-Engine/frontend/src/components/bible/WorldBibleWorkspace.tsx",
    "knowledge_base": [
      "`WorldBibleWorkspace` list/editor interactions",
      "canonical world-bible types from `frontend/src/types/bible.ts`",
      "existing world-bible mock service contract in `frontend/src/services/mocks/worldBibleMock.ts`"
    ],
    "references_and_schema": {
      "input_data_schema": "Aligned `WorldBibleEntry` contract from `frontend/src/types/bible.ts`.",
      "output_data_schema": "Workspace interactions that read and write canonical world-bible fields only.",
      "external_refs": [
        "F:/Dev/Narrative-Engine/frontend/src/components/bible/WorldBibleWorkspace.tsx",
        "F:/Dev/Narrative-Engine/frontend/src/types/bible.ts",
        "F:/Dev/Narrative-Engine/frontend/src/services/mocks/worldBibleMock.ts"
      ]
    },
    "utilized_features": [
      "existing React list/editor patterns",
      "current world-bible mock service contract",
      "existing save/delete/cancel callback flow"
    ],
    "expected_outcomes": [
      "`WorldBibleWorkspace` no longer relies on `id`, `type`, or `details` if those are not in the canonical contract.",
      "Entry add/edit/delete interactions emit canonical world-bible payloads that match the existing service layer."
    ],
    "execution_constraints": {
      "mode": "serial",
      "serial_after": [
        "68b5205b-a526-4532-b640-7e4159617f6d"
      ],
      "serial_notes": "Run after the world-bible type contract is corrected."
    },
    "guardrails": [
      "Do not edit the world-bible mock service in this task.",
      "Do not add new workspace routes here.",
      "Do not keep placeholder editor fields that are unsupported by the canonical schema."
    ]
  },
  {
    "task_id": "7507c266-688d-4afb-849d-6fc9294ea05c",
    "purpose": "Remove the unsafe `as BrainstormItem` cast and fix user-facing mojibake in `BrainstormWorkspace` so the component only emits real persisted items and production-ready copy.",
    "responsible_file": "F:/Dev/Narrative-Engine/frontend/src/components/brainstorm/BrainstormWorkspace.tsx",
    "knowledge_base": [
      "`BrainstormWorkspace` callback flow",
      "`BrainstormItem` and `BrainstormItemCreateRequest` in `frontend/src/types/brainstorm.ts`",
      "current mock creation semantics in `frontend/src/services/mocks/brainstormMock.ts`"
    ],
    "references_and_schema": {
      "input_data_schema": "`BrainstormItemCreateRequest` input for create operations and canonical `BrainstormItem` output returned after persistence.",
      "output_data_schema": "UI callbacks that distinguish create requests from saved item records and only display valid UTF-8 strings.",
      "external_refs": [
        "F:/Dev/Narrative-Engine/frontend/src/components/brainstorm/BrainstormWorkspace.tsx",
        "F:/Dev/Narrative-Engine/frontend/src/types/brainstorm.ts",
        "F:/Dev/Narrative-Engine/frontend/src/services/mocks/brainstormMock.ts"
      ]
    },
    "utilized_features": [
      "existing React callback patterns",
      "current brainstorm mock contract",
      "typed create-request vs saved-record separation"
    ],
    "expected_outcomes": [
      "`onItemAdd` is no longer called with `newItem as BrainstormItem`.",
      "Visible strings such as bullets, arrows, and promoted labels render as valid text instead of mojibake."
    ],
    "execution_constraints": {
      "mode": "parallel",
      "serial_after": [],
      "serial_notes": "This can run independently of the foundation/character/world-bible alignment tasks."
    },
    "guardrails": [
      "Do not change `frontend/src/services/mocks/brainstormMock.ts` in this task.",
      "Do not invent new brainstorm service APIs.",
      "Keep the fix limited to callback correctness and text cleanup."
    ]
  },
  {
    "task_id": "a9f9b18e-dcea-4d0a-b6a3-5e5a0f329352",
    "purpose": "Finish the manuscript-aids container by replacing placeholder diff/history content with the existing `DiffViewer` and `SuggestionHistory` components and cleaning the corrupted arrow text.",
    "responsible_file": "F:/Dev/Narrative-Engine/frontend/src/components/aids/AidsPanel.tsx",
    "knowledge_base": [
      "`AidsPanel` tab state and selected suggestion flow",
      "`DiffViewer` props in `frontend/src/components/aids/DiffViewer.tsx`",
      "`SuggestionHistory` props in `frontend/src/components/aids/SuggestionHistory.tsx`",
      "`RevisionSuggestion` shape in `frontend/src/types/aids.ts`"
    ],
    "references_and_schema": {
      "input_data_schema": "Current `RevisionSuggestion[]` prop plus selected suggestion id held in `AidsPanel` local state.",
      "output_data_schema": "Aids tab content that renders real diff and history child components instead of placeholder text.",
      "external_refs": [
        "F:/Dev/Narrative-Engine/frontend/src/components/aids/AidsPanel.tsx",
        "F:/Dev/Narrative-Engine/frontend/src/components/aids/DiffViewer.tsx",
        "F:/Dev/Narrative-Engine/frontend/src/components/aids/SuggestionHistory.tsx",
        "F:/Dev/Narrative-Engine/frontend/src/types/aids.ts"
      ]
    },
    "utilized_features": [
      "existing tab state in `AidsPanel`",
      "existing `DiffViewer` component",
      "existing `SuggestionHistory` component"
    ],
    "expected_outcomes": [
      "The diff tab renders `DiffViewer` using the currently selected suggestion instead of placeholder copy.",
      "The history tab renders `SuggestionHistory` instead of hand-rolled accepted/rejected lists.",
      "Corrupted arrow text is replaced with valid UTF-8 or ASCII copy."
    ],
    "execution_constraints": {
      "mode": "parallel",
      "serial_after": [],
      "serial_notes": "This task depends only on already existing aids child components."
    },
    "guardrails": [
      "Do not change `DiffViewer.tsx` or `SuggestionHistory.tsx` in this task.",
      "Do not add new tabs or speculative manuscript features.",
      "Keep this file limited to composition, tab content, and copy cleanup."
    ]
  },
  {
    "task_id": "171704f3-530c-4501-b46b-84170f50153f",
    "purpose": "Integrate the newly added brainstorm, foundation, character, and world-bible surfaces into the routed workspace so the committed UI becomes reachable from the existing `/workspace/:projectId/*` flow.",
    "responsible_file": "F:/Dev/Narrative-Engine/frontend/src/views/PlanningView.tsx",
    "knowledge_base": [
      "`PlanningView` tab routing and `activeTab` state",
      "existing `projectId` route param usage",
      "new component exports in `frontend/src/components/brainstorm`, `foundation`, `characters`, and `bible`"
    ],
    "references_and_schema": {
      "input_data_schema": "Current `PlanningView` tab state machine and `projectId` route parameter from React Router.",
      "output_data_schema": "A deterministic workspace tab surface where each newly committed component is reachable through an explicit view state.",
      "external_refs": [
        "F:/Dev/Narrative-Engine/frontend/src/views/PlanningView.tsx",
        "F:/Dev/Narrative-Engine/frontend/src/App.tsx",
        "F:/Dev/Narrative-Engine/frontend/src/components/brainstorm/BrainstormWorkspace.tsx",
        "F:/Dev/Narrative-Engine/frontend/src/components/foundation/FoundationEditor.tsx",
        "F:/Dev/Narrative-Engine/frontend/src/components/characters/CharacterBuilder.tsx",
        "F:/Dev/Narrative-Engine/frontend/src/components/bible/WorldBibleWorkspace.tsx"
      ]
    },
    "utilized_features": [
      "existing `activeTab` state pattern in `PlanningView`",
      "current workspace route structure",
      "current project-id param flow"
    ],
    "expected_outcomes": [
      "Each newly committed surface is reachable from the existing workspace view without adding dead-end routes.",
      "The branch no longer consists of unreachable UI files only."
    ],
    "execution_constraints": {
      "mode": "serial",
      "serial_after": [
        "a2f41946-7f8f-4873-adb4-454eb0750b30",
        "1982a23d-f9d2-4ff9-8603-fed1379061dd",
        "8a781345-3360-4e32-92c6-887de2cd29a6",
        "7507c266-688d-4afb-849d-6fc9294ea05c",
        "a9f9b18e-dcea-4d0a-b6a3-5e5a0f329352"
      ],
      "serial_notes": "Run after the individual component contracts are corrected, because this file is the final integration point."
    },
    "guardrails": [
      "Do not create new top-level routes in `App.tsx` for this task unless strictly required by the existing workspace architecture.",
      "Do not add placeholder tabs that render empty shells.",
      "Only expose components that are backed by existing in-repo services or mock services."
    ]
  },
  {
    "task_id": "38ce4a79-5e47-4c47-8764-8167f500a70c",
    "purpose": "Add deterministic validation coverage for the new text-diff logic so the executor can prove the diff helper returns stable change summaries for equal, insert, delete, and replace cases.",
    "responsible_file": "F:/Dev/Narrative-Engine/frontend/src/lib/diff.ts",
    "knowledge_base": [
      "`computeDiff`, `formatDiff`, and `getDiffSummary` in `frontend/src/lib/diff.ts`",
      "existing frontend validation commands: `npm run lint`, `npm run typecheck`, `npm run build`",
      "current absence of dedicated frontend test infrastructure in `frontend/package.json`"
    ],
    "references_and_schema": {
      "input_data_schema": "String inputs consumed by `computeDiff(original, modified)`.",
      "output_data_schema": "Deterministic helper behavior documented in code comments or inline self-check scaffolding without introducing unsupported tooling.",
      "external_refs": [
        "F:/Dev/Narrative-Engine/frontend/src/lib/diff.ts",
        "F:/Dev/Narrative-Engine/frontend/package.json"
      ]
    },
    "utilized_features": [
      "existing TypeScript helper module",
      "current repo validation gate"
    ],
    "expected_outcomes": [
      "`computeDiff` behavior for equal, insert, delete, and replace cases is explicitly documented or codified in the file using only supported repo tooling.",
      "No unsupported test framework is introduced as part of this task."
    ],
    "execution_constraints": {
      "mode": "parallel",
      "serial_after": [],
      "serial_notes": "Independent hardening task; it does not block the contract-alignment chain."
    },
    "guardrails": [
      "Do not add Vitest, Jest, or any other new test runner in this task.",
      "Do not modify `frontend/package.json`.",
      "Limit work to `frontend/src/lib/diff.ts` only."
    ]
  }
]
