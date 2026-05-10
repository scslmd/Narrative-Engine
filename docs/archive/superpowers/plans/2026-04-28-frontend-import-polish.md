# Frontend Import UX Polish — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development

**Goal:** Add toast notification system, import error retry button, and file size indicator to StoryImportModal.

**Architecture:** New Toast component + useToast hook in `components/ui/`. Modal wraps with toast provider. Retry re-submits without user re-entry. Size indicator shows char/word count and estimated processing time.

**Tech Stack:** React, TypeScript, Tailwind CSS

---

## Task 1: Toast Component and Hook

**Files:**
- Create: `frontend/src/components/ui/Toast.tsx`
- Create: `frontend/src/hooks/useToast.ts`

### Step 1: Write the toast hook

Create `frontend/src/hooks/useToast.ts`:

```typescript
import { createContext, useContext, useState, useCallback, ReactNode } from 'react';

export type ToastVariant = 'success' | 'error' | 'info';

export interface ToastItem {
  id: string;
  message: string;
  variant: ToastVariant;
}

interface ToastContextType {
  toasts: ToastItem[];
  addToast: (message: string, variant?: ToastVariant) => void;
  removeToast: (id: string) => void;
}

const ToastContext = createContext<ToastContextType | null>(null);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const addToast = useCallback((message: string, variant: ToastVariant = 'info') => {
    const id = Math.random().toString(36).slice(2);
    setToasts((prev) => [...prev.slice(-2), { id, message, variant }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 5000);
  }, []);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ toasts, addToast, removeToast }}>
      {children}
    </ToastContext.Provider>
  );
}

export function useToast(): ToastContextType {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error('useToast must be used within ToastProvider');
  return ctx;
}
```

### Step 2: Write the Toast component

Create `frontend/src/components/ui/Toast.tsx`:

```typescript
import { useEffect, useState } from 'react';
import { X, CheckCircle, AlertCircle, Info } from 'lucide-react';
import { useToast, ToastVariant } from '../../hooks/useToast';

const VARIANT_STYLES: Record<ToastVariant, string> = {
  success: 'bg-green-50 border-green-200 text-green-800',
  error: 'bg-red-50 border-red-200 text-red-800',
  info: 'bg-blue-50 border-blue-200 text-blue-800',
};

const VARIANT_ICON: Record<ToastVariant, React.ReactNode> = {
  success: <CheckCircle className="w-5 h-5 text-green-500" />,
  error: <AlertCircle className="w-5 h-5 text-red-500" />,
  info: <Info className="w-5 h-5 text-blue-500" />,
};

export function ToastContainer(): React.ReactElement {
  const { toasts, removeToast } = useToast();

  return (
    <div className="fixed top-4 right-4 z-50 flex flex-col gap-2">
      {toasts.map((toast) => (
        <Toast key={toast.id} toast={toast} onDismiss={removeToast} />
      ))}
    </div>
  );
}

interface ToastProps {
  toast: { id: string; message: string; variant: ToastVariant };
  onDismiss: (id: string) => void;
}

function Toast({ toast, onDismiss }: ToastProps): React.ReactElement {
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setVisible(false);
      setTimeout(() => onDismiss(toast.id), 300);
    }, 5000);
    return () => clearTimeout(timer);
  }, [toast.id, onDismiss]);

  return (
    <div
      className={`flex items-center gap-3 px-4 py-3 border rounded-lg shadow-lg transition-opacity duration-300 ${
        visible ? 'opacity-100' : 'opacity-0'
      } ${VARIANT_STYLES[toast.variant]}`}
    >
      {VARIANT_ICON[toast.variant]}
      <span className="text-sm flex-1">{toast.message}</span>
      <button
        onClick={() => onDismiss(toast.id)}
        className="opacity-60 hover:opacity-100 transition-opacity"
        aria-label="Dismiss"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  );
}
```

### Step 3: Run frontend checks

Run: `cd frontend && npm run lint && npm run typecheck`
Expected: PASS

### Step 4: Commit

```bash
git add frontend/src/components/ui/Toast.tsx frontend/src/hooks/useToast.ts
git commit -m "feat: add toast notification system with provider and hook"
```

---

## Task 2: Wire Toast into App

**Files:**
- Modify: `frontend/src/App.tsx` (or main layout)

### Step 1: Read current App.tsx

Find where the app is structured. Wrap with ToastProvider and add ToastContainer.

### Step 2: Add toast provider to app root

Add to top-level render:
```tsx
import { ToastProvider, ToastContainer } from './components/ui/Toast';

function App() {
  return (
    <ToastProvider>
      {/* existing content */}
      <ToastContainer />
    </ToastProvider>
  );
}
```

### Step 3: Run checks and commit

Run: `cd frontend && npm run lint && npm run typecheck && npm run build`
Expected: PASS

Commit: `git add frontend/src/App.tsx && git commit -m "feat: wire toast provider into app root"`

---

## Task 3: Retry Button and File Size Indicator in Modal

**Files:**
- Modify: `frontend/src/components/projects/StoryImportModal.tsx`

### Step 1: Add retry state and file size indicator

Add to modal state:
```tsx
const [importError, setImportError] = useState<string | null>(null);
const { addToast } = useToast();
```

Compute text stats from storyText:
```tsx
const charCount = storyText.length;
const wordCount = storyText.trim() ? storyText.trim().split(/\s+/).length : 0;
const estimatedTime = charCount > 30000
  ? `${Math.ceil(charCount / 10000 * 2)}-${Math.ceil(charCount / 10000 * 4)} min`
  : charCount > 5000
    ? '1-3 min'
    : '< 1 min';
```

Add size indicator below textarea:
```tsx
{importMode === 'story' && storyText && (
  <div className="mt-2 flex items-center gap-4 text-xs text-gray-500">
    <span>{charCount.toLocaleString()} characters</span>
    <span>{wordCount.toLocaleString()} words</span>
    <span>~{estimatedTime} to process</span>
    {charCount > 100000 && (
      <span className="text-amber-600">Large file — may take longer</span>
    )}
  </div>
)}
```

### Step 2: Add retry button on error

When import fails (error state is set), show retry button:
```tsx
{importError && !isImporting && (
  <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
    <p className="text-sm text-red-700">{importError}</p>
    <button
      type="button"
      onClick={() => {
        setImportError(null);
        setError(null);
        handleSubmit(event); // re-trigger submit
      }}
      className="mt-2 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors text-sm"
    >
      Retry Import
    </button>
  </div>
)}
```

### Step 3: Wire toasts into success/error paths

In the polling handler, replace error/setError calls with addToast:
```tsx
if (progress.status === 'completed' && progress.result) {
  const msg = `Imported ${progress.result.project_name}`;
  const detail = progress.result.chapters_processed
    ? ` (${progress.result.chapters_processed} chapters)`
    : '';
  addToast(`${msg}${detail}`, 'success');
  // ... navigation
} else if (progress.status === 'failed') {
  setImportError(progress.error || 'Import failed');
  addToast(progress.error || 'Import failed', 'error');
  // ...
}
```

### Step 4: Run checks and commit

Run: `cd frontend && npm run lint && npm run typecheck && npm run build`
Expected: PASS

Commit: `git add frontend/src/components/projects/StoryImportModal.tsx && git commit -m "feat: add retry button, file size indicator, and toast notifications to import modal"`

---

## Task 4: Full Validation

### Step 1: Run frontend checks

Run: `cd frontend && npm run lint && npm run typecheck && npm run build`
Expected: All pass

### Step 2: Commit

```bash
git status && git log --oneline -3
```
