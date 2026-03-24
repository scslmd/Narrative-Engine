import { create } from 'zustand'
import { WorkspaceMode } from '../routes'

interface UIState {
  mode: WorkspaceMode
  projectId: string | null
  chapterId: string | null
  jobId: string | null
  setMode: (mode: WorkspaceMode) => void
  setProjectId: (projectId: string | null) => void
  setChapterId: (chapterId: string | null) => void
  setJobId: (jobId: string | null) => void
  reset: () => void
}

export const useUIStore = create<UIState>((set) => ({
  mode: 'plan',
  projectId: null,
  chapterId: null,
  jobId: null,
  setMode: (mode) => set({ mode }),
  setProjectId: (projectId) => set({ projectId }),
  setChapterId: (chapterId) => set({ chapterId }),
  setJobId: (jobId) => set({ jobId }),
  reset: () => set({ mode: 'plan', projectId: null, chapterId: null, jobId: null }),
}))