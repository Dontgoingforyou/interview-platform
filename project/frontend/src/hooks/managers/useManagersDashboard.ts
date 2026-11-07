import { useQuery } from '@tanstack/react-query'

import { getManagersAnalytics, getManagersDashboardTable, getManagersObservations } from '../../api/managersApi'
import { paginatedListQueryOptions } from '../../utils/paginatedListQuery'

const STALE_ANALYTICS_MS = 5 * 60_000
const STALE_TABLE_OBS_MS = 2 * 60_000

/** Загрузка дашборда «Менеджеры»: KPI, таблица, наблюдения. */
export function useManagersDashboard() {
  const analyticsQuery = useQuery({
    queryKey: ['managers', 'analytics'],
    queryFn: getManagersAnalytics,
    staleTime: STALE_ANALYTICS_MS,
  })

  const observationsQuery = useQuery({
    queryKey: ['managers', 'observations'],
    queryFn: getManagersObservations,
    staleTime: STALE_TABLE_OBS_MS,
  })

  const tableQuery = useQuery({
    queryKey: ['managers', 'table'],
    queryFn: getManagersDashboardTable,
    staleTime: STALE_TABLE_OBS_MS,
    ...paginatedListQueryOptions,
  })

  return { analyticsQuery, observationsQuery, tableQuery }
}
