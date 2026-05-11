import { InputHTMLAttributes } from 'react'

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
}

export function Input({ label, error, className = '', ...props }: InputProps) {
  const baseStyles = [
    'w-full px-3 py-2 rounded-lg',
    'text-sm font-medium',
    'transition-all duration-150',
    'focus:outline-none focus:ring-2 focus:ring-offset-1',
    'focus:ring-offset-[var(--bg-primary)]',
  ].join(' ')

  const errorStyles = [
    'border-[var(--color-danger)]',
    'focus:ring-[var(--color-danger)]/40',
    'focus:border-[var(--color-danger)]',
  ].join(' ')

  const normalStyles = [
    'bg-[var(--bg-secondary)] border-[var(--border-primary)]',
    'text-[var(--text-primary)] placeholder-[var(--text-tertiary)]',
    'focus:ring-[var(--color-primary)]/30 focus:border-[var(--color-primary)]',
    'hover:border-[var(--border-secondary)]',
  ].join(' ')

  const inputStyles = `${baseStyles} ${error ? errorStyles : normalStyles} ${className}`

  return (
    <div className="flex flex-col gap-1.5">
      {label && (
        <label className="text-xs font-semibold uppercase tracking-widest text-[var(--text-tertiary)]">
          {label}
        </label>
      )}
      <input className={inputStyles} {...props} />
      {error && (
        <span className="text-xs text-[var(--color-danger)] font-medium">
          {error}
        </span>
      )}
    </div>
  )
}
