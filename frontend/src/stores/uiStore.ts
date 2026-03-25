import { create } from 'zustand'
import { WorkspaceMode } from '../routes'
import type { InspectContext } from '../types/inspect'

interface UIState {
  mode: WorkspaceMode
  projectId: string | null
  chapterId: string | null
  jobId: string | null
  inspectContext: InspectContext | null
  setMode: (mode: WorkspaceMode) => void
  setProjectId: (projectId: string | null) => void
  setChapterId: (chapterId: string | null) => void
  setJobId: (jobId: string | null) => void
  setInspectContext: (context: InspectContext | null) => void
  reset: () => void
}

export const useUIStore = create<UIState>((set) => ({
  mode: 'plan',
  projectId: null,
  chapterId: null,
  jobId: null,
  inspectContext: null,
  setMode: (mode) => set({ mode }),
  setProjectId: (projectId) => set({ projectId }),
  setChapterId: (chapterId) => set({ chapterId }),
  setJobId: (jobId) => set({ jobId }),
  setInspectContext: (context) => set({ inspectContext: context }),
  reset: () => set({ mode: 'plan', projectId: null, chapterId: null, jobId: null, inspectContext: null }),
}))