/**
 * Список сотрудников: замоканные менеджеры, без запроса поиска стажёров (q короче 2 символов).
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen } from '@testing-library/react'

import EmployeesListPage from '../../pages/employees/EmployeesListPage'
import { renderWithProviders } from '../testUtils'

const mockUseEmployeesManagers = vi.fn()

vi.mock('../../hooks/employees/useEmployeesManagers', () => ({
  useEmployeesManagers: () => mockUseEmployeesManagers(),
}))

describe('EmployeesListPage', () => {
  beforeEach(() => {
    mockUseEmployeesManagers.mockReturnValue({
      data: [{ email: 'lead@test', full_name: 'Руководитель Тестовый' }],
      isLoading: false,
      isError: false,
      isFetching: false,
    })
  })

  it('показывает таблицу менеджеров из мока', () => {
    renderWithProviders(<EmployeesListPage />, { initialEntries: ['/employees'] })
    expect(screen.getByText('Менеджеры')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Руководитель Тестовый' })).toBeInTheDocument()
  })
})
