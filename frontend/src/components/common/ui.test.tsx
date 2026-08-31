import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { AqiBadge } from '@/components/common/AqiBadge'
import { SeverityChip } from '@/components/common/Chips'
import { EmptyState } from '@/components/common/EmptyState'
import { LoadingSkeleton } from '@/components/common/LoadingSkeleton'

describe('AqiBadge', () => {
  it('shows the numeric value and CPCB category', () => {
    render(<AqiBadge value={310} />)
    const badge = screen.getByTitle('AQI category: Very Poor')
    expect(badge).toBeInTheDocument()
    expect(badge.textContent).toContain('310')
    expect(badge.textContent).toContain('Very Poor')
  })

  it('falls back to category-only rendering', () => {
    render(<AqiBadge value={40} showValue={false} />)
    expect(screen.getByTitle('AQI category: Good').textContent).toContain('Good')
    expect(screen.getByTitle('AQI category: Good').textContent).not.toContain('40')
  })
})

describe('SeverityChip', () => {
  it('renders severity labels accessibly', () => {
    render(<SeverityChip severity="critical" />)
    expect(screen.getByText('critical')).toBeInTheDocument()
  })
})

describe('states', () => {
  it('empty state communicates absence of data', () => {
    render(<EmptyState message="Nothing here yet" />)
    expect(screen.getByText('Nothing here yet')).toBeInTheDocument()
  })

  it('loading skeleton exposes a loading status', () => {
    render(<LoadingSkeleton rows={2} />)
    expect(screen.getByRole('status')).toBeInTheDocument()
  })
})
