import { create } from 'zustand';

interface JobMonitorState {
  activeJobId: string | null;
  isVisible: boolean;
  
  setActiveJobId: (jobId: string | null) => void;
  toggleVisibility: () => void;
  hide: () => void;
}

export const useJobStore = create<JobMonitorState>((set) => ({
  activeJobId: null,
  isVisible: false,
  
  setActiveJobId: (jobId) => set({ activeJobId: jobId, isVisible: !!jobId }),
  toggleVisibility: () => set((state) => ({ isVisible: !state.isVisible })),
  hide: () => set({ activeJobId: null, isVisible: false }),
}));
