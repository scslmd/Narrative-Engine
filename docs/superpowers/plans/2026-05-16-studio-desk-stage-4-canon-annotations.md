# Studio Desk Stage 4 Canon Annotation Parity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire existing canon annotation loading and creation into Studio character and world bible panels.

**Architecture:** Reuse `getCanonAnnotations` and `createCanonAnnotation` from `frontend/src/services/canonCustomization.ts`. Match the current `PlanningView` behavior for `target_kind: 'character'` and `target_kind: 'world_bible'`.

**Tech Stack:** React Query, existing canon customization service, CharacterBuilder, WorldBibleWorkspace, Vitest.

---

## Contract

| Task | Responsible file | Purpose |
| --- | --- | --- |
| S4-T001 | `frontend/src/components/studio/StudioCharactersPanel.tsx` | Load/create character annotations |
| S4-T002 | `frontend/src/components/studio/StudioWorldBiblePanel.tsx` | Load/create world bible annotations |
| S4-T003 | `frontend/src/views/StudioView.test.tsx` | Add annotation endpoint mocks |

## Guardrails

- Do not create new canon services.
- Do not change annotation type definitions.
- Do not change `CharacterBuilder` or `WorldBibleWorkspace` props.
- Do not add delete annotation behavior in this stage.

## Tasks

### S4-T001: Character Annotation Wiring

**Responsible file:** `frontend/src/components/studio/StudioCharactersPanel.tsx`

- [ ] Import:

```ts
import { createCanonAnnotation, getCanonAnnotations } from '../../services/canonCustomization';
```

- [ ] Add query:

```ts
const canonAnnotationsQuery = useQuery({
  queryKey: ['studio', 'canon', 'annotations', projectId, 'characters'],
  queryFn: () => getCanonAnnotations(projectId, { target_kind: 'character' }),
});
```

- [ ] Add mutation:

```ts
const canonAnnotationMutation = useMutation({
  mutationFn: createCanonAnnotation,
  onSuccess: () => {
    void queryClient.invalidateQueries({ queryKey: ['studio', 'canon', 'annotations', projectId, 'characters'] });
  },
});
```

- [ ] Pass `canonAnnotations={canonAnnotationsQuery.data ?? []}` to `CharacterBuilder`.
- [ ] Pass `onAnnotateField` that calls `canonAnnotationMutation.mutateAsync` with:

```ts
{
  project_id: projectId,
  target_kind: 'character',
  target_id: targetId,
  field_path: fieldPath,
  annotation_kind: annotationKind,
  note,
}
```

### S4-T002: World Bible Annotation Wiring

**Responsible file:** `frontend/src/components/studio/StudioWorldBiblePanel.tsx`

- [ ] Import:

```ts
import { createCanonAnnotation, getCanonAnnotations } from '../../services/canonCustomization';
```

- [ ] Add query:

```ts
const canonAnnotationsQuery = useQuery({
  queryKey: ['studio', 'canon', 'annotations', projectId, 'world-bible'],
  queryFn: () => getCanonAnnotations(projectId, { target_kind: 'world_bible' }),
});
```

- [ ] Add mutation:

```ts
const canonAnnotationMutation = useMutation({
  mutationFn: createCanonAnnotation,
  onSuccess: () => {
    void queryClient.invalidateQueries({ queryKey: ['studio', 'canon', 'annotations', projectId, 'world-bible'] });
  },
});
```
- [ ] Pass `canonAnnotations={canonAnnotationsQuery.data ?? []}` to `WorldBibleWorkspace`.
- [ ] Pass `onAnnotateField` that calls `canonAnnotationMutation.mutateAsync` with:

```ts
{
  project_id: projectId,
  target_kind: 'world_bible',
  target_id: targetId,
  field_path: fieldPath,
  annotation_kind: annotationKind,
  note,
}
```

### S4-T003: Update Studio Tests

**Responsible file:** `frontend/src/views/StudioView.test.tsx`

- [ ] Add MSW mocks for:

```ts
http.get('/v1/canon/annotations', () => HttpResponse.json([]))
http.post('/v1/canon/annotations', async () => HttpResponse.json({
  annotation_id: 'ann-1',
  project_id: 'proj-1',
  target_kind: 'character',
  target_id: 'char-1',
  field_path: 'display_name',
  annotation_kind: 'locked',
  note: 'test',
}))
```

- [ ] Keep existing Studio route tests passing.
- [ ] Add an assertion that opening the Characters panel triggers a GET request whose query string includes `target_kind=character`.
- [ ] Add an assertion that opening the World Bible panel triggers a GET request whose query string includes `target_kind=world_bible`.

## Final Verification

```powershell
cd frontend; cmd /c npm.cmd run lint
cd frontend; cmd /c npm.cmd run typecheck
cd frontend; cmd /c npm.cmd run build
cd frontend; cmd /c npm.cmd run test -- StudioView
```

Expected: all exit 0.

## Stage 4 Pass Criteria

Stage 4 is complete only when all of these are true:

- Studio character panel loads annotations through `getCanonAnnotations(projectId, { target_kind: 'character' })`.
- Studio character panel creates annotations through `createCanonAnnotation` with `target_kind: 'character'`.
- Studio world bible panel loads annotations through `getCanonAnnotations(projectId, { target_kind: 'world_bible' })`.
- Studio world bible panel creates annotations through `createCanonAnnotation` with `target_kind: 'world_bible'`.
- Annotation mutation success invalidates only the relevant Studio annotation query keys.
- Existing `PlanningView` annotation behavior remains unchanged.
- Focused tests pass:

```powershell
cd frontend; cmd /c npm.cmd run test -- StudioView
cd frontend; cmd /c npm.cmd run test -- CanonView
```

Do not proceed to Stage 5 until these pass and the final verification commands above exit 0.
