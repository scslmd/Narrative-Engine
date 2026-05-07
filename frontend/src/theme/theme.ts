export type ThemeMode = 'light' | 'dark' | 'midnight' | 'forest' | 'ocean'
export type StageTheme = 'planning' | 'writing' | 'review' | 'inspect'

export interface ThemeConfig {
  mode: ThemeMode
  stage: StageTheme
}

export const stageColors: Record<StageTheme, { primary: string; secondary: string }> = {
  planning: { primary: '#2563eb', secondary: '#3b82f6' },
  writing: { primary: '#059669', secondary: '#10b981' },
  review: { primary: '#d97706', secondary: '#f59e0b' },
  inspect: { primary: '#7c3aed', secondary: '#8b5cf6' },
}



export const themeMeta: Record<ThemeMode, { label: string; icon: string }> = {
  light: { label: 'Light', icon: '☀' },
  dark: { label: 'Dark', icon: '🌙' },
  midnight: { label: 'Midnight', icon: '🌌' },
  forest: { label: 'Forest', icon: '🌲' },
  ocean: { label: 'Ocean', icon: '🌊' },
}

const allThemes: ThemeMode[] = ['light', 'dark', 'midnight', 'forest', 'ocean']
const allStages: StageTheme[] = ['planning', 'writing', 'review', 'inspect']

export const getThemeConfig = (): ThemeConfig => {
  const stored = localStorage.getItem('narrative-engine:theme')
  if (stored) {
    try {
      const parsed = JSON.parse(stored)
      if (parsed && allThemes.includes(parsed.mode) && allStages.includes(parsed.stage)) {
        return parsed
      }
    } catch {
      // ignore parse errors
    }
  }
  return { mode: 'light', stage: 'planning' }
}

export const setThemeConfig = (config: ThemeConfig): void => {
  localStorage.setItem('narrative-engine:theme', JSON.stringify(config))
  applyTheme(config)
}

export const applyTheme = (config: ThemeConfig): void => {
  const root = document.documentElement
  root.setAttribute('data-theme', config.mode)
  root.setAttribute('data-stage', config.stage)

  // Tailwind darkMode: 'class' requires 'dark' class on <html>
  if (config.mode !== 'light') {
    root.classList.add('dark')
  } else {
    root.classList.remove('dark')
  }

  const colors = stageColors[config.stage]
  root.style.setProperty('--color-primary', colors.primary)
  root.style.setProperty('--color-secondary', colors.secondary)
}
