import { ReactNode, useEffect, useState } from 'react'
import { matchPath, useLocation, useNavigate } from 'react-router-dom'
import { BookOpen, ChevronRight, Grid3x3, LayoutList, Lightbulb, Moon, Search, Sparkles, Sun, Settings } from 'lucide-react'
import { useThemeStore } from '../stores/themeStore'
import { useUIStore } from '../stores/uiStore'
import { useProjects } from '../hooks/useProjects'
import { useSettingsStore } from '../stores/settingsStore'
import type { WorkspaceMode } from '../routes'
import { useRouteSync } from '../hooks/useRouteSync'
import { SettingsPanel } from './SettingsPanel'

interface LayoutProps {
  children: ReactNode
}

const stageMap: Record<WorkspaceMode, 'planning' | 'writing' | 'review' | 'inspect'> = {
  plan: 'planning',
  braindump: 'planning',
  generate: 'planning',
  write: 'writing',
  review: 'review',
  inspect: 'inspect',
}

const modeIcons: Record<WorkspaceMode, typeof Grid3x3> = {
  plan: LayoutList,
  braindump: Lightbulb,
  generate: Sparkles,
  write: BookOpen,
  review: Search,
  inspect: Sparkles,
}

const modeLabels: Record<WorkspaceMode, string> = {
  plan: 'Planning',
  braindump: 'Brain Dump',
  generate: 'Generate',
  write: 'Writing',
  review: 'Review',
  inspect: 'Inspect',
}

export function Layout({ children }: LayoutProps) {
  const { mode, toggleMode, setStage } = useThemeStore()
  const { mode: uiMode, setMode, projectId } = useUIStore()
  const { iconMode } = useSettingsStore()
  const location = useLocation()
  const navigate = useNavigate()
  const [showSettings, setShowSettings] = useState(false)

  useRouteSync()

  const { data: projects } = useProjects()
  const currentProject = projects?.find((p) => p.project_id === projectId)

  useEffect(() => {
    setStage(stageMap[uiMode])
  }, [setStage, uiMode])

  const handleModeChange = (nextMode: WorkspaceMode) => {
    setMode(nextMode)

    const workspaceMatch = matchPath('/workspace/:projectId/*', location.pathname)
    const matchedProjectId = workspaceMatch?.params.projectId

    if (!matchedProjectId) {
      return
    }

    navigate(`/workspace/${matchedProjectId}/${nextMode}`)
  }

  const isDark = ['dark', 'midnight', 'forest', 'ocean'].includes(mode)
  const isWorkspace = location.pathname.startsWith('/workspace/')
  const iconsOnly = iconMode !== 'labels'
  const showIcons = iconsOnly || window.innerWidth < 640

  return (
    <div className="min-h-screen flex flex-col bg-[var(--bg-base)]" data-icon-mode={iconsOnly ? iconMode : ''}>
      <div className="stage-bar" />
      <header className="border-b border-[var(--border-primary)] bg-[var(--bg-primary)]/80 glass sticky top-0 z-[200]">
        <div className="flex items-center justify-between px-4 lg:px-6 py-2.5">
          <div className="flex items-center gap-3 min-w-0">
            <div className="flex items-center gap-2.5 flex-shrink-0">
              <div className="w-8 h-8 rounded-lg flex items-center justify-center bg-gradient-to-br from-indigo-500 to-violet-600 shadow-sm">
                <span className="text-white font-bold text-sm">N</span>
              </div>
              <h1 className="text-base font-semibold tracking-tight text-[var(--text-primary)] hidden sm:block">
                Narrative Engine
              </h1>
            </div>

            {isWorkspace && currentProject && (
              <>
                <ChevronRight className="w-4 h-4 flex-shrink-0 text-[var(--text-tertiary)]" />
                <div className="flex items-center gap-2 min-w-0">
                  <span className="text-sm font-medium truncate text-[var(--text-primary)]">
                    {currentProject.project_name}
                  </span>
                  <span className="hidden md:inline text-xs px-2 py-0.5 rounded-full font-medium text-[var(--text-secondary)] bg-[var(--bg-secondary)]">
                    {currentProject.genre}
                  </span>
                </div>
              </>
            )}
          </div>

          <div className="flex items-center gap-1.5">
            {isWorkspace && (
              <div className="hidden sm:flex items-center rounded-lg border border-[var(--border-primary)] bg-[var(--bg-secondary)]/50">
                {(Object.keys(modeIcons) as WorkspaceMode[]).map((m) => {
                  const Icon = modeIcons[m]
                  const isActive = uiMode === m
                  return (
                    <button
                      key={m}
                      onClick={() => handleModeChange(m)}
                      className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium transition-all duration-150 ${
                        isActive
                          ? 'text-[var(--text-primary)] bg-[var(--bg-elevated)] shadow-sm'
                          : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
                      }`}
                    >
                      <Icon className="w-3.5 h-3.5" />
                      {showIcons && <span className="hidden lg:inline">{modeLabels[m]}</span>}
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
          <div className="sm:hidden flex border-t border-[var(--border-primary)]">
            {(Object.keys(modeIcons) as WorkspaceMode[]).map((m) => {
              const Icon = modeIcons[m]
              const isActive = uiMode === m
              return (
                <button
                  key={m}
                  onClick={() => handleModeChange(m)}
                  className={`flex-1 flex items-center justify-center gap-1.5 px-2 py-2 text-xs font-medium transition-colors ${
                    isActive
                      ? 'text-[var(--text-primary)] border-b-2 border-[var(--color-primary)]'
                      : 'text-[var(--text-secondary)]'
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  <span>{modeLabels[m]}</span>
                </button>
              )
            })}
          </div>
        )}
      </header>
      <main className="flex-1 p-4 lg:p-6">
        {children}
      </main>

      {showSettings && (
        <SettingsPanel onClose={() => setShowSettings(false)} />
      )}
    </div>
  )
}
