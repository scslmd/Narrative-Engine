import { HTMLAttributes, ReactNode } from 'react'

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode
  title?: string
  actions?: ReactNode
  variant?: 'default' | 'elevated' | 'outlined'
}

export function Card({
  children,
  title,
  actions,
  variant = 'default',
  className = '',
  ...props
}: CardProps) {
  const variantStyles = {
    default: 'bg-white dark:bg-gray-800',
    elevated: 'bg-white dark:bg-gray-800 shadow-lg',
    outlined: 'bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700',
  }

  return (
    <div
      className={`rounded-lg p-4 ${variantStyles[variant]} ${className}`}
      {...props}
    >
      {(title || actions) && (
        <div className="flex items-center justify-between mb-4">
          {title && <h3 className="text-lg font-semibold">{title}</h3>}
          {actions && <div>{actions}</div>}
        </div>
      )}
      {children}
    </div>
  )
}