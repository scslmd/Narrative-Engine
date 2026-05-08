# Guided Setup Readiness Detection — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Surface the LLM's `ready_to_create` signal as a prominent visual state so users know when they have enough data to save their project.

**Architecture:** Pure frontend changes across 4 files. Store tracks `wasReadyBefore` flag to fire a one-time readiness notification. ChatPanel shows readiness badge and category count. FieldPreview renders per-category completeness bars. GuidedSetupView button switches between "Save What You Have" and "Save Project" states.

**Tech Stack:** React, TypeScript, Zustand, Vitest, Testing Library, Tailwind CSS

---

### Task 1: Store — wasReadyBefore tracking and readiness notification

**Files:**
- Modify: `frontend/src/stores/guidedSetupStore.ts`
- Create: `frontend/src/stores/guidedSetupStore.test.ts`

**Changes to `guidedSetupStore.ts`:**

Add `wasReadyBefore: boolean` to state interface (default `false`). In `handleAnalyze`, after receiving LLM response, check if `ready_to_create` flipped from false to true. If so, inject a system message into conversation history and set `wasReadyBefore = true`.

Reset `wasReadyBefore` in the `reset()` function.

- [ ] **Step 1: Write failing test for wasReadyBefore tracking**

Create `frontend/src/stores/guidedSetupStore.test.ts`:

```typescript
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { act } from '@testing-library/react';
import { useGuidedSetupStore } from './guidedSetupStore';
import * as guidedSetup from '../services/guidedSetup';

describe('guidedSetupStore', () => {
  beforeEach(() => {
    useGuidedSetupStore.reset();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('starts with wasReadyBefore false', () => {
    const state = useGuidedSetupStore.getState();
    expect(state.readyToCreate).toBe(false);
  });

  it('sets readyToCreate when LLM returns true', async () => {
    const mockResponse = {
      extracted_fields: guidedSetup.emptyExtractedFields(),
      next_question: 'Any more details?',
      confidence: 0.9,
      progress: 85,
      ready_to_create: true,
      category_progress: [],
    };

    vi.spyOn(guidedSetup, 'analyzeTurn').mockResolvedValue(mockResponse);

    await act(async () => {
      await useGuidedSetupStore.getState().handleAnalyze('test answer');
    });

    const state = useGuidedSetupStore.getState();
    expect(state.readyToCreate).toBe(true);
  });

  it('injects readiness notification when ready flips from false to true', async () => {
    const mockResponse = {
      extracted_fields: guidedSetup.emptyExtractedFields(),
      next_question: 'Any more details?',
      confidence: 0.9,
      progress: 85,
      ready_to_create: true,
      category_progress: [],
    };

    vi.spyOn(guidedSetup, 'analyzeTurn').mockResolvedValue(mockResponse);

    await act(async () => {
      await useGuidedSetupStore.getState().handleAnalyze('first answer');
    });

    const state = useGuidedSetupStore.getState();
    const systemMessages = state.conversationHistory.filter(m => m.role === 'system');
    const readinessMessage = systemMessages.find(m =>
      m.content.includes('enough to create') || m.content.includes('ready')
    );
    expect(readinessMessage).toBeDefined();
  });

  it('does not re-inject notification when already ready', async () => {
    const mockResponse = {
      extracted_fields: guidedSetup.emptyExtractedFields(),
      next_question: 'Any more details?',
      confidence: 0.9,
      progress: 90,
      ready_to_create: true,
      category_progress: [],
    };

    vi.spyOn(guidedSetup, 'analyzeTurn').mockResolvedValue(mockResponse);

    await act(async () => {
      await useGuidedSetupStore.getState().handleAnalyze('first answer');
    });

    const notificationsAfterFirst = useGuidedSetupStore.getState()
      .conversationHistory.filter(m =>
        m.role === 'system' && (m.content.includes('enough to create') || m.content.includes('ready'))
      ).length;

    await act(async () => {
      await useGuidedSetupStore.getState().handleAnalyze('second answer');
    });

    const notificationsAfterSecond = useGuidedSetupStore.getState()
      .conversationHistory.filter(m =>
        m.role === 'system' && (m.content.includes('enough to create') || m.content.includes('ready'))
      ).length;

    expect(notificationsAfterSecond).toBe(notificationsAfterFirst);
  });

  it('reset clears wasReadyBefore', () => {
    act(() => {
      useGuidedSetupStore.getState().setProgress(80, 0.9, true, []);
    });
    useGuidedSetupStore.reset();
    const state = useGuidedSetupStore.getState();
    expect(state.readyToCreate).toBe(false);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npm run test -- guidedSetupStore.test.ts -t "starts with wasReadyBefore"`
