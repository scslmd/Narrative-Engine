import { create } from 'zustand'
import { ThemeMode, StageTheme, setThemeConfig as applyThemeConfig } from '../theme/theme'

interface ThemeStore {
  mode: ThemeMode
  stage: StageTheme
  setMode: (mode: ThemeMode) => void
  setStage: (stage: StageTheme) => void
  toggleMode: () => void
}

export const useThemeStore = create<ThemeStore>((set) => ({
  mode: 'light',
  stage: 'planning',
  setMode: (mode) => {
    set({ mode })
    applyThemeConfig({ mode, stage: useThemeStore.getState().stage })
  },
  setStage: (stage) => {
    set({ stage })
    applyThemeConfig({ mode: useThemeStore.getState().mode, stage })
  },
  toggleMode: () => {
    set((state) => {
      const newMode = state.mode === 'light' ? 'dark' : 'light'
      applyThemeConfig({ mode: newMode, stage: state.stage })
      return { mode: newMode }
    })
  },
}))