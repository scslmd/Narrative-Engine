import { create } from 'zustand'
import { ThemeMode, StageTheme, setThemeConfig as applyThemeConfig, getThemeConfig } from '../theme/theme'

interface ThemeStore {
  mode: ThemeMode
  stage: StageTheme
  setMode: (mode: ThemeMode) => void
  setStage: (stage: StageTheme) => void
  toggleMode: () => void
}

const themeOrder: ThemeMode[] = ['light', 'dark', 'midnight', 'forest', 'ocean']

export const useThemeStore = create<ThemeStore>((set, get) => {
  const stored = getThemeConfig()
  return {
    mode: stored.mode,
    stage: stored.stage,
    setMode: (mode) => {
      set({ mode })
      applyThemeConfig({ mode, stage: get().stage })
    },
    setStage: (stage) => {
      set({ stage })
      applyThemeConfig({ mode: get().mode, stage })
    },
    toggleMode: () => {
      set((state) => {
        const currentIndex = themeOrder.indexOf(state.mode)
        const nextIndex = (currentIndex + 1) % themeOrder.length
        const newMode = themeOrder[nextIndex]
        applyThemeConfig({ mode: newMode, stage: state.stage })
        return { mode: newMode }
      })
    },
  }
})