Expected: Test may pass for initial state, but readiness notification tests should fail since the logic isn't implemented yet.

- [ ] **Step 3: Implement wasReadyBefore in guidedSetupStore.ts**

In the `GuidedSetupState` interface, add:
```typescript
wasReadyBefore: boolean;
```

In the initial state object, add:
```typescript
wasReadyBefore: false,
```

In the `reset()` function, add to the reset object:
```typescript
wasReadyBefore: false,
```

In `handleAnalyze`, replace the response processing `set(...)` block (currently lines 136-149 in `guidedSetupStore.ts`) with readiness flip detection.

The existing block looks like:
```typescript
      const currentTurn = get().turnCount;
      set({
        accumulatedFields: response.extracted_fields,
        nextQuestion: response.next_question,
        progress: response.progress,
        confidence: response.confidence,
        readyToCreate: response.ready_to_create,
        categoryProgress: response.category_progress,
        conversationHistory: [
          ...get().conversationHistory,
          { role: 'system' as const, content: response.next_question, turn: currentTurn + 1 },
        ],
        turnCount: currentTurn + 1,
      });
```

Replace with:
```typescript
      const wasReady = get().wasReadyBefore;
      const newlyReady = response.ready_to_create && !wasReady;

      const currentTurn = get().turnCount;
      const extraMessages: ChatMessage[] = [];
      if (newlyReady) {
        extraMessages.push({
          role: 'system' as const,
          content: "I think we have enough to create your project. You can review the fields on the right and save whenever you're ready.",
          turn: currentTurn + 2,
        });
      }

      set({
        accumulatedFields: response.extracted_fields,
        nextQuestion: response.next_question,
        progress: response.progress,
        confidence: response.confidence,
        readyToCreate: response.ready_to_create,
        categoryProgress: response.category_progress,
        wasReadyBefore: response.ready_to_create || wasReady,
        conversationHistory: [
          ...get().conversationHistory,
          { role: 'system' as const, content: response.next_question, turn: currentTurn + 1 },
          ...extraMessages,
        ],
        turnCount: currentTurn + 1 + extraMessages.length,
      });
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd frontend && npm run test -- guidedSetupStore.test.ts`
Expected: All 5 tests pass

- [ ] **Step 5: Commit**

```bash
git add frontend/src/stores/guidedSetupStore.ts frontend/src/stores/guidedSetupStore.test.ts
git commit -m "feat: track wasReadyBefore and inject readiness notification in guided setup store"
```

---

### Task 2: ChatPanel — readiness badge, progress bar color, category count

**Files:**
- Modify: `frontend/src/components/guided-setup/ChatPanel.tsx`
- Create: `frontend/src/components/guided-setup/ChatPanel.test.tsx`

**Changes to `ChatPanel.tsx`:**

Add `readyToCreate` and `categoryProgress` props. Update header to show readiness badge or category count. Change progress bar gradient based on readiness.

- [ ] **Step 1: Write failing tests for ChatPanel readiness UI**

Create `frontend/src/components/guided-setup/ChatPanel.test.tsx`:

