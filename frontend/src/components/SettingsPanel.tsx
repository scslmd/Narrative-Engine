import { Settings, X } from 'lucide-react'
import { useThemeStore } from '../stores/themeStore'
import { useSettingsStore, IconMode } from '../stores/settingsStore'
import { themeMeta } from '../theme/theme'

interface SettingsPanelProps {
  onClose: () => void
}

const iconModes: { value: IconMode; label: string }[] = [
  { value: 'labels', label: 'Icons + Labels' },
  { value: 'icons-large', label: 'Icons Only (Large)' },
  { value: 'icons-small', label: 'Icons Only (Small)' },
]

export function SettingsPanel({ onClose }: SettingsPanelProps) {
  const { mode: themeMode, setMode: setThemeMode, toggleMode } = useThemeStore()
  const { iconMode, showTooltips, setIconMode, setShowTooltips } = useSettingsStore()

  return (
    <div className="fixed inset-0 z-[600] flex items-center justify-center" onClick={onClose}>
      <div className="absolute inset-0 bg-black/40" />
      <div
        className="relative w-full max-w-md mx-4 rounded-xl border bg-[var(--bg-primary)] shadow-elevated"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b px-5 py-4">
          <div className="flex items-center gap-2">
            <Settings className="w-4 h-4" />
            <h3 className="text-sm font-semibold">Settings</h3>
          </div>
          <button
            onClick={onClose}
            className="rounded-md p-1.5 text-[var(--text-tertiary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-secondary)] transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="px-5 py-4 space-y-5">
          {/* Theme Selection */}
          <div>
            <label className="block text-xs font-medium text-[var(--text-secondary)] mb-2">
              Theme
            </label>
            <div className="grid grid-cols-5 gap-2">
              {(Object.keys(themeMeta) as Array<keyof typeof themeMeta>).map((key) => {
                const theme = themeMeta[key]
                const isActive = themeMode === key
                return (
                  <button
                    key={key}
                    onClick={() => setThemeMode(key)}
                    className={`
                      relative flex flex-col items-center gap-1 rounded-lg border px-2 py-2 text-xs transition-all
                      ${isActive
                        ? 'border-[var(--color-primary)] bg-[var(--color-primary-subtle)] text-[var(--color-primary)]'
                        : 'border-[var(--border-primary)] text-[var(--text-secondary)] hover:border-[var(--border-secondary)] hover:bg-[var(--bg-secondary)]'
                      }
                    `}
                  >
                    <span className="text-base">{theme.icon}</span>
                    <span className="truncate">{theme.label}</span>
                    {isActive && (
                      <div className="absolute -top-1 -right-1 w-3 h-3 rounded-full bg-[var(--color-primary)]" />
                    )}
                  </button>
                )
              })}
            </div>
          </div>

          {/* Quick Toggle */}
          <div>
            <button
              onClick={toggleMode}
              className="w-full rounded-lg border border-[var(--border-primary)] bg-[var(--bg-secondary)] px-4 py-2.5 text-sm font-medium text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)] transition-colors"
            >
              Switch Theme
            </button>
          </div>

          {/* Icon Mode */}
          <div>
            <label className="block text-xs font-medium text-[var(--text-secondary)] mb-2">
              Navigation Icon Mode
            </label>
            <div className="space-y-1.5">
              {iconModes.map((mode) => (
                <button
                  key={mode.value}
                  onClick={() => setIconMode(mode.value)}
                  className={`
                    w-full flex items-center gap-3 rounded-lg border px-3 py-2.5 text-left text-sm transition-all
                    ${iconMode === mode.value
                      ? 'border-[var(--color-primary)] bg-[var(--color-primary-subtle)]'
                      : 'border-[var(--border-primary)] bg-transparent hover:bg-[var(--bg-secondary)]'
                    }
                  `}
                >
                  <div className={`
                    w-3.5 h-3.5 rounded-full border flex items-center justify-center flex-shrink-0
                    ${iconMode === mode.value
                      ? 'border-[var(--color-primary)]'
                      : 'border-[var(--border-secondary)]'
                    }
                  `}>
                    {iconMode === mode.value && (
                      <div className="w-1.5 h-1.5 rounded-full bg-[var(--color-primary)]" />
                    )}
                  </div>
                  <span className="text-[var(--text-primary)]">{mode.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Tooltips Toggle */}
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-[var(--text-primary)]">Show Tooltips</p>
              <p className="text-xs text-[var(--text-secondary)] mt-0.5">
                Hover over icons to see descriptions
              </p>
            </div>
            <button
              onClick={() => setShowTooltips(!showTooltips)}
              className={`
                relative w-11 h-6 rounded-full transition-colors
                ${showTooltips ? 'bg-[var(--color-primary)]' : 'bg-[var(--border-secondary)]'}
              `}
            >
              <div
                className={`
                  absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white shadow-sm transition-transform
                  ${showTooltips ? 'translate-x-5' : 'translate-x-0'}
                `}
              />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
