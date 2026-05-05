import { beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { InlineActions } from './InlineActions'

describe('InlineActions', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders correct number of action buttons', () => {
    const actions = [
      { label: 'Save', onClick: vi.fn() },
      { label: 'Cancel', onClick: vi.fn() },
      { label: 'Delete', onClick: vi.fn() },
    ]

    render(<InlineActions actions={actions} />)

    expect(screen.getByRole('button', { name: 'Save' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Cancel' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Delete' })).toBeInTheDocument()
  })

  it('calls onClick when button is clicked', async () => {
    const handleClick = vi.fn()
    const actions = [{ label: 'Click me', onClick: handleClick }]

    render(<InlineActions actions={actions} />)

    const button = screen.getByRole('button', { name: 'Click me' })
    button.click()

    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('disables button when isLoading is true', () => {
    const actions = [{ label: 'Loading', isLoading: true, onClick: vi.fn() }]

    render(<InlineActions actions={actions} />)

    expect(screen.getByRole('button', { name: 'Loading' })).toBeDisabled()
  })

  it('applies danger variant when danger flag is set', () => {
    const actions = [{ label: 'Delete', danger: true, onClick: vi.fn() }]

    render(<InlineActions actions={actions} />)

    const button = screen.getByRole('button', { name: 'Delete' })
    expect(button).toHaveClass('bg-red-600')
  })
})
