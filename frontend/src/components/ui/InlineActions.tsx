import { Button } from './Button'

export interface InlineAction {
  label: string
  variant?: 'primary' | 'ghost' | 'soft' | 'danger'
  onClick?: () => void
  onConfirm?: () => Promise<void>
  danger?: boolean
  disabled?: boolean
  isLoading?: boolean
}

export interface InlineActionsProps {
  actions: InlineAction[]
  className?: string
}

export function InlineActions({ actions, className = '' }: InlineActionsProps) {
  return (
    <div className={`flex items-center gap-2 ${className}`}>
      {actions.map((action, index) => {
        const isDisabled = action.disabled || action.isLoading
        const variant = action.danger ? 'danger' : (action.variant ?? 'ghost')

        return (
          <Button
            key={`${action.label}-${index}`}
            variant={variant}
            size="sm"
            disabled={isDisabled}
            isLoading={action.isLoading}
            onClick={action.onClick}
          >
            {action.label}
          </Button>
        )
      })}
    </div>
  )
}
