import { useQuery } from '@tanstack/react-query'

import { getDirectionMetrics, getDirectionObservations } from '../../api/directionsApi'
import {
  directionMetricsFiltersKey,
  directionMetricsToApiParams,
} from '../../utils/directions/directionMetricsParams'
import type { DirectionMetricsPageFilters } from '../../types/direction'

export function useDirectionsMetricsPage(filters: DirectionMetricsPageFilters) {
  const params = directionMetricsToApiParams(filters)
  const metricsQuery = useQuery({
    queryKey: ['directions', 'metrics', directionMetricsFiltersKey(filters)],
    queryFn: () => getDirectionMetrics(params),
  })

  const observationsQuery = useQuery({
    queryKey: ['directions', 'observations'],
    queryFn: getDirectionObservations,
  })

  return { metricsQuery, observationsQuery }
}