```typescript
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '../../__tests__/test-utils';
import { ChatPanel } from './ChatPanel';
import type { CategoryProgress } from '../../services/guidedSetup';

const mockCategoryProgress: CategoryProgress[] = [
  { category: 'config', completeness: 0.8, confidence: 0.9, fields_collected: ['genre'], fields_missing: [] },
  { category: 'foundation', completeness: 0.7, confidence: 0.8, fields_collected: ['premise_text'], fields_missing: [] },
  { category: 'characters', completeness: 0.9, confidence: 0.9, fields_collected: ['protagonist'], fields_missing: [] },
  { category: 'world_bible', completeness: 0.5, confidence: 0.6, fields_collected: [], fields_missing: ['setting'] },
  { category: 'arcs', completeness: 0.7, confidence: 0.7, fields_collected: [], fields_missing: [] },
];

function renderChatPanel(overrides = {}) {
  return render(
    <ChatPanel
      onSend={vi.fn().mockResolvedValue(undefined)}
      isLoading={false}
      readyToCreate={false}
      progress={50}
      categoryProgress={[]}
      {...overrides}
    />
  );
}

describe('ChatPanel', () => {
  it('shows readiness badge when readyToCreate is true', async () => {
    renderChatPanel({
      readyToCreate: true,
      progress: 85,
      categoryProgress: mockCategoryProgress,
    });

    await vi.waitFor(() => {
      expect(screen.getByText('Ready to Save')).toBeInTheDocument();
    });
  });

  it('shows category readiness count when not ready but has progress', async () => {
    renderChatPanel({
      readyToCreate: false,
      progress: 50,
      categoryProgress: mockCategoryProgress,
    });

    await vi.waitFor(() => {
      expect(screen.getByText('4/5 categories ready')).toBeInTheDocument();
    });
  });

  it('shows percentage when no category progress available', async () => {
    renderChatPanel({
      readyToCreate: false,
      progress: 35,
      categoryProgress: [],
    });

    await vi.waitFor(() => {
      expect(screen.getByText('35% complete')).toBeInTheDocument();
    });
  });

  it('uses emerald gradient for progress bar when ready', () => {
    const { container } = renderChatPanel({
      readyToCreate: true,
      progress: 85,
      categoryProgress: mockCategoryProgress,
    });

    const progressBar = container.querySelector('[class*="from-emerald"]');
    expect(progressBar).toBeInTheDocument();
  });

  it('uses violet gradient for progress bar when not ready', () => {
    const { container } = renderChatPanel({
      readyToCreate: false,
      progress: 50,
      categoryProgress: mockCategoryProgress,
    });

    const progressBar = container.querySelector('[class*="from-violet"]');
    expect(progressBar).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npm run test -- ChatPanel.test.tsx -t "shows readiness badge"`
Expected: FAIL — `readyToCreate` prop doesn't exist yet, and "Ready to Save" text isn't rendered

- [ ] **Step 3: Implement readiness UI in ChatPanel.tsx**

Update the `ChatPanelProps` interface:

```typescript
import type { CategoryProgress } from '../../services/guidedSetup';

interface ChatPanelProps {
  onSend: (message: string) => Promise<void>;
  isLoading: boolean;
  readyToCreate: boolean;
  progress: number;
  categoryProgress: CategoryProgress[];
}
```

Update the component signature:

```typescript
export function ChatPanel({ onSend, isLoading, readyToCreate, progress, categoryProgress }: ChatPanelProps): React.ReactElement {
```

Replace the header section (lines 60-80) with:

```typescript
<div className={`px-4 py-3 border-b transition-colors duration-300 ${
  readyToCreate
    ? 'border-emerald-200 dark:border-emerald-800 bg-emerald-50/50 dark:bg-emerald-900/10'
    : 'border-gray-200 dark:border-gray-700'
}`}>
  <div className="flex items-center justify-between">
    <div className="flex items-center gap-2">
      <Sparkles className="w-5 h-5 text-violet-500" />
      <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
        Story Architect
      </h2>
    </div>
    <div className="flex items-center gap-3">
      {readyToCreate ? (
        <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800">
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
          </svg>
          Ready to Save
        </span>
      ) : categoryProgress.length > 0 ? (
        <span className="text-sm text-gray-500 dark:text-gray-400">
          {categoryProgress.filter(c => c.completeness >= 0.7).length}/5 categories ready
        </span>
      ) : (
        <span className="text-sm text-gray-500 dark:text-gray-400">
          {Math.round(progress)}% complete
        </span>
      )}
      <div className="w-24 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-300 ${
            readyToCreate
              ? 'bg-gradient-to-r from-emerald-400 to-teal-500'
              : 'bg-gradient-to-r from-violet-500 to-purple-500'
          }`}
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  </div>
</div>
```

Remove the `progress` import from store since it's now passed as prop. Update line 30:
```typescript
const { conversationHistory } = useGuidedSetupStore();
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd frontend && npm run test -- ChatPanel.test.tsx`
Expected: All 5 tests pass

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/guided-setup/ChatPanel.tsx frontend/src/components/guided-setup/ChatPanel.test.tsx
git commit -m "feat: add readiness badge, category count, and dynamic progress bar to ChatPanel"
```

---

### Task 3: FieldPreview — per-category completeness bars and missing field tags

**Files:**
- Modify: `frontend/src/components/guided-setup/FieldPreview.tsx`
- Create: `frontend/src/components/guided-setup/FieldPreview.test.tsx`

