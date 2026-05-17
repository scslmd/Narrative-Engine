import { ReactNode, useEffect, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { BookOpen, ChevronRight, Lightbulb, Moon, Search, Sun, Settings } from 'lucide-react'
import { useThemeStore } from '../stores/themeStore'
import { resolveEffectiveMode } from '../theme/theme'
import { useUIStore } from '../stores/uiStore'
import { useProjects } from '../hooks/useProjects'
import { useSettingsStore } from '../stores/settingsStore'
import { modeToStage, type WorkspaceMode } from '../routes'
import { useRouteSync } from '../hooks/useRouteSync'
import { SettingsPanel } from './SettingsPanel'

interface LayoutProps {
  children: ReactNode
}

type StageId = 'planning' | 'writing' | 'review'

const STAGE_DEFAULT_MODE: Record<StageId, string> = {
  planning: 'plan',
  writing: 'write',
  review: 'review',
}

const stageButtons: { id: StageId; label: string; icon: typeof Lightbulb; shadow: string; border: string }[] = [
  { id: 'planning', label: 'Planning', icon: Lightbulb, shadow: 'shadow-amber-500/30', border: 'border-amber-500' },
  { id: 'writing', label: 'Writing', icon: BookOpen, shadow: 'shadow-blue-500/30', border: 'border-blue-500' },
  { id: 'review', label: 'Review', icon: Search, shadow: 'shadow-emerald-500/30', border: 'border-emerald-500' },
]

export function Layout({ children }: LayoutProps) {
  const { mode, stage, _systemTick, toggleMode, setStage } = useThemeStore()
  void _systemTick;
  const { mode: uiMode, setMode, projectId } = useUIStore()
  const { iconMode } = useSettingsStore()
  const location = useLocation()
  const navigate = useNavigate()
  const [showSettings, setShowSettings] = useState(false)

  useRouteSync()

  const { data: projects } = useProjects()
  const currentProject = projects?.find((p) => p.project_id === projectId)

  useEffect(() => {
    const nextStage = modeToStage[uiMode]
    if (stage !== nextStage) {
      setStage(nextStage)
    }
  }, [setStage, stage, uiMode])

 const handleStageChange = (stageId: StageId) => {
    const nextMode = STAGE_DEFAULT_MODE[stageId] as WorkspaceMode
    setMode(nextMode)
    if (!projectId) return
    navigate(`/workspace/${projectId}/${nextMode}`)
  }

  const activeStage = modeToStage[uiMode]
  const isDark = resolveEffectiveMode(mode) === 'dark'
  const isWorkspace = location.pathname.startsWith('/workspace/')
  const iconsOnly = iconMode !== 'labels'

  return (
    <div className="h-screen flex flex-col overflow-hidden bg-[var(--bg-base)]" data-icon-mode={iconsOnly ? iconMode : ''}>
      <div className="stage-bar" />
      <header className="border-b border-[var(--border-primary)] bg-[var(--bg-primary)]/90 backdrop-blur supports-[backdrop-filter]:bg-[var(--bg-primary)]/80 sticky top-0 z-[200]">
        <div className="flex items-center justify-between px-4 lg:px-6 py-3">
          <div className="flex items-center gap-3 min-w-0">
            <div className="flex items-center gap-2.5 flex-shrink-0">
              <button
                onClick={() => navigate('/')}
                className="flex items-center gap-2.5 flex-shrink-0 hover:opacity-80 transition-opacity cursor-pointer"
              >
                <div className="w-8 h-8 rounded-lg flex items-center justify-center bg-gradient-to-br from-indigo-500 to-violet-600 shadow-sm">
                  <span className="text-white font-bold text-sm">N</span>
                </div>
                <h1 className="text-base font-semibold tracking-tight text-[var(--text-primary)] hidden sm:block">
                  Narrative Engine
                </h1>
              </button>
            </div>

            {isWorkspace && currentProject && (
              <>
                <ChevronRight className="w-4 h-4 flex-shrink-0 text-[var(--text-tertiary)]" />
                <div className="min-w-0">
                  <p className="text-[11px] uppercase tracking-wide text-[var(--text-tertiary)]">Current Project</p>
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="text-sm font-semibold truncate text-[var(--text-primary)]">
                      {currentProject.project_name}
                    </span>
                    <span className="hidden md:inline text-xs px-2 py-0.5 rounded-full font-medium text-[var(--text-secondary)] bg-[var(--bg-secondary)]">
                      {currentProject.genre}
                    </span>
                  </div>
                </div>
              </>
            )}
          </div>

          <div className="flex items-center gap-1.5">
            {isWorkspace && (
              <div
                role="group"
                aria-label="Workflow stages"
                className="hidden sm:flex items-center gap-1 rounded-lg border border-[var(--border-primary)] bg-[var(--bg-secondary)]/50 p-0.5"
              >
                {stageButtons.map(({ id, label, icon: Icon, shadow }) => {
                  const isActive = activeStage === id
                  return (
                    <button
                      key={id}
                      onClick={() => handleStageChange(id)}
                      aria-current={isActive ? 'page' : undefined}
                      className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium transition-all duration-200 rounded-md ${
                        isActive
                          ? `bg-[var(--bg-elevated)] text-[var(--text-primary)] shadow-lg ${shadow}`
                          : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)]/50'
                      }`}
                    >
                      <Icon className="w-3.5 h-3.5" />
                      <span className="hidden md:inline">{label}</span>
                    </button>
                  )
                })}
              </div>
            )}

            <button
              onClick={toggleMode}
              className="p-2 rounded-lg transition-colors text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)] hover:text-[var(--text-primary)]"
              aria-label="Toggle theme"
            >
              {isDark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            </button>

            <button
              onClick={() => setShowSettings(true)}
              className="p-2 rounded-lg transition-colors text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)] hover:text-[var(--text-primary)]"
              aria-label="Settings"
            >
              <Settings className="w-4 h-4" />
            </button>
          </div>
        </div>

        {isWorkspace && (
          <div role="group" aria-label="Workflow stages" className="sm:hidden flex border-t border-[var(--border-primary)]">
            {stageButtons.map(({ id, label, icon: Icon, border }) => {
              const isActive = activeStage === id
              return (
                <button
                  key={id}
                  onClick={() => handleStageChange(id)}
                  aria-current={isActive ? 'page' : undefined}
                  className={`flex-1 flex items-center justify-center gap-1.5 px-2 py-2 text-xs font-medium transition-colors ${
                    isActive
                      ? `text-[var(--text-primary)] border-b-2 ${border}`
                      : 'text-[var(--text-secondary)]'
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  <span>{label}</span>
                </button>
              )
            })}
          </div>
        )}
      </header>
      <main className="flex-1 overflow-auto px-4 py-4 lg:px-6 lg:py-5">
        {children}
      </main>

      {showSettings && (
        <SettingsPanel onClose={() => setShowSettings(false)} />
      )}
    </div>
  )
}
