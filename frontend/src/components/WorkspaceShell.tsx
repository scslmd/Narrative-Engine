import { ReactNode } from 'react'
import { useUIStore } from '../stores/uiStore'
import { useSettingsStore } from '../stores/settingsStore'
import { LayoutList, BookOpen, Search, Sparkles } from 'lucide-react'

interface WorkspaceShellProps {
  children: ReactNode
}

interface NavItem {
  key: string
  label: string
  icon: typeof LayoutList
  gradient: string
  glow: string
}

const navItems: NavItem[] = [
  { key: 'plan', label: 'Planning', icon: LayoutList, gradient: 'from-blue-500 to-blue-600', glow: 'glow-planning' },
  { key: 'write', label: 'Writing', icon: BookOpen, gradient: 'from-emerald-500 to-emerald-600', glow: 'glow-writing' },
  { key: 'review', label: 'Review', icon: Search, gradient: 'from-amber-500 to-amber-600', glow: 'glow-review' },
  { key: 'inspect', label: 'Inspect', icon: Sparkles, gradient: 'from-violet-500 to-violet-600', glow: 'glow-inspect' },
]

export function WorkspaceShell({ children }: WorkspaceShellProps) {
  const { mode, setMode } = useUIStore()
  const { iconMode, showTooltips } = useSettingsStore()
  const iconsOnly = iconMode !== 'labels'
  const showTooltipsEnabled = showTooltips && iconsOnly

  return (
    <div className="flex gap-5">
      <aside className="w-52 flex-shrink-0">
        <nav className="space-y-0.5 py-1">
          {navItems.map((item) => {
            const isActive = mode === item.key
            const Icon = item.icon
            const tooltipText = showTooltipsEnabled ? item.label : undefined
            return (
              <button
                key={item.key}
                onClick={() => setMode(item.key as typeof mode)}
                data-tooltip={tooltipText}
                className={`w-full nav-item flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 group ${
                  isActive
                    ? 'bg-[var(--color-primary-subtle)] text-[var(--color-primary)] shadow-card'
                    : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-secondary)]'
                }`}
              >
                <div className={`nav-icon-wrapper w-8 h-8 rounded-lg flex items-center justify-center transition-all duration-150 ${
                  isActive
                    ? `bg-gradient-to-br ${item.gradient} text-white shadow-sm`
                    : 'bg-[var(--bg-secondary)] text-[var(--text-tertiary)] group-hover:bg-[var(--bg-tertiary)] group-hover:text-[var(--text-secondary)]'
                }`}>
                  <Icon className="w-4 h-4" />
                </div>
                <span className="flex-1 text-left nav-label">{item.label}</span>
                {isActive && (
                  <div className={`w-1.5 h-1.5 rounded-full bg-gradient-to-br ${item.gradient} nav-label`} />
                )}
              </button>
            )
          })}
        </nav>
      </aside>
      <main className="flex-1 min-w-0">{children}</main>
    </div>
  )
}
