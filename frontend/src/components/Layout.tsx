import { ReactNode, useEffect } from 'react'
import { matchPath, useLocation, useNavigate } from 'react-router-dom'
import { BookOpen, ChevronRight, Grid3x3, LayoutList, Moon, Search, Sparkles, Sun } from 'lucide-react'
import { useThemeStore } from '../stores/themeStore'
import { useUIStore } from '../stores/uiStore'
import { useProjects } from '../hooks/useProjects'
import type { WorkspaceMode } from '../routes'
import { useRouteSync } from '../hooks/useRouteSync'

interface LayoutProps {
  children: ReactNode
}

const stageMap: Record<WorkspaceMode, 'planning' | 'writing' | 'review' | 'inspect'> = {
  plan: 'planning',
  write: 'writing',
  review: 'review',
  inspect: 'inspect',
}

const modeIcons: Record<WorkspaceMode, typeof Grid3x3> = {
  plan: LayoutList,
  write: BookOpen,
  review: Search,
  inspect: Sparkles,
}

const modeLabels: Record<WorkspaceMode, string> = {
  plan: 'Planning',
  write: 'Writing',
  review: 'Review',
  inspect: 'Inspect',
}

export function Layout({ children }: LayoutProps) {
  const { mode, toggleMode, setStage } = useThemeStore()
  const { mode: uiMode, setMode, projectId } = useUIStore()
  const location = useLocation()
  const navigate = useNavigate()

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

  const isDark = mode === 'dark'
  const isWorkspace = location.pathname.startsWith('/workspace/')

  return (
    <div className={`min-h-screen flex flex-col ${isDark ? 'bg-[#0b1120]' : 'bg-[#f8fafc]'}`}>
      <div className="stage-bar" />
      <header className={`border-b ${isDark ? 'border-slate-800/80 bg-[#0f172a]/80' : 'border-slate-200/80 bg-white/80'} glass sticky top-0 z-[200]`}>
        <div className="flex items-center justify-between px-4 lg:px-6 py-2.5">
          <div className="flex items-center gap-3 min-w-0">
            <div className="flex items-center gap-2.5 flex-shrink-0">
              <div className={`w-8 h-8 rounded-lg flex items-center justify-center bg-gradient-to-br from-indigo-500 to-violet-600 shadow-sm`}>
                <span className="text-white font-bold text-sm">N</span>
              </div>
              <h1 className={`text-base font-semibold tracking-tight ${isDark ? 'text-slate-100' : 'text-slate-900'} hidden sm:block`}>
                Narrative Engine
              </h1>
            </div>

            {isWorkspace && currentProject && (
              <>
                <ChevronRight className={`w-4 h-4 flex-shrink-0 ${isDark ? 'text-slate-600' : 'text-slate-400'}`} />
                <div className="flex items-center gap-2 min-w-0">
                  <span className={`text-sm font-medium truncate ${isDark ? 'text-slate-200' : 'text-slate-700'}`}>
                    {currentProject.project_name}
                  </span>
                  <span className={`hidden md:inline text-xs px-2 py-0.5 rounded-full font-medium ${isDark ? 'bg-slate-800 text-slate-400' : 'bg-slate-100 text-slate-500'}`}>
                    {currentProject.genre}
                  </span>
                </div>
              </>
            )}
          </div>

          <div className="flex items-center gap-1.5">
            {isWorkspace && (
              <div className={`hidden sm:flex items-center rounded-lg border ${isDark ? 'bg-slate-800/50 border-slate-700/60' : 'bg-slate-50 border-slate-200'}`}>
                {(Object.keys(modeIcons) as WorkspaceMode[]).map((m) => {
                  const Icon = modeIcons[m]
                  const isActive = uiMode === m
                  return (
                    <button
                      key={m}
                      onClick={() => handleModeChange(m)}
                      className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium transition-all duration-150 ${
                        isActive
                          ? isDark
                            ? 'bg-slate-700 text-white'
                            : 'bg-white text-slate-900 shadow-sm'
                          : isDark
                            ? 'text-slate-400 hover:text-slate-200'
                            : 'text-slate-500 hover:text-slate-700'
                      }`}
                    >
                      <Icon className="w-3.5 h-3.5" />
                      <span className="hidden lg:inline">{modeLabels[m]}</span>
                    </button>
                  )
                })}
              </div>
            )}

            <button
              onClick={toggleMode}
              className={`p-2 rounded-lg transition-colors ${
                isDark
                  ? 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
                  : 'text-slate-500 hover:bg-slate-100 hover:text-slate-700'
              }`}
              aria-label="Toggle theme"
            >
              {isDark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            </button>
          </div>
        </div>

        {isWorkspace && (
          <div className={`sm:hidden flex border-t ${isDark ? 'border-slate-800' : 'border-slate-200'}`}>
            {(Object.keys(modeIcons) as WorkspaceMode[]).map((m) => {
              const Icon = modeIcons[m]
              const isActive = uiMode === m
              return (
                <button
                  key={m}
                  onClick={() => handleModeChange(m)}
                  className={`flex-1 flex items-center justify-center gap-1.5 px-2 py-2 text-xs font-medium transition-colors ${
                    isActive
                      ? isDark
                        ? 'text-white border-b-2 border-indigo-500'
                        : 'text-slate-900 border-b-2 border-indigo-500'
                      : isDark
                        ? 'text-slate-500'
                        : 'text-slate-500'
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
    </div>
  )
}
