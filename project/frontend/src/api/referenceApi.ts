import apiClient from './client'
import { searchCompaniesForSelect } from './companiesApi'

export interface DirectionOption {
  id: number
  name: string
}

export interface CompanyOption {
  id: number
  name: string
}

export interface InternOption {
  id: number
  full_name: string
  direction_id: number | null
  direction_name: string | null
}

export interface ManagerFilterOption {
  email: string
  full_name: string
}

export async function getDirections(): Promise<DirectionOption[]> {
  const { data } = await apiClient.get<{ results?: DirectionOption[] } | DirectionOption[]>(
    '/api/directions/',
  )
  if (Array.isArray(data)) {
    return data
  }
  return data.results ?? []
}

export async function searchCompanies(q: string): Promise<CompanyOption[]> {
  return searchCompaniesForSelect(q)
}

export async function getCompaniesFirstPage(): Promise<CompanyOption[]> {
  return searchCompaniesForSelect('')
}

export async function getInternsPage(): Promise<InternOption[]> {
  const { data } = await apiClient.get<{ results?: InternOption[] }>('/api/interns/', {
    params: { page_size: 500 },
  })
  return data.results ?? []
}

export async function searchInterns(q: string): Promise<InternOption[]> {
  const { data } = await apiClient.get<{ results?: InternOption[] }>('/api/interns/', {
    params: { q, page_size: 50 },
  })
  return data.results ?? []
}

export async function getManagersForFilters(): Promise<ManagerFilterOption[]> {
  const { data } = await apiClient.get<ManagerFilterOption[]>('/api/managers/for-filters/')
  return Array.isArray(data) ? data : []
}
