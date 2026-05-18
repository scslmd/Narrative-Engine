import { ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'
import { useUIStore } from '../stores/uiStore'
import { useSettingsStore } from '../stores/settingsStore'
import { modeToStage } from '../routes'
import { LayoutList, Search, Sparkles, Lightbulb, Scroll, Zap, MonitorUp } from 'lucide-react'

interface WorkspaceShellProps {
  children: ReactNode
}

interface NavItem {
  key: string
  label: string
  icon: typeof LayoutList
  gradient: string
  glow: string
  stage: 'planning' | 'writing' | 'review'
}

const navItems: NavItem[] = [
  { key: 'braindump', label: 'Brain Dump', icon: Lightbulb, gradient: 'from-amber-500 to-amber-600', glow: 'glow-braindump', stage: 'planning' },
  { key: 'plan', label: 'Planning', icon: LayoutList, gradient: 'from-blue-500 to-blue-600', glow: 'glow-planning', stage: 'planning' },
  { key: 'canon', label: 'Canon', icon: Scroll, gradient: 'from-indigo-500 to-indigo-600', glow: 'glow-canon', stage: 'planning' },
  { key: 'generate', label: 'Generate', icon: Zap, gradient: 'from-purple-500 to-purple-600', glow: 'glow-generate', stage: 'planning' },
  { key: 'studio', label: 'Studio', icon: MonitorUp, gradient: 'from-emerald-500 to-emerald-600', glow: 'glow-writing', stage: 'writing' },
  { key: 'review', label: 'Review', icon: Search, gradient: 'from-amber-500 to-amber-600', glow: 'glow-review', stage: 'review' },
  { key: 'inspect', label: 'Inspect', icon: Sparkles, gradient: 'from-violet-500 to-violet-600', glow: 'glow-inspect', stage: 'review' },
]

export function WorkspaceShell({ children }: WorkspaceShellProps) {
  const { mode, setMode, projectId } = useUIStore()
  const navigate = useNavigate()
  const { iconMode, showTooltips } = useSettingsStore()
  const iconsOnly = iconMode !== 'labels'
  const showTooltipsEnabled = showTooltips && iconsOnly
  const activeStage = modeToStage[mode]
  const visibleItems = navItems.filter((item) => item.stage === activeStage)
  const isStudio = mode === 'studio'

  const handleNavClick = (key: string) => {
    setMode(key as typeof mode)
    if (projectId) {
      navigate(`/workspace/${projectId}/${key}`)
    }
  }

  return (
    <div className="flex flex-col lg:flex-row gap-4 lg:gap-5 h-full">
      {!isStudio ? (
      <aside className="lg:w-60 lg:flex-shrink-0">
        <div className="rounded-xl border border-[var(--border-primary)] bg-[var(--bg-primary)] shadow-card p-3 lg:sticky lg:top-0">
          <p className="text-[11px] uppercase tracking-wide font-semibold text-[var(--text-tertiary)] px-1 pb-2">
            Workspace sections
          </p>
          <nav aria-label="Workspace sections" className="space-y-1">
          {visibleItems.map((item) => {
            const isActive = mode === item.key
            const Icon = item.icon
            const tooltipText = showTooltipsEnabled ? item.label : undefined
            return (
              <button
                key={item.key}
                onClick={() => handleNavClick(item.key)}
                data-tooltip={tooltipText}
                aria-current={isActive ? 'page' : undefined}
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
        </div>
      </aside>) : null}
      <main className="flex-1 min-w-0">{children}</main>
    </div>
  )
}
