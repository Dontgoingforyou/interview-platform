import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import Pagination from '../../components/Pagination'

describe('Pagination', () => {
  it('не рендерится при одной странице', () => {
    const onPageChange = vi.fn()
    const { container } = render(
      <Pagination currentPage={1} totalPages={1} onPageChange={onPageChange} />,
    )
    expect(container.firstChild).toBeNull()
  })

  it('вызывает onPageChange по кнопке «Вперёд»', async () => {
    const user = userEvent.setup()
    const onPageChange = vi.fn()
    render(<Pagination currentPage={1} totalPages={3} onPageChange={onPageChange} />)
    await user.click(screen.getByRole('button', { name: 'Вперёд' }))
    expect(onPageChange).toHaveBeenCalledWith(2)
  })

  it('показывает текущую страницу из total', () => {
    render(<Pagination currentPage={2} totalPages={5} onPageChange={vi.fn()} />)
    expect(screen.getByText('2 из 5')).toBeInTheDocument()
  })
})
