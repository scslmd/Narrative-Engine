# LLM Backend Detection and User Warning — Design

**Date:** 2026-04-29
**Status:** Approved

## Problem

When no LLM backend is configured (e.g., `NARRATIVE_INFERENCE_URL` not set, stub backend in use), the frontend provides no warning. Users paste a story, click Import, and receive an opaque `"Failed to parse LLM response as JSON"` error after 30+ seconds. This is a poor UX — the user should know upfront that their LLM isn't available.

## Goals

1. Detect LLM backend availability at app startup
2. Warn user via toast if no LLM is detected
3. Re-check before each import/extract operation
4. Keep import buttons enabled (user may have custom backend not reflected in health check)
5. Zero backend code changes — reuse existing `/health/ready` endpoint

## Non-Goals

- Storing raw imported story text in DB (separate feature)
- Prompting against previously imported stories (separate feature)
- Disabling UI elements when LLM is unavailable
- Polling for LLM recovery after initial failure

## Design

### Architecture

```
App mount → useHealthCheck hook → GET /health/ready → parse inference status
                                                    ↓
                                    LLM available? → No → addToast("No LLM backend...")
                                                    ↓ Yes
                                              cache status in store

Before import submit → checkBeforeImport() → re-check /health/ready
                                                        ↓
                                        LLM available? → No → addToast + proceed anyway
```

### Backend — Minimal Change

**Problem:** The existing `/health/ready` checks circuit breaker state, but the stub backend's circuit breaker stays CLOSED (it doesn't fail, it returns placeholder text). So the health check reports "all good" even when the stub is active.

**Fix:** Add `inference_backend` field to the `/health/ready` response indicating whether a real backend or stub is configured. One-line change in `app/api/health.py`:

```python
# In readiness_check(), add to return dict:
"inference": {
    "backend": settings.inference_backend,  # "stub" | "llama.cpp" | "lmstudio" | etc.
    "backends": {name: str(state.state) for name, state in circuit_states.items()},
},
```

When `settings.inference_backend == "stub"`, the frontend treats this as LLM unavailable. This is a 3-line addition to an existing endpoint, no new routes or schemas.

### Frontend — New Files

#### `frontend/src/services/health.ts`

Health check service function:
```typescript
import api from '../lib/api';

export interface HealthStatus {
  isReady: boolean;
  isLlmAvailable: boolean;
  backendType: string;  // "stub" | "llama.cpp" | "lmstudio" | etc.
  issues: HealthIssue[];
}

export interface HealthIssue {
  component: string;
  error: string;
}

export async function checkHealth(): Promise<HealthStatus> {
  try {
    const response = await api.get('/health/ready');
    const data = response.data;
    const backendType = data?.components?.inference?.backend ?? 'unknown';
    return {
      isReady: true,
      isLlmAvailable: backendType !== 'stub',
      backendType,
      issues: [],
    };
  } catch (error: unknown) {
    const err = error as { response?: { data?: { issues?: HealthIssue[]; detail?: { issues?: HealthIssue[] } } } };
    const detail = err.response?.data;
    const issues = (typeof detail === 'object' && detail !== null && 'issues' in detail)
      ? (detail as { issues: HealthIssue[] }).issues
      : ((detail as { detail?: { issues?: HealthIssue[] } })?.detail?.issues ?? []);
    const backendType = issues.find((i) => i.component === 'inference')?.error ?? 'unknown';
    return {
      isReady: false,
      isLlmAvailable: backendType !== 'stub' && backendType !== 'unknown',
      backendType,
      issues,
    };
  }
}
```

#### `frontend/src/hooks/useHealthCheck.ts`

Hook that runs on mount and exposes pre-submit check:
```typescript
import { useEffect, useState, useCallback } from 'react';
import { useToast } from './useToast';
import { checkHealth, HealthStatus } from '../services/health';

export function useHealthCheck() {
  const [status, setStatus] = useState<HealthStatus | null>(null);
  const { addToast } = useToast();

  useEffect(() => {
    checkHealth().then((result) => {
      setStatus(result);
      if (!result.isLlmAvailable) {
        addToast(
          'No LLM backend detected — imports and extractions will fail. Configure NARRATIVE_INFERENCE_URL to enable.',
          'error',
        );
      }
    });
  }, [addToast]);

  const checkBeforeImport = useCallback(async (): Promise<boolean> => {
    const result = await checkHealth();
    setStatus(result);
    if (!result.isLlmAvailable) {
      addToast('LLM backend unavailable — import will likely fail.', 'error');
    }
    return true; // Always allow proceed
  }, [addToast]);

  return { isLlmAvailable: status?.isLlmAvailable ?? null, checkBeforeImport };
}
```

### Frontend — Modified Files

#### `frontend/src/App.tsx`

Add hook at root level (existing ToastProvider scope):
```typescript
import { useHealthCheck } from './hooks/useHealthCheck';

function App() {
  useHealthCheck(); // Runs health check on mount, shows toast if needed
  return ( /* existing content */ );
}
```

#### `frontend/src/components/projects/StoryImportModal.tsx`

Add pre-submit check in `handleSubmit`:
```typescript
import { useHealthCheck } from '../../hooks/useHealthCheck';

export function StoryImportModal({ isOpen, onClose }: StoryImportModalProps) {
  const { checkBeforeImport } = useHealthCheck();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await checkBeforeImport(); // Show toast if LLM unavailable, but proceed
    // ... existing submit logic
  };
}
```

### Error Handling

- `/health/ready` call failure (network error, server down): treat as LLM unavailable, show generic toast
- `inference_backend == "stub"`: specific toast about configuring NARRATIVE_INFERENCE_URL
- Circuit breaker OPEN: specific toast about LLM backend being down
- Circuit breaker HALF_OPEN or CLOSED with real backend: LLM is available, no toast

### Testing

**Backend tests:** No new tests needed (health endpoint already tested).

**Frontend checks:**
- `npm run lint` — no errors
- `npm run typecheck` — no errors
- `npm run build` — succeeds, module count unchanged or +2

## Implementation Workflow

1. **Git branch** — create `codex/llm-detection` from `codex/main`
2. **Task 1** — add `inference.backend` field to `/health/ready` response (3-line backend change)
3. **Task 2** — create `health.ts` service and `useHealthCheck.ts` hook
4. **Task 3** — wire into `App.tsx` (mount check) and `StoryImportModal.tsx` (pre-submit)
5. **Task 4** — frontend validation: lint, typecheck, build
6. **Commit and squash-merge** to `codex/main`

## Scale

Small feature. 2 new files (~80 lines total), 2 file modifications (~10 lines each). No backend changes. Estimated implementation time: 30 minutes with subagents.
