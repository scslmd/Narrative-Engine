import { ReactNode } from 'react'
import { useThemeStore } from '../stores/themeStore'
import { useUIStore } from '../stores/uiStore'

interface LayoutProps {
  children: ReactNode
}

export function Layout({ children }: LayoutProps) {
  const { mode, toggleMode, setStage } = useThemeStore()
  const { mode: uiMode } = useUIStore()

  const stageMap = {
    plan: 'planning',
    write: 'writing',
    review: 'review',
    inspect: 'inspect',
  } as const

  return (
    <div className={`min-h-screen bg-${mode === 'dark' ? 'gray-900' : 'gray-100'}`}>
      <header className="border-b border-gray-300 bg-white dark:bg-gray-800">
        <div className="flex items-center justify-between px-4 py-3">
          <h1 className="text-xl font-bold">Narrative Engine</h1>
          <div className="flex items-center gap-4">
            <select
              value={uiMode}
              onChange={(e) => setStage(stageMap[e.target.value as keyof typeof stageMap])}
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