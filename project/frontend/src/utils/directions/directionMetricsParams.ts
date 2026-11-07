import type { DirectionMetricsPageFilters } from '../../types/direction'

/**
 * Парсинг query string страницы метрик направлений.
 */
export function parseDirectionMetricsFromSearchParams(
  searchParams: URLSearchParams,
): DirectionMetricsPageFilters {
  const directionRaw = searchParams.get('direction')
  let direction: number | null = null
  if (directionRaw != null && directionRaw !== '') {
    const n = parseInt(directionRaw, 10)
    direction = Number.isNaN(n) ? null : n
  }
  const min_conversion = searchParams.get('min_conversion')
  const date_filter = searchParams.get('date_filter')
  return {
    direction,
    min_conversion: min_conversion && min_conversion !== '' ? min_conversion : null,
    date_filter: date_filter && date_filter !== '' ? date_filter : null,
  }
}

/** Параметры для GET /api/analytics/directions/ */
export function directionMetricsToApiParams(filters: DirectionMetricsPageFilters): Record<string, string> {
  const out: Record<string, string> = {}
  if (filters.direction != null) {
    out.direction = String(filters.direction)
  }
  if (filters.min_conversion != null) {
    out.min_conversion = filters.min_conversion
  }
  if (filters.date_filter != null) {
    out.date_filter = filters.date_filter
  }
  return out
}

/** Стабильная строка для queryKey TanStack Query. */
export function directionMetricsFiltersKey(filters: DirectionMetricsPageFilters): string {
  return JSON.stringify({
    direction: filters.direction,
    min_conversion: filters.min_conversion,
    date_filter: filters.date_filter,
  })
}
