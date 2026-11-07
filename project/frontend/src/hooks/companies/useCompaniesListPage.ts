import { useQuery } from '@tanstack/react-query'

import { getCompaniesPaginated, getCompanyStats } from '../../api/companiesApi'
import type { CompanyListFilters } from '../../types/company'
import { paginatedListQueryOptions } from '../../utils/paginatedListQuery'

/**
 * Список компаний и сводная статистика для страницы списка.
 */
export function useCompaniesListPage(filters: CompanyListFilters) {
  const statsQuery = useQuery({
    queryKey: ['companies', 'stats'],
    queryFn: getCompanyStats,
    staleTime: 60_000,
  })

  const listQuery = useQuery({
    queryKey: ['companies', 'list', filters],
    queryFn: () => getCompaniesPaginated(filters),
    ...paginatedListQueryOptions,
  })

  return { statsQuery, listQuery }
}
