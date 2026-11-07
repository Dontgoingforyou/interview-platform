/**
 * Список собеседований с замоканным useInterviewList — без Django.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen } from '@testing-library/react'

import InterviewsListPage from '../../pages/interviews/InterviewsListPage'
import type { AuthUser } from '../../store/authStore'
import { minimalInterviewAnalytics, sampleInterviewListItem } from '../fixtures/interviewList'
import { renderWithProviders } from '../testUtils'

const authState = vi.hoisted(() => ({
  user: null as AuthUser | null,
}))

vi.mock('../../store/authStore', () => ({
  useAuthStore: (selector: (s: { user: AuthUser | null }) => unknown) =>
    selector({ user: authState.user }),
}))

const mockUseInterviewList = vi.fn()

vi.mock('../../hooks/interviews/useInterviewList', () => ({
  useInterviewList: (...args: unknown[]) => mockUseInterviewList(...args),
}))

function buildInterviewListHookReturn(overrides: Record<string, unknown> = {}) {
  const analytics = minimalInterviewAnalytics()
  return {
    analyticsQuery: { isLoading: false, isError: false, data: analytics },
    typeBreakdownQuery: { isError: false, data: { total: 0 } },
    directionsQuery: { data: [], isLoading: false },
    managersQuery: { data: [], isLoading: false },
    spaConfigQuery: { data: undefined },
    deepgramQuery: { data: undefined, isLoading: false },
    listQuery: {
      isLoading: false,
      isSuccess: true,
      isError: false,
      isFetching: false,
      data: { results: [], count: 0 },
    },
    deleteMutation: { mutate: vi.fn() },
    importMutation: { mutate: vi.fn(), isPending: false },
    importStatusQuery: {},
    importTaskId: null,
    setImportTaskId: vi.fn(),
    totalPages: 1,
    currentPage: 1,
    results: [],
    ...overrides,
  }
}

describe('InterviewsListPage', () => {
  beforeEach(() => {
    authState.user = {
      email: 'm@test',
      username: 'm',
      full_name: 'Менеджер',
      manager_role: 'manager',
      groups: ['employment'],
    }
    mockUseInterviewList.mockReturnValue(buildInterviewListHookReturn())
  })

  it('показывает вводную карточку и секцию фильтров после загрузки', () => {
    renderWithProviders(<InterviewsListPage />, { initialEntries: ['/interviews'] })
    expect(screen.getByText(/Общая аналитика собеседований/)).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Поиск и фильтры' })).toBeInTheDocument()
  })

  it('показывает имя кандидата при непустом списке', () => {
    const row = sampleInterviewListItem()
    mockUseInterviewList.mockReturnValue(
      buildInterviewListHookReturn({
        listQuery: {
          isLoading: false,
          isSuccess: true,
          isError: false,
          isFetching: false,
          data: { results: [row], count: 1 },
        },
        results: [row],
      }),
    )
    renderWithProviders(<InterviewsListPage />, { initialEntries: ['/interviews'] })
    expect(screen.getAllByText('Кандидат Тестовый').length).toBeGreaterThanOrEqual(1)
  })
})
