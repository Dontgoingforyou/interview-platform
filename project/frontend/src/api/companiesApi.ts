import apiClient from './client'
import { normalizePaginatedResponse } from './normalizePaginatedResponse'
import type { Paginated } from '../types/common'
import type {
  CompanyListFilters,
  CompanyListItem,
  CompanyMergeResponse,
  CompanyStats,
  CompanyWritePayload,
} from '../types/company'
const BASE = '/api/companies/'

/** Размер страницы списка. */
export const COMPANY_LIST_PAGE_SIZE = 50

function buildListParams(filters: CompanyListFilters): Record<string, string | number | boolean> {
  const params: Record<string, string | number | boolean> = {
    page: filters.page,
    page_size: COMPANY_LIST_PAGE_SIZE,
    sort: filters.sort,
  }
  if (filters.q) {
    params.q = filters.q
  }
  if (filters.bigtech === '1') {
    params.is_bigtech = true
  } else if (filters.bigtech === '0') {
    params.is_bigtech = false
  }
  return params
}

export async function getCompanyStats(): Promise<CompanyStats> {
  const { data } = await apiClient.get<CompanyStats>('/api/companies/stats/')
  return data
}

export async function getCompaniesPaginated(filters: CompanyListFilters): Promise<Paginated<CompanyListItem>> {
  const { data } = await apiClient.get<Paginated<CompanyListItem> | CompanyListItem[]>(BASE, {
    params: buildListParams(filters),
  })
  return normalizePaginatedResponse(data)
}

export async function getCompany(id: number): Promise<CompanyListItem> {
  const { data } = await apiClient.get<CompanyListItem>(`${BASE}${id}/`)
  return data
}

export async function updateCompany(id: number, payload: Partial<CompanyWritePayload>): Promise<CompanyListItem> {
  const { data } = await apiClient.patch<CompanyListItem>(`${BASE}${id}/`, payload)
  return data
}

export async function deleteCompany(id: number): Promise<void> {
  await apiClient.delete(`${BASE}${id}/`)
}

export async function mergeCompanies(primaryId: number, duplicateIds: number[]): Promise<CompanyMergeResponse> {
  const { data } = await apiClient.post<CompanyMergeResponse>('/api/companies/merge/', {
    primary_id: primaryId,
    duplicate_ids: duplicateIds,
  })
  return data
}

/** Опции для react-select (поиск по справочнику). */
export interface CompanySelectOption {
  id: number
  name: string
}

/**
 * Поиск компаний для селектов (собеседования, объединение).
 * Возвращает до 100 записей.
 */
export async function searchCompaniesForSelect(q: string): Promise<CompanySelectOption[]> {
  const params: Record<string, string | number> = { page_size: 100 }
  const trimmed = q.trim()
  if (trimmed) {
    params.q = trimmed
  }
  const { data } = await apiClient.get<Paginated<CompanySelectOption> | CompanySelectOption[]>(BASE, {
    params,
  })
  const paginated = normalizePaginatedResponse(data)
  return paginated.results.map((r) => ({ id: r.id, name: r.name }))
}