**Changes to `FieldPreview.tsx`:**

Add `categoryProgress` prop. For each of the 5 mapped categories, show a mini completeness bar in the section header and missing field tags when completeness < 0.7.

- [ ] **Step 1: Write failing tests for FieldPreview completeness bars**

Create `frontend/src/components/guided-setup/FieldPreview.test.tsx`:

```typescript
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '../../__tests__/test-utils';
import { FieldPreview } from './FieldPreview';
import type { CategoryProgress } from '../../services/guidedSetup';

const mockCategoryProgress: CategoryProgress[] = [
  { category: 'config', completeness: 0.8, confidence: 0.9, fields_collected: ['genre', 'project_name'], fields_missing: [] },
  { category: 'foundation', completeness: 0.4, confidence: 0.6, fields_collected: ['premise_text'], fields_missing: ['logline', 'thematic_spine'] },
  { category: 'characters', completeness: 0.9, confidence: 0.9, fields_collected: ['protagonist'], fields_missing: [] },
  { category: 'world_bible', completeness: 0.2, confidence: 0.3, fields_collected: [], fields_missing: ['setting', 'world rules'] },
  { category: 'arcs', completeness: 0.7, confidence: 0.7, fields_collected: [], fields_missing: [] },
];

function renderFieldPreview(overrides = {}) {
  return render(
    <FieldPreview categoryProgress={[]} {...overrides} />
  );
}

describe('FieldPreview', () => {
  it('shows completeness bars for categories with progress data', async () => {
    renderFieldPreview({ categoryProgress: mockCategoryProgress });

    await vi.waitFor(() => {
      expect(screen.getByText('Project Config')).toBeInTheDocument();
    });
  });

  it('shows missing field tags when completeness is below 0.7', async () => {
    renderFieldPreview({ categoryProgress: mockCategoryProgress });

    await vi.waitFor(() => {
      expect(screen.getByText('Foundation')).toBeInTheDocument();
      const missingTag = screen.queryByText(/logline/);
      expect(missingTag).toBeInTheDocument();
    });
  });

  it('does not show missing tags when category is complete', async () => {
    const completeProgress: CategoryProgress[] = [
      { category: 'config', completeness: 0.9, confidence: 0.9, fields_collected: ['genre'], fields_missing: [] },
    ];
    renderFieldPreview({ categoryProgress: completeProgress });

    await vi.waitFor(() => {
      expect(screen.getByText('Project Config')).toBeInTheDocument();
    });
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npm run test -- FieldPreview.test.tsx -t "shows completeness bars"`
Expected: FAIL — `categoryProgress` prop doesn't exist on FieldPreview yet

- [ ] **Step 3: Implement completeness bars in FieldPreview.tsx**

Add imports at top of file:
```typescript
import type { CategoryProgress } from '../../services/guidedSetup';
```

Update `FieldPreview` component to accept and use the prop:

```typescript
export function FieldPreview({ categoryProgress = [] }: { categoryProgress?: CategoryProgress[] }): React.ReactElement {
```

Add helper function before `FieldPreview`:

```typescript
function getCategoryCompleteness(category: string, categoryProgress: CategoryProgress[]): CategoryProgress | null {
  return categoryProgress.find(cp => cp.category === category) ?? null;
}

function completenessColor(completeness: number): string {
  if (completeness >= 0.7) return 'bg-emerald-500';
  if (completeness >= 0.3) return 'bg-amber-500';
  return 'bg-gray-400';
}
```

Add a `CategoryBar` component:

