import apiClient from './client'
import type {
  ManagersAnalytics,
  ManagersDashboardTableRow,
  ManagersObservations,
} from '../types/managerDashboard'

const ANALYTICS_MANAGERS_BASE = '/api/analytics/managers/'

export async function getManagersAnalytics(): Promise<ManagersAnalytics> {
  const { data } = await apiClient.get<ManagersAnalytics>(ANALYTICS_MANAGERS_BASE)
  return data
}

export async function getManagersObservations(): Promise<ManagersObservations> {
  const { data } = await apiClient.get<ManagersObservations>(`${ANALYTICS_MANAGERS_BASE}observations/`)
  return data
}

export async function getManagersDashboardTable(): Promise<ManagersDashboardTableRow[]> {
  const { data } = await apiClient.get<{ results: ManagersDashboardTableRow[] }>(
    `${ANALYTICS_MANAGERS_BASE}table/`,
  )
  return data.results
}

export interface ManagerPatchPayload {
  full_name?: string
  username?: string
  is_active?: boolean
}

export async function patchManagerUpdate(
  email: string,
  payload: ManagerPatchPayload,
): Promise<Record<string, unknown>> {
  const enc = encodeURIComponent(email)
  const { data } = await apiClient.patch<Record<string, unknown>>(`/api/managers/${enc}/update/`, payload)
  return data
}
