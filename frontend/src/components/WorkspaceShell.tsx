import { ReactNode } from 'react'
import { useUIStore } from '../stores/uiStore'
import { Button } from './ui/Button'

interface WorkspaceShellProps {
  children: ReactNode
}

const modeLabels = {
  plan: 'Planning',
  write: 'Writing',
  review: 'Review',
  inspect: 'Inspect',
} as const

export function WorkspaceShell({ children }: WorkspaceShellProps) {
  const { mode, setMode } = useUIStore()

  return (
    <div className="flex h-full">
      <aside className="w-64 border-r border-gray-300 p-4">
        <nav className="space-y-2">
          {(['plan', 'write', 'review', 'inspect'] as const).map((m) => (
            <Button
              key={m}
              variant={mode === m ? 'primary' : 'ghost'}
              size="sm"
              onClick={() => setMode(m)}
              className="w-full justify-start"
            >
              {modeLabels[m]}
            </Button>
          ))}
        </nav>
      </aside>
      <main className="flex-1 p-4 overflow-auto">{children}</main>
    </div>
  )
}