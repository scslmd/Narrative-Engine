import { create } from 'zustand'
import { ThemeMode, StageTheme, setThemeConfig as applyThemeConfig, getThemeConfig, resolveEffectiveMode, watchSystemTheme } from '../theme/theme'

interface ThemeStore {
  mode: ThemeMode
  stage: StageTheme
  _systemTick: number
  setMode: (mode: ThemeMode) => void
  setStage: (stage: StageTheme) => void
  toggleMode: () => void
}

const themeOrder: ThemeMode[] = ['light', 'dark', 'midnight', 'forest', 'ocean', 'system']

// Track cleanup function for system theme listener
let _unwatchSystem: (() => void) | null = null

export const useThemeStore = create<ThemeStore>((set, get) => {
  const stored = getThemeConfig()
  return {
    mode: stored.mode,
    stage: stored.stage,
    _systemTick: 0,
    setMode: (mode) => {
      // Clean up system listener if switching away from system
      if (get().mode === 'system' && mode !== 'system' && _unwatchSystem) {
        _unwatchSystem()
        _unwatchSystem = null
      }

      set({ mode })
      applyThemeConfig({ mode, stage: get().stage })

      // Set up system listener if switching to system
      if (mode === 'system') {
        _unwatchSystem = watchSystemTheme(() => {
          const root = document.documentElement
          const effectiveDark = resolveEffectiveMode('system') === 'dark'
          if (effectiveDark) {
            root.classList.add('dark')
          } else {
            root.classList.remove('dark')
          }
          // Tick to force React re-renders
          set((state) => ({ _systemTick: state._systemTick + 1 }))
        })
      }
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

        // Clean up system listener if switching away from system
        if (state.mode === 'system' && _unwatchSystem) {
          _unwatchSystem()
          _unwatchSystem = null
        }

        applyThemeConfig({ mode: newMode, stage: state.stage })

        // Set up system listener if switching to system
        if (newMode === 'system') {
          _unwatchSystem = watchSystemTheme(() => {
            const root = document.documentElement
            const effectiveDark = resolveEffectiveMode('system') === 'dark'
            if (effectiveDark) {
              root.classList.add('dark')
            } else {
              root.classList.remove('dark')
            }
            set((s) => ({ _systemTick: s._systemTick + 1 }))
          })
        }

        return { mode: newMode }
      })
    },
  }
})