```typescript
function CategoryBar({ completeness, missingFields }: { completeness: number; missingFields: string[] }) {
  return (
    <>
      <div className="w-12 h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-300 ${completenessColor(completeness)}`}
          style={{ width: `${completeness * 100}%` }}
        />
      </div>
      {missingFields.length > 0 && (
        <div className="flex flex-wrap gap-1 mt-1">
          {missingFields.map(f => (
            <span key={f} className="text-[10px] px-1.5 py-0.5 bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 rounded">
              {f}
            </span>
          ))}
        </div>
      )}
    </>
  );
}
```

Update each collapsible section to include the bar. For example, the "Project Config" section becomes:

```typescript
{(() => {
  const cp = getCategoryCompleteness('config', categoryProgress);
  return (
    <CollapsibleSection title="Project Config" icon={<Settings className="w-4 h-4" />} defaultOpen>
      {cp && <CategoryBar completeness={cp.completeness} missingFields={cp.fields_missing} />}
      <FieldRow label="Name" value={config.project_name} editable onChange={(v) => updateFields({ config: { project_name: v } })} />
      {/* ... rest unchanged ... */}
    </CollapsibleSection>
  );
})()}
```

Apply the same pattern to Foundation (`foundation`), Characters (`characters`), World (`world_bible`), and Arcs (`arcs`) sections. Do NOT add bars to Sequences and Chapters sections (they have no category_progress entries).

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd frontend && npm run test -- FieldPreview.test.tsx`
Expected: All 3 tests pass

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/guided-setup/FieldPreview.tsx frontend/src/components/guided-setup/FieldPreview.test.tsx
git commit -m "feat: add per-category completeness bars and missing field tags to FieldPreview"
```

---

### Task 4: GuidedSetupView — dual-state action button

**Files:**
- Modify: `frontend/src/views/GuidedSetupView.tsx`
- Create: `frontend/src/views/GuidedSetupView.test.tsx`

**Changes to `GuidedSetupView.tsx`:**

Replace the single "Create Project" button with two states based on `readyToCreate`. Wire up new props to ChatPanel and FieldPreview.

- [ ] **Step 1: Write failing tests for dual-state button**

Create `frontend/src/views/GuidedSetupView.test.tsx`:

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '../__tests__/test-utils';
import { act } from '@testing-library/react';
import { GuidedSetupView } from './GuidedSetupView';
import { useGuidedSetupStore } from '../stores/guidedSetupStore';
import { useGuidedSetup } from '../hooks/useGuidedSetup';
import * as guidedSetup from '../services/guidedSetup';

vi.mock('../hooks/useGuidedSetup', () => ({
  useGuidedSetup: vi.fn(),
}));

vi.mock('../services/guidedSetup', () => ({
  checkLlmHealth: vi.fn().mockResolvedValue({ ok: true, backend: 'llama.cpp', model: 'test' }),
  analyzeTurn: vi.fn().mockResolvedValue({}),
  createFromFields: vi.fn().mockResolvedValue({}),
  emptyExtractedFields: vi.fn().mockReturnValue({}),
}));

describe('GuidedSetupView', () => {
  beforeEach(() => {
    useGuidedSetupStore.reset();
  });

  it('shows "Save What You Have" button when not ready but has content', async () => {
    act(() => {
      useGuidedSetupStore.setState({
        accumulatedFields: {
          config: { project_name: 'Test Project', genre: '', tone_profile: '', pov: '', story_structure: '', primary_language: '', secondary_language: null, constraints: [] },
          foundation: { premise_text: '', logline: '', thematic_spine: '', emotional_promise: '', target_audience: '', complexity_level: '', success_definition: '', narrative_constraints: [] },
          characters: [],
          world_bible: [],
          arcs: [],
          sequences: [],
          chapters: [],
        },
        conversationHistory: [{ role: 'system', content: 'Hello', turn: 1 }],
        readyToCreate: false,
      });
    });

    vi.mocked(useGuidedSetup).mockReturnValue({
      isAnalyzing: false,
      createMutation: { isPending: false },
      handleAnalyze: vi.fn().mockResolvedValue(undefined),
      handleSubmitCreate: vi.fn(),
    } as any);

    render(<GuidedSetupView />, { route: '/setup-wizard' });

    await vi.waitFor(() => {
      expect(screen.getByText('Save What You Have')).toBeInTheDocument();
    });
  });

  it('shows "Save Project" button when readyToCreate is true', async () => {
    act(() => {
      useGuidedSetupStore.setState({
        accumulatedFields: {
          config: { project_name: 'Test Project', genre: '', tone_profile: '', pov: '', story_structure: '', primary_language: '', secondary_language: null, constraints: [] },
          foundation: { premise_text: '', logline: '', thematic_spine: '', emotional_promise: '', target_audience: '', complexity_level: '', success_definition: '', narrative_constraints: [] },
          characters: [],
          world_bible: [],
          arcs: [],
          sequences: [],
          chapters: [],
        },
        conversationHistory: [{ role: 'system', content: 'Hello', turn: 1 }],
        readyToCreate: true,
      });
    });

    vi.mocked(useGuidedSetup).mockReturnValue({
      isAnalyzing: false,
      createMutation: { isPending: false },
      handleAnalyze: vi.fn().mockResolvedValue(undefined),
      handleSubmitCreate: vi.fn(),
    } as any);

    render(<GuidedSetupView />, { route: '/setup-wizard' });

    await vi.waitFor(() => {
      expect(screen.getByText('Save Project')).toBeInTheDocument();
    });
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npm run test -- GuidedSetupView.test.tsx -t "Save What You Have"`
Expected: FAIL — button text "Save What You Have" doesn't exist yet

