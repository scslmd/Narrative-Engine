import { ReactNode } from 'react'
import { useUIStore } from '../stores/uiStore'
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

  return (
    <div className="flex gap-5">
      <aside className="w-52 flex-shrink-0">
        <nav className="space-y-0.5 py-1">
          {navItems.map((item) => {
            const isActive = mode === item.key
            const Icon = item.icon
            return (
              <button
                key={item.key}
                onClick={() => setMode(item.key as typeof mode)}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 group ${
                  isActive
                    ? 'bg-gradient-to-r from-slate-800/60 to-slate-800/30 text-white shadow-card'
                    : 'text-slate-500 hover:text-slate-700 hover:bg-slate-100/60 dark:text-slate-400 dark:hover:text-slate-200 dark:hover:bg-slate-800/40'
                }`}
              >
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center transition-all duration-150 ${
                  isActive
                    ? `bg-gradient-to-br ${item.gradient} text-white shadow-sm`
                    : 'bg-slate-100 text-slate-400 dark:bg-slate-800 dark:text-slate-500 group-hover:bg-slate-200 dark:group-hover:bg-slate-700'
                }`}>
                  <Icon className="w-4 h-4" />
                </div>
                <span className="flex-1 text-left">{item.label}</span>
                {isActive && (
                  <div className={`w-1.5 h-1.5 rounded-full bg-gradient-to-br ${item.gradient}`} />
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
