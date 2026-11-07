import apiClient from './client'
import { normalizePaginatedResponse } from './normalizePaginatedResponse'
import type {
  InterviewListItem,
  InterviewsDatabaseListFilters,
  PaginatedInterviews,
} from '../types/interview'
import { buildInterviewsDatabaseListParams } from '../utils/interviewsDatabase/interviewsDatabaseListParams'

const BASE = '/api/interviews-database/'

export const INTERVIEWS_DATABASE_PAGE_SIZE = 20

export async function getInterviewsDatabaseList(
  filters: InterviewsDatabaseListFilters,
): Promise<PaginatedInterviews> {
  const params = buildInterviewsDatabaseListParams(filters)
  const { data } = await apiClient.get<PaginatedInterviews | InterviewListItem[]>(BASE, {
    params,
  })
  return normalizePaginatedResponse(data)
}
