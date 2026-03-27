import { ReactNode, useEffect } from 'react'
import { matchPath, useLocation, useNavigate } from 'react-router-dom'
import { useThemeStore } from '../stores/themeStore'
import { useUIStore } from '../stores/uiStore'
import type { WorkspaceMode } from '../routes'

interface LayoutProps {
  children: ReactNode
}

const stageMap: Record<WorkspaceMode, 'planning' | 'writing' | 'review' | 'inspect'> = {
  plan: 'planning',
  write: 'writing',
  review: 'review',
  inspect: 'inspect',
}

export function Layout({ children }: LayoutProps) {
  const { mode, toggleMode, setStage } = useThemeStore()
  const { mode: uiMode, setMode } = useUIStore()
  const location = useLocation()
  const navigate = useNavigate()

  useEffect(() => {
    setStage(stageMap[uiMode])
  }, [setStage, uiMode])

  const handleModeChange = (nextMode: WorkspaceMode) => {
    setMode(nextMode)

    const workspaceMatch = matchPath('/workspace/:projectId/*', location.pathname)
    const projectId = workspaceMatch?.params.projectId

    if (!projectId) {
      return
    }

    navigate(`/workspace/${projectId}/${nextMode}`)
  }

  return (
    <div className={`min-h-screen bg-${mode === 'dark' ? 'gray-900' : 'gray-100'}`}>
      <header className="border-b border-gray-300 bg-white dark:bg-gray-800">
        <div className="flex items-center justify-between px-4 py-3">
          <h1 className="text-xl font-bold">Narrative Engine</h1>
          <div className="flex items-center gap-4">
            <select
              value={uiMode}
              onChange={(e) => handleModeChange(e.target.value as WorkspaceMode)}
              className="border rounded px-2 py-1 text-sm"
            >
              <option value="plan">Planning</option>
              <option value="write">Writing</option>
              <option value="review">Review</option>
              <option value="inspect">Inspect</option>
            </select>
            <button
              onClick={toggleMode}
              className="px-3 py-1 border rounded hover:bg-gray-100"
            >
              {mode === 'dark' ? '☀️' : '🌙'}
            </button>
          </div>
        </div>
      </header>
      <main className="p-4">{children}</main>
    </div>
  )
}
