import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { DEBT_LIST_PAGE_SIZE, deleteDebt, getDebtAnalytics, getDebts } from '../../api/debtsApi'
import type { DebtListFilters } from '../../types/debt'
import { isAdminUser } from '../../utils/authRoles'
import { paginatedListQueryOptions } from '../../utils/paginatedListQuery'
import { toast } from '../../utils/toast'
import type { AuthUser } from '../../store/authStore'

export function useDebtsList(filters: DebtListFilters, user: AuthUser | null) {
  const queryClient = useQueryClient()
  const isAdmin = isAdminUser(user)

  const analyticsQuery = useQuery({
    queryKey: ['debts', 'analytics'],
    queryFn: getDebtAnalytics,
    staleTime: 60_000,
  })

  const listQuery = useQuery({
    queryKey: ['debts', 'list', filters],
    queryFn: () => getDebts(filters),
    staleTime: 30_000,
    ...paginatedListQueryOptions,
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteDebt(id),
    onSuccess: () => {
      toast.success('Запись о долге удалена')
      void queryClient.invalidateQueries({ queryKey: ['debts'] })
    },
    onError: () => {
      toast.error('Не удалось удалить запись')
    },
  })

  const paginated = listQuery.data?.paginated
  const count = paginated?.count ?? 0
  const totalPages = Math.max(1, Math.ceil(count / DEBT_LIST_PAGE_SIZE))
  const currentPage = filters.page ?? 1
  const results = paginated?.results ?? []
  const lastFourMonthLabels = listQuery.data?.lastFourMonthLabels ?? []

  return {
    analyticsQuery,
    listQuery,
    deleteMutation,
    count,
    totalPages,
    currentPage,
    results,
    lastFourMonthLabels,
    isAdmin,
  }
}
