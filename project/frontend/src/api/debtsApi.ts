import apiClient from './client'
import { normalizePaginatedResponse } from './normalizePaginatedResponse'
import type { Paginated } from '../types/common'
import type {
  DebtAnalytics,
  DebtByMonthApiResponse,
  DebtByMonthFilters,
  DebtByMonthRow,
  DebtDetail,
  DebtListApiResponse,
  DebtListFilters,
  DebtListItem,
  DebtWritePayload,
  PaginatedDebts,
} from '../types/debt'
import { buildDebtByMonthParams } from '../utils/debts/debtByMonthParams'
import { buildDebtListParams } from '../utils/debts/debtListParams'

const BASE = '/api/debts/'

export const DEBT_LIST_PAGE_SIZE = 20

export async function getDebtAnalytics(): Promise<DebtAnalytics> {
  const { data } = await apiClient.get<DebtAnalytics>('/api/analytics/debts/')
  return data
}

export async function getDebts(filters: DebtListFilters): Promise<{
  paginated: PaginatedDebts
  lastFourMonthLabels: string[]
}> {
  const params = buildDebtListParams(filters)
  const { data } = await apiClient.get<DebtListApiResponse | DebtListItem[]>(BASE, { params })
  if (Array.isArray(data)) {
    return { paginated: normalizePaginatedResponse(data), lastFourMonthLabels: [] }
  }
  const labels = data.last_four_month_labels ?? []
  const paginated = normalizePaginatedResponse({
    count: data.count,
    next: data.next,
    previous: data.previous,
    results: data.results,
  })
  return { paginated, lastFourMonthLabels: labels }
}

export async function getDebtsByMonth(filters: DebtByMonthFilters): Promise<{
  paginated: Paginated<DebtByMonthRow>
  exportMonths: string[]
  selectedPeriod: string
}> {
  const params = buildDebtByMonthParams(filters)
  const { data } = await apiClient.get<DebtByMonthApiResponse>(`${BASE}by-month/`, { params })
  const exportMonths = data.export_months ?? []
  const selectedPeriod = data.selected_period ?? ''
  const paginated = normalizePaginatedResponse<DebtByMonthRow>({
    count: data.count,
    next: data.next,
    previous: data.previous,
    results: data.results,
  })
  return { paginated, exportMonths, selectedPeriod }
}

export async function getDebt(id: number): Promise<DebtDetail> {
  const { data } = await apiClient.get<DebtDetail>(`${BASE}${id}/`)
  return data
}

export async function createDebt(payload: DebtWritePayload): Promise<DebtListItem> {
  const { data } = await apiClient.post<DebtListItem>(BASE, payload)
  return data
}

export async function updateDebt(id: number, payload: Partial<DebtWritePayload>): Promise<DebtListItem> {
  const { data } = await apiClient.patch<DebtListItem>(`${BASE}${id}/`, payload)
  return data
}

export async function deleteDebt(id: number): Promise<void> {
  await apiClient.delete(`${BASE}${id}/`)
}

export async function addDebtPayment(
  id: number,
  body: { month: number; year: number; amount: string },
): Promise<void> {
  await apiClient.post(`${BASE}${id}/add-payment/`, body)
}

export async function postDebtImport(file: File): Promise<{ status: string; task_id: string }> {
  const body = new FormData()
  body.append('file', file)
  const { data } = await apiClient.post<{ status: string; task_id: string }>('/api/debts/import/', body)
  return data
}
