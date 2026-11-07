/** Строка метрик по одному направлению (таблица на странице метрик). */
export interface DirectionMetricRow {
  direction: { id: number; name: string }
  interviews: number
  tech_interviews: number
  candidates: number
  conversion_rate: number
  upcoming_interviews: number
  last_interview_date: string | null
}

/** Ответ GET /api/analytics/directions/ */
export interface DirectionMetricsResponse {
  'total-directions'?: number
  total_interviews: number
  total_tech_interviews_count: number
  total_candidates: number
  total_upcoming: number
  metrics: DirectionMetricRow[]
  metrics_data: DirectionMetricRow[]
  target_date: string
  directions: number
  top_direction_30: string
  top_direction_90: string
  best_conversion: string
  worst_conversion: string
  fastest_direction: string
  fastest_direction_person: string
  slowest_direction: string
  slowest_direction_person: string
  best_month: string
  worst_month: string
  tech_share: number
  chart_directions: { labels: string[]; data: number[] }
  chart_months: { labels: string[]; data: number[] }
  tooltips: Record<string, string>
}

/** Элемент списка в ответе наблюдений. */
export interface DirectionObservationListItem {
  direction: string
  candidates: number
  interviews: number
  successful: number
  upcoming: number
  cancelled: number
  week_count: number
  managers: number
  last_interview_date: string | null
  active_candidates: number
  avgSpeed: number | null
  successRate: number
  cancelRate: number
}

/** Ответ GET /api/observations/directions/ */
export interface DirectionObservationsResponse {
  list: DirectionObservationListItem[]
  totalDirections: number
  totalCandidates: number
  totalInterviews: number
  fastest: DirectionObservationListItem | null
  slowest: DirectionObservationListItem | null
  highestCancel: DirectionObservationListItem | null
  mostManagers: DirectionObservationListItem | null
  highestUpcoming: DirectionObservationListItem | null
  bestConversion: DirectionObservationListItem | null
  worstConversion: DirectionObservationListItem | null
  focusNeeded: number
  bestMonth: [string, number] | null
  worstMonth: [string, number] | null
}

/** Параметры фильтров страницы метрик (query string). */
export interface DirectionMetricsPageFilters {
  direction: number | null
  min_conversion: string | null
  date_filter: string | null
}
