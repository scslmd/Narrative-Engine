export type ThemeMode = 'light' | 'dark'
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

export const getThemeConfig = (): ThemeConfig => {
  const stored = localStorage.getItem('narrative-engine:theme')
  if (stored) {
    try {
      return JSON.parse(stored)
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
  
  const colors = stageColors[config.stage]
  root.style.setProperty('--color-primary', colors.primary)
  root.style.setProperty('--color-secondary', colors.secondary)
}