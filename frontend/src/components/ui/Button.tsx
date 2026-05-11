import { ButtonHTMLAttributes, ReactNode } from 'react'
import { Loader2 } from 'lucide-react'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost' | 'outline' | 'soft'
  size?: 'sm' | 'md' | 'lg'
  children: ReactNode
  isLoading?: boolean
  icon?: ReactNode
}

export function Button({
  variant = 'primary',
  size = 'md',
  children,
  isLoading = false,
  disabled,
  icon,
  className = '',
  ...props
}: ButtonProps) {
  const baseStyles = [
    'inline-flex items-center justify-center font-medium',
    'rounded-lg',
    'transition-all duration-200',
    'focus:outline-none focus:ring-2 focus:ring-offset-1',
    'active:scale-[0.98]',
    'disabled:opacity-60 disabled:cursor-not-allowed',
    'disabled:active:scale-100',
    'focus:ring-offset-[var(--bg-primary)]',
  ].join(' ')

  const variantStyles: Record<string, string> = {
    primary: [
      'bg-[var(--color-primary)] text-[var(--text-inverse)]',
      'hover:bg-[var(--color-primary-hover)]',
      'focus:ring-[var(--color-primary)]/40',
      'shadow-sm shadow-[var(--color-primary)]/20',
    ].join(' '),
    secondary: [
      'bg-[var(--bg-secondary)] text-[var(--text-secondary)]',
      'hover:bg-[var(--bg-tertiary)] hover:text-[var(--text-primary)]',
      'focus:ring-[var(--color-primary)]/30',
    ].join(' '),
    danger: [
      'bg-[var(--color-danger)] text-[var(--text-inverse)]',
      'hover:bg-[var(--color-warning)]',
      'focus:ring-[var(--color-danger)]/40',
      'shadow-sm shadow-[var(--color-danger)]/20',
    ].join(' '),
    ghost: [
      'bg-transparent text-[var(--text-secondary)]',
      'hover:bg-[var(--bg-secondary)] hover:text-[var(--text-primary)]',
      'focus:ring-[var(--color-primary)]/30',
    ].join(' '),
    outline: [
      'border border-[var(--border-secondary)] text-[var(--text-primary)]',
      'hover:bg-[var(--bg-secondary)] hover:text-[var(--text-inverse)]',
      'focus:ring-[var(--color-primary)]/30',
    ].join(' '),
    soft: [
      'bg-[var(--color-primary-subtle)] text-[var(--color-primary)]',
      'hover:bg-[var(--color-primary-border)] hover:text-[var(--text-inverse)]',
      'focus:ring-[var(--color-primary)]/30',
    ].join(' '),
  }

  const sizeStyles: Record<string, string> = {
    sm: 'px-3 py-1.5 text-xs gap-1.5',
    md: 'px-4 py-2 text-sm gap-2',
    lg: 'px-6 py-3 text-base gap-2.5',
  }

  return (
    <button
      className={`${baseStyles} ${variantStyles[variant]} ${sizeStyles[size]} ${className}`}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading && <Loader2 className="w-4 h-4 animate-spin" />}
      {!isLoading && icon}
      {children}
    </button>
  )
}
