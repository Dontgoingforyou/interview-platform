import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'

import PageTitle from '../../../components/ui/PageTitle'

describe('PageTitle', () => {
  it('рендерит h1 с переданным текстом', () => {
    render(<PageTitle>Собеседования</PageTitle>)
    expect(screen.getByRole('heading', { level: 1, name: 'Собеседования' })).toBeInTheDocument()
  })
})