- [ ] **Step 3: Implement dual-state button in GuidedSetupView.tsx**

Update imports to include `Check` and `Save` from lucide-react:
```typescript
import { ArrowLeft, Loader2, Rocket, AlertTriangle, Check, Save } from 'lucide-react';
```

Update the component to read `readyToCreate` from store:
```typescript
const { accumulatedFields, conversationHistory, readyToCreate, categoryProgress } = useGuidedSetupStore();
```

Replace the button block (lines 78-93) with:

```typescript
{hasContent && !isCreating && (
  readyToCreate ? (
    <button
      onClick={handleCreate}
      className="flex items-center gap-2 px-6 py-2.5 bg-gradient-to-r from-violet-500 to-purple-500 text-white rounded-lg hover:from-violet-600 hover:to-purple-600 transition-all font-medium shadow-md"
    >
      <Check className="w-4 h-4" />
      Save Project
    </button>
  ) : (
    <button
      onClick={handleCreate}
      className="flex items-center gap-2 px-6 py-2.5 border border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-400 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-all font-medium"
    >
      <Save className="w-4 h-4" />
      Save What You Have
    </button>
  )
)}
```

Update the ChatPanel and FieldPreview usage to pass new props.

First, update the store destructuring (line 19) to include `readyToCreate`, `categoryProgress`, and `progress`:

```typescript
const { accumulatedFields, conversationHistory, readyToCreate, categoryProgress, progress } = useGuidedSetupStore();
```

Then update the component usage:

```typescript
<ChatPanel
  onSend={handleSend}
  isLoading={isAnalyzing}
  readyToCreate={readyToCreate}
  progress={progress}
  categoryProgress={categoryProgress}
/>
```

```typescript
<FieldPreview categoryProgress={categoryProgress} />
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd frontend && npm run test -- GuidedSetupView.test.tsx`
Expected: Both tests pass

- [ ] **Step 5: Commit**

```bash
git add frontend/src/views/GuidedSetupView.tsx frontend/src/views/GuidedSetupView.test.tsx
git commit -m "feat: dual-state save button and wire readiness props to guided setup components"
```

---

### Task 5: Integration verification and lint

**Files:**
- Verify all changed files work together

- [ ] **Step 1: Run full frontend test suite**

Run: `cd frontend && npm run test`
Expected: All tests pass (554+ new tests from this feature)

- [ ] **Step 2: Run lint check**

Run: `cd frontend && npm run lint`
Expected: 0 errors

- [ ] **Step 3: Run typecheck**

Run: `cd frontend && npm run typecheck`
Expected: 0 errors

- [ ] **Step 4: Run build**

Run: `cd frontend && npm run build`
Expected: Successful build, no errors

- [ ] **Step 5: Final commit if any fixes were needed**

```bash
git add -A
git commit -m "fix: address lint/typecheck issues from guided setup readiness feature"
```

---

## Self-Review

**1. Spec coverage:**
- Chat header readiness indicator (Task 2) — covers green border, badge, progress bar color, category count
- Dual-state button (Task 4) — covers "Save What You Have" vs "Save Project" with correct icons and styles
- Per-category completeness bars (Task 3) — covers bars, colors, missing field tags, category mapping
- Readiness notification (Task 1) — covers `wasReadyBefore` tracking, one-time system message injection
- Edge cases: LLM unavailable (button still shows as "Save What You Have"), ready flips back (button reverts), empty categoryProgress (falls back to percentage)

**2. Placeholder scan:** No TBDs, no vague language. All code blocks contain complete implementations. All test assertions are specific.

**3. Type consistency:**
- `CategoryProgress` type imported from `services/guidedSetup.ts` in all files — consistent
- `readyToCreate: boolean` used consistently across store, ChatPanel, FieldPreview, GuidedSetupView
- Prop names: `categoryProgress`, `readyToCreate`, `progress` — consistent with spec table

**4. No gaps found.** All 4 design sections have corresponding tasks. Task 5 verifies integration.
