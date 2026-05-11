import { HTMLAttributes, ReactNode } from 'react'

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
  const variantStyles: Record<string, string> = {
    default: 'bg-[var(--bg-primary)] border border-[var(--border-primary)]',
    elevated: 'bg-[var(--bg-primary)] border border-[var(--border-primary)] shadow-card',
    outlined: 'bg-[var(--bg-primary)] border border-[var(--border-secondary)]',
  }

  const hoverStyle = hover
    ? 'transition-shadow duration-200 hover:shadow-card-hover'
    : ''

  return (
    <div
      className={`rounded-xl p-5 ${variantStyles[variant]} ${hoverStyle} ${className}`}
      {...props}
    >
      {(title || actions) && (
        <div className="flex items-start justify-between mb-4 gap-4">
          <div>
            {title && (
              <h3 className="text-base font-semibold text-[var(--text-primary)] tracking-tight">
                {title}
              </h3>
            )}
            {subtitle && (
              <p className="text-sm mt-0.5 text-[var(--text-secondary)]">
                {subtitle}
              </p>
            )}
          </div>
          {actions && <div className="flex-shrink-0">{actions}</div>}
        </div>
      )}
      {children}
    </div>
  )
}
