import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'

import { hrContactsCell, vacancyCell } from '../../../utils/interviews/interviewCells'

describe('vacancyCell', () => {
  it('— для пустого', () => {
    expect(vacancyCell(null)).toBe('—')
    expect(vacancyCell('  ')).toBe('—')
  })

  it('ссылка для http(s)', () => {
    render(<>{vacancyCell('https://jobs.example/1')}</>)
    const a = screen.getByRole('link', { name: 'Вакансия' })
    expect(a).toHaveAttribute('href', 'https://jobs.example/1')
  })

  it('обрезает длинный текст', () => {
    render(<>{vacancyCell('оченьдлинныйтекствакансии')}</>)
    expect(screen.getByTitle('оченьдлинныйтекствакансии').textContent).toMatch(/…$/)
  })
})

describe('hrContactsCell', () => {
  it('— / telegram / url / plain', () => {
    expect(hrContactsCell(null)).toBe('—')
    const { rerender } = render(<>{hrContactsCell('@hr_user')}</>)
    expect(screen.getByRole('link')).toHaveAttribute('href', 'https://t.me/hr_user')
    rerender(<>{hrContactsCell('https://t.me/hr')}</>)
    expect(screen.getByRole('link')).toHaveAttribute('href', 'https://t.me/hr')
    rerender(<>{hrContactsCell('просто текст')}</>)
    expect(screen.getByText('просто текст')).toBeInTheDocument()
  })
})
