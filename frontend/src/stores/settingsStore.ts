import { create } from 'zustand'

export type IconMode = 'labels' | 'icons-large' | 'icons-small'

export type OutlineDetail = 'headings' | 'detailed'

export interface UserSettings {
  iconMode: IconMode
  showTooltips: boolean
  outlineDetail: OutlineDetail
}

const STORAGE_KEY = 'narrative-engine:settings'

const defaultSettings: UserSettings = {
  iconMode: 'labels',
  showTooltips: true,
  outlineDetail: 'headings',
}

function loadSettings(): UserSettings {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      const parsed = JSON.parse(stored)
      if (parsed && typeof parsed.iconMode === 'string' && typeof parsed.showTooltips === 'boolean') {
        return { ...defaultSettings, ...parsed }
      }
    }
  } catch {
    // ignore
  }
  return defaultSettings
}

function saveSettings(settings: UserSettings): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(settings))
}

interface SettingsState extends UserSettings {
  setIconMode: (mode: IconMode) => void
  setShowTooltips: (show: boolean) => void
  setOutlineDetail: (detail: OutlineDetail) => void
  reset: () => void
}

export const useSettingsStore = create<SettingsState>((set, get) => ({
  ...loadSettings(),
  setIconMode: (iconMode) => {
    const newSettings = { ...get(), iconMode }
    set(newSettings)
    saveSettings(newSettings)
  },
  setShowTooltips: (showTooltips) => {
    const newSettings = { ...get(), showTooltips }
    set(newSettings)
    saveSettings(newSettings)
  },
  setOutlineDetail: (outlineDetail) => {
    const newSettings = { ...get(), outlineDetail }
    set(newSettings)
    saveSettings(newSettings)
  },
  reset: () => {
    set(defaultSettings)
    saveSettings(defaultSettings)
  },
}))
