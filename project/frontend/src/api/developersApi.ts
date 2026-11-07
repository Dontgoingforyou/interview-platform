import apiClient from './client'
import { normalizePaginatedResponse } from './normalizePaginatedResponse'
import type { Paginated } from '../types/common'
import type { DeveloperAnalytics, DeveloperListFilters, DeveloperStatRow } from '../types/developer'
import {
  buildDeveloperListParams,
  buildDeveloperTableExportParams,
} from '../utils/developers/developerListParams'
import { downloadBlobResponse } from '../utils/downloadBlob'

const LIST_URL = '/api/developers/'

export const DEVELOPER_LIST_PAGE_SIZE = 20

export async function getDeveloperAnalytics(): Promise<DeveloperAnalytics> {
  const { data } = await apiClient.get<DeveloperAnalytics>('/api/analytics/developers/')
  return data
}

export async function getDevelopersList(filters: DeveloperListFilters): Promise<Paginated<DeveloperStatRow>> {
  const params = buildDeveloperListParams(filters)
  const { data } = await apiClient.get(LIST_URL, { params })
  return normalizePaginatedResponse<DeveloperStatRow>(data)
}

export async function downloadDevelopersTableExport(filters: DeveloperListFilters): Promise<void> {
  const response = await apiClient.get<Blob>(`${LIST_URL}export/table/`, {
    params: buildDeveloperTableExportParams(filters),
    responseType: 'blob',
  })
  downloadBlobResponse(response, 'developers_table.xlsx')
}

export async function downloadDevelopersMetricsExport(): Promise<void> {
  const response = await apiClient.get<Blob>(`${LIST_URL}export/metrics/`, { responseType: 'blob' })
  downloadBlobResponse(response, 'developers_metrics.xlsx')
}

export async function downloadDevelopersChartExport(): Promise<void> {
  const response = await apiClient.get<Blob>(`${LIST_URL}export/chart/`, { responseType: 'blob' })
  downloadBlobResponse(response, 'developers_chart.xlsx')
}
