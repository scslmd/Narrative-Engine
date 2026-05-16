import { create } from 'zustand';

export type StudioPanelKey =
  | 'suggestions'
  | 'ideas'
  | 'characters'
  | 'worldBible'
  | 'relationships'
  | 'generation'
  | 'review'
  | 'inspect'
  | 'notes'
  | 'jobs';

interface StudioState {
  activePanel: StudioPanelKey;
  leftRailOpen: boolean;
  contextPanelOpen: boolean;
  setActivePanel: (panel: StudioPanelKey) => void;
  setLeftRailOpen: (open: boolean) => void;
  setContextPanelOpen: (open: boolean) => void;
  openPanel: (panel: StudioPanelKey) => void;
  toggleLeftRail: () => void;
  toggleContextPanel: () => void;
  closeDrawers: () => void;
}

export const useStudioStore = create<StudioState>((set) => ({
  activePanel: 'suggestions',
  leftRailOpen: true,
  contextPanelOpen: true,
  setActivePanel: (activePanel) => set({ activePanel }),
  setLeftRailOpen: (leftRailOpen) => set({ leftRailOpen }),
  setContextPanelOpen: (contextPanelOpen) => set({ contextPanelOpen }),
  openPanel: (activePanel) => set({ activePanel, contextPanelOpen: true }),
  toggleLeftRail: () => set((state) => ({ leftRailOpen: !state.leftRailOpen })),
  toggleContextPanel: () => set((state) => ({ contextPanelOpen: !state.contextPanelOpen })),
  closeDrawers: () => set({ leftRailOpen: false, contextPanelOpen: false }),
}));
