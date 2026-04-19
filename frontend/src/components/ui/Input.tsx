import { InputHTMLAttributes } from 'react'

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
}

export function Input({ label, error, className = '', ...props }: InputProps) {
  const isDark = document.documentElement.getAttribute('data-theme') === 'dark'
  
  const baseStyles = `w-full px-3 py-2 rounded-lg border text-sm transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-offset-0 ${isDark ? 'focus:ring-offset-slate-900' : 'focus:ring-offset-white'}`
  
  const inputStyles = `${baseStyles} ${
    error 
      ? 'border-red-500 focus:ring-red-500/40 focus:border-red-500'
      : isDark
        ? 'bg-slate-800 border-slate-700 text-slate-200 placeholder-slate-500 focus:border-indigo-500 focus:ring-indigo-500/30 hover:border-slate-600'
        : 'bg-white border-slate-300 text-slate-900 placeholder-slate-400 focus:border-indigo-500 focus:ring-indigo-500/30 hover:border-slate-400'
  } ${className}`

  return (
    <div className="flex flex-col gap-1.5">
      {label && <label className={`text-xs font-semibold uppercase tracking-wider ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>{label}</label>}
      <input className={inputStyles} {...props} />
      {error && <span className="text-xs text-red-500 font-medium">{error}</span>}
    </div>
  )
}
