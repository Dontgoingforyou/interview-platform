import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'

import MetricCard from '../../../components/ui/MetricCard'

describe('MetricCard', () => {
  it('отображает подпись и дочерний контент', () => {
    render(
      <MetricCard label="Всего записей">
        <strong>100</strong>
      </MetricCard>,
    )
    expect(screen.getByText('Всего записей')).toBeInTheDocument()
    expect(screen.getByText('100')).toBeInTheDocument()
  })
})
