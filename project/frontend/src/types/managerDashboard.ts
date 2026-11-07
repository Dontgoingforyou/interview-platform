/** Ответ GET `/api/analytics/managers/` */
export interface ManagersAnalytics {
  managers: number
  'hot-candidates': number
  'active-candidates': number
  'portfolio-candidates': number
  'avg-candidates': number
  'top-speed': string
  'top-speed-count': number
  'this-week': number
  tooltips: Record<string, string>
}

/** Элемент списка в наблюдениях (менеджер) */
export interface ManagersObservationListItem {
  manager: string
  candidates: number
  interviews: number
  successful: number
  upcoming: number
  cancelled: number
  week_count: number
  directions: number
  last_interview_date: string | null
  hot_candidates: number
  active_candidates: number
  portfolio_candidates: number
  avgSpeed: number | null
  successRate: number
}

/** Ответ GET `/api/analytics/managers/observations/` */
export interface ManagersObservations {
  list: ManagersObservationListItem[]
  totalManagers: number
  totalCandidates: number
  totalInterviews: number
  fastest: ManagersObservationListItem | null
  slowest: ManagersObservationListItem | null
  successSorted: ManagersObservationListItem[]
  busiest: ManagersObservationListItem | null
  biggestPortfolio: ManagersObservationListItem | null
  upcomingChamp: ManagersObservationListItem | null
  cancelledChamp: ManagersObservationListItem | null
  noSuccessYet: ManagersObservationListItem[]
}

/** Строка GET `/api/analytics/managers/table/` */
export interface ManagersDashboardTableRow {
  email: string
  full_name: string
  candidates_count: number
  hot_candidates_count: number
  active_candidates_count: number
  portfolio_candidates_count: number
  interviews_count: number
  successful_candidates_count: number
  directions: string
  last_interview_date: string | null
}
