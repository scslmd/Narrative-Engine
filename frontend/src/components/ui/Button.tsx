import { ButtonHTMLAttributes, ReactNode } from 'react'
import { Loader2 } from 'lucide-react'
import { useThemeStore } from '../../stores/themeStore'

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
  const { mode } = useThemeStore()
  const isDark = ['dark', 'midnight', 'forest', 'ocean'].includes(mode)
  
  const baseStyles = 'inline-flex items-center justify-center font-medium rounded-lg transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-offset-2 active:scale-[0.98] disabled:opacity-60 disabled:cursor-not-allowed disabled:active:scale-100'
  
  const variantStyles: Record<string, string> = {
    primary: isDark
      ? 'bg-indigo-500 text-white hover:bg-indigo-400 focus:ring-indigo-500/40 shadow-sm shadow-indigo-500/20'
      : 'bg-indigo-600 text-white hover:bg-indigo-700 focus:ring-indigo-500/40 shadow-sm shadow-indigo-500/20',
    secondary: isDark
      ? 'bg-slate-700 text-slate-200 hover:bg-slate-600 focus:ring-slate-500/40'
      : 'bg-slate-100 text-slate-700 hover:bg-slate-200 focus:ring-slate-400/40',
    danger: isDark
      ? 'bg-red-500 text-white hover:bg-red-400 focus:ring-red-500/40 shadow-sm shadow-red-500/20'
      : 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500/40 shadow-sm shadow-red-500/20',
    ghost: isDark
      ? 'bg-transparent text-slate-400 hover:bg-slate-800 hover:text-slate-200 focus:ring-slate-500/40'
      : 'bg-transparent text-slate-600 hover:bg-slate-100 hover:text-slate-900 focus:ring-slate-400/40',
    outline: isDark
      ? 'border border-slate-600 text-slate-300 hover:bg-slate-800 hover:text-slate-100 focus:ring-slate-500/40'
      : 'border border-slate-300 text-slate-700 hover:bg-slate-50 hover:text-slate-900 focus:ring-slate-400/40',
    soft: isDark
      ? 'bg-slate-800/60 text-slate-300 hover:bg-slate-700/80 hover:text-slate-100 focus:ring-slate-500/40'
      : 'bg-slate-100 text-slate-700 hover:bg-slate-200/80 hover:text-slate-900 focus:ring-slate-400/40',
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
