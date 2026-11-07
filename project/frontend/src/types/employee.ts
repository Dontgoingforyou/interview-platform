/** Элемент списка менеджеров на странице «Сотрудники». */
export interface EmployeeManagerListItem {
  email: string
  full_name: string
}

export interface BoardManager {
  email: string
  full_name: string
}

export interface BoardIntern {
  id: number
  full_name: string
  email: string
  group: string
  manager_email: string
  direction_id: number | null
  real_interview_date: string | null
}

export interface BoardAbsenceInfo {
  status: string
  status_display: string
  notes: string
}

export interface BoardRecentWeekData {
  count: number
  week_start: string
  absence_info: BoardAbsenceInfo | null
  week_idx: number
}

export interface BoardInternRow {
  intern: BoardIntern
  stats: number[]
  recent_stats: number[]
  recent_weeks_data: BoardRecentWeekData[]
  week_statuses: (BoardAbsenceInfo | null)[]
  exclude_from_coefficient: boolean[]
  status: string
  status_display: string
}

export interface BoardMonthWeekCell {
  count: number | string
  week_start: string | null
  absence_info: BoardAbsenceInfo | null
  week_idx: number
}

export interface BoardAllInternRow {
  intern: BoardIntern
  month: string
  month_weeks_data: BoardMonthWeekCell[]
  status: string
  status_display: string
}

export interface BoardAllMonthWeek {
  week_start: string
  week_end: string
}

export interface ManagerBoardResponse {
  manager: BoardManager
  recent_weeks: [string, string][]
  coefficients: number[]
  active_interns: BoardInternRow[]
  inactive_interns: BoardInternRow[]
  all_months: Record<string, BoardAllMonthWeek[]>
  all_months_formatted: Record<string, [string, string][]>
  all_interns: BoardAllInternRow[]
  directions_dict: Record<string, string>
  intern_statuses: Record<string, string>
}

export interface AdminKpiManager {
  full_name: string
  email: string
  is_active: boolean
}

export interface AdminKpiQualifyingWeek {
  week_start: string
  week_end: string
  kpi: number
  active_count: number
  total_interviews: number
}

export interface AdminKpiRow {
  manager: AdminKpiManager
  qualifying_weeks_count: number
  qualifying_weeks: AdminKpiQualifyingWeek[]
  total_active_devs: number
}

export interface AdminKpiResponse {
  date_from: string
  date_to: string
  min_kpi: number
  results: AdminKpiRow[]
}

export interface AdminDeveloperIntern {
  id: number
  full_name: string
  email: string
  group: string
  manager_email: string
}

export interface AdminDeveloperRow {
  manager: AdminKpiManager
  active_count: number
  interns: AdminDeveloperIntern[]
}

export interface AdminDevelopersResponse {
  results: AdminDeveloperRow[]
  hidden_results: AdminDeveloperRow[]
  total_active: number
  hidden_count: number
}

export interface WeeklyStatusDto {
  id: number
  intern: number
  intern_name: string
  week_start: string
  manual_interview_count: number | null
  absence_status: string | null
  absence_notes: string
  created_at: string
  updated_at: string
}
