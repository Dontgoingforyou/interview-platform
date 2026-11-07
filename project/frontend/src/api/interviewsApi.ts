import apiClient from './client'
import { normalizePaginatedResponse } from './normalizePaginatedResponse'
import type {
  InterviewAnalytics,
  InterviewListFilters,
  InterviewListItem,
  InterviewTypeBreakdown,
  InterviewWritePayload,
  PaginatedInterviews,
} from '../types/interview'
import { buildInterviewListParams } from '../utils/interviews/interviewListParams'

const BASE = '/api/interviews/'

export const INTERVIEW_LIST_PAGE_SIZE = 30

export async function getInterviewAnalytics(): Promise<InterviewAnalytics> {
  const { data } = await apiClient.get<InterviewAnalytics>('/api/analytics/interviews/')
  return data
}

export async function getInterviewTypeBreakdown(
  filters: InterviewListFilters,
): Promise<InterviewTypeBreakdown> {
  const params = buildInterviewListParams(filters)
  delete params.page
  const { data } = await apiClient.get<InterviewTypeBreakdown>(
    '/api/analytics/interviews/type-breakdown/',
    { params },
  )
  return data
}

export async function getDeepgramBalance(): Promise<{ amount?: number | null; error?: string }> {
  const { data } = await apiClient.get('/api/transcriptions/deepgram-balance/')
  return data as { amount?: number | null; error?: string }
}

export async function getInterviews(filters: InterviewListFilters): Promise<PaginatedInterviews> {
  const params = {
    ...buildInterviewListParams(filters),
    page_size: INTERVIEW_LIST_PAGE_SIZE,
  }
  const { data } = await apiClient.get<PaginatedInterviews | InterviewListItem[]>(BASE, {
    params,
  })
  return normalizePaginatedResponse(data)
}

export async function getInterview(id: number): Promise<InterviewListItem> {
  const { data } = await apiClient.get<InterviewListItem>(`${BASE}${id}/`)
  return data
}

export async function createInterview(payload: InterviewWritePayload): Promise<InterviewListItem> {
  const { data } = await apiClient.post<InterviewListItem>(BASE, payload)
  return data
}

export async function updateInterview(
  id: number,
  payload: Partial<InterviewWritePayload>,
): Promise<InterviewListItem> {
  const { data } = await apiClient.patch<InterviewListItem>(`${BASE}${id}/`, payload)
  return data
}

export async function deleteInterview(id: number): Promise<void> {
  await apiClient.delete(`${BASE}${id}/`)
}

export async function postTranscribe(interviewId: number): Promise<{ status?: string; message?: string; error?: string }> {
  const { data } = await apiClient.post(`/api/interviews/${interviewId}/transcribe/`)
  return data
}

export async function getTranscriptionStatus(interviewId: number): Promise<{
  status: string
  error_message?: string
}> {
  const { data } = await apiClient.get(`/api/interviews/${interviewId}/transcription-status/`)
  return data
}

export async function getTranscriptionText(interviewId: number): Promise<{
  text?: string
  error?: string
  filename?: string
}> {
  const { data } = await apiClient.get(`/api/interviews/${interviewId}/transcription-text/`)
  return data
}

export async function postInterviewImport(file: File): Promise<{ status: string; task_id: string }> {
  const body = new FormData()
  body.append('file', file)
  const { data } = await apiClient.post<{ status: string; task_id: string }>(
    '/api/interviews/import/',
    body,
  )
  return data
}
