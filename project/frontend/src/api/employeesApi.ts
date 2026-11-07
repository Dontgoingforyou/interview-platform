import apiClient from './client'
import { normalizePaginatedResponse } from './normalizePaginatedResponse'
import type {
  AdminDevelopersResponse,
  AdminKpiResponse,
  EmployeeManagerListItem,
  ManagerBoardResponse,
  WeeklyStatusDto,
} from '../types/employee'
import type { Paginated } from '../types/common'

const MANAGERS_BASE = '/api/employees/managers/'
const WEEKLY_BASE = '/api/employees/weekly-statuses/'

export async function getEmployeeManagers(): Promise<EmployeeManagerListItem[]> {
  const { data } = await apiClient.get<EmployeeManagerListItem[]>(MANAGERS_BASE)
  return data
}

export async function getManagerBoard(managerEmail: string): Promise<ManagerBoardResponse> {
  const enc = encodeURIComponent(managerEmail)
  const { data } = await apiClient.get<ManagerBoardResponse>(`${MANAGERS_BASE}${enc}/board/`)
  return data
}

export async function getEmployeesAdminKpi(params: {
  date_from: string
  date_to: string
  min_kpi?: number
}): Promise<AdminKpiResponse> {
  const { data } = await apiClient.get<AdminKpiResponse>('/api/employees/admin/kpi/', { params })
  return data
}

export async function getEmployeesAdminDevelopers(showHidden: boolean): Promise<AdminDevelopersResponse> {
  const { data } = await apiClient.get<AdminDevelopersResponse>('/api/employees/admin/developers/', {
    params: showHidden ? { show_hidden: 1 } : {},
  })
  return data
}

async function fetchWeeklyStatuses(
  internId: number,
  weekStart: string,
): Promise<WeeklyStatusDto[]> {
  const { data } = await apiClient.get<Paginated<WeeklyStatusDto> | WeeklyStatusDto[]>(WEEKLY_BASE, {
    params: { intern_id: internId, week_start: weekStart },
  })
  return normalizePaginatedResponse(data).results
}

export async function upsertWeeklyStatus(payload: {
  intern: number
  week_start: string
  manual_interview_count?: number | null
  absence_status?: string | null
  absence_notes?: string
}): Promise<WeeklyStatusDto> {
  const existing = await fetchWeeklyStatuses(payload.intern, payload.week_start)
  const row = existing[0]
  if (row) {
    const { data } = await apiClient.patch<WeeklyStatusDto>(`${WEEKLY_BASE}${row.id}/`, payload)
    return data
  }
  const { data } = await apiClient.post<WeeklyStatusDto>(WEEKLY_BASE, payload)
  return data
}
