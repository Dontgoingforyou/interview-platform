import { useQuery } from '@tanstack/react-query'

import { DEBT_LIST_PAGE_SIZE, getDebtsByMonth } from '../../api/debtsApi'
import type { DebtByMonthFilters } from '../../types/debt'

export function useDebtsByMonth(filters: DebtByMonthFilters) {
  const hasPeriod =
    filters.month_from != null &&
    filters.year_from != null &&
    filters.month_to != null &&
    filters.year_to != null

  const query = useQuery({
    queryKey: ['debts', 'by-month', filters],
    queryFn: () => getDebtsByMonth(filters),
    enabled: hasPeriod,
    staleTime: 30_000,
  })

  const paginated = query.data?.paginated
  const count = paginated?.count ?? 0
  const totalPages = Math.max(1, Math.ceil(count / DEBT_LIST_PAGE_SIZE))
  const currentPage = filters.page ?? 1
  const results = paginated?.results ?? []

  return {
    query,
    exportMonths: query.data?.exportMonths ?? [],
    selectedPeriod: query.data?.selectedPeriod ?? '',
    count,
    totalPages,
    currentPage,
    results,
    hasPeriod,
  }
}
