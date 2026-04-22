import { HTMLAttributes, ReactNode } from 'react'
import { useThemeStore } from '../../stores/themeStore'

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode
  title?: string
  subtitle?: string
  actions?: ReactNode
  variant?: 'default' | 'elevated' | 'outlined'
  hover?: boolean
}

export function Card({
  children,
  title,
  subtitle,
  actions,
  variant = 'default',
  hover = false,
  className = '',
  ...props
}: CardProps) {
  const { mode } = useThemeStore()
  const isDark = ['dark', 'midnight', 'forest', 'ocean'].includes(mode)
  
  const baseBorder = isDark ? 'border-slate-800' : 'border-slate-200'
  const baseBg = isDark ? 'bg-slate-900' : 'bg-white'
  
  const variantStyles: Record<string, string> = {
    default: `${baseBg} border ${baseBorder}`,
    elevated: `${baseBg} border ${baseBorder} shadow-card`,
    outlined: `${baseBg} border ${isDark ? 'border-slate-700' : 'border-slate-300'}`,
  }
  
  const hoverStyle = hover ? `transition-all duration-150 ${isDark ? 'hover:shadow-card-hover hover:border-slate-700' : 'hover:shadow-card-hover hover:border-slate-300'}` : ''
  
  return (
    <div
      className={`rounded-xl p-5 ${variantStyles[variant]} ${hoverStyle} ${className}`}
      {...props}
    >
      {(title || actions) && (
        <div className="flex items-start justify-between mb-4 gap-4">
          <div>
            {title && <h3 className={`text-base font-semibold ${isDark ? 'text-slate-100' : 'text-slate-900'}`}>{title}</h3>}
            {subtitle && <p className={`text-sm mt-0.5 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>{subtitle}</p>}
          </div>
          {actions && <div className="flex-shrink-0">{actions}</div>}
        </div>
      )}
      {children}
    </div>
  )
}
