import type { InterviewsDatabaseTranscriptionFilterValue } from '../constants/interviewsDatabaseTranscriptionFilter'
import type { OrderDir, Paginated } from './common'

/** Ответ GET `/api/analytics/interviews/` — сводная аналитика по собеседованиям. */
export interface InterviewAnalytics {
  total: number
  companies: number
  upcoming: number
  'this-week': number
  'last-week': number
  success_rate: number
  cancelled: number
  fastest_manager: string
  fastest_manager_count: number
  avg_per_person: number
  avg_per_manager: number
  total_all_time: number
  companies_all_time: number
  upcoming_all_time: number
  this_week_all_time: number
  last_week_all_time: number
  success_rate_all_time: number
  cancelled_all_time: number
  top_manager_all_time: string
  top_manager_count_all_time: number
  avg_per_person_all_time: number
  avg_per_manager_all_time: number
  tooltips: Record<string, string>
}

/** Элемент списка GET /api/interviews/ (InterviewFullSerializer) */
export interface InterviewListItem {
  id: number
  intern: number
  intern_name: string
  direction_id: number | null
  direction_name: string | null
  company_id: number | null
  company_name: string | null
  manager_email: string | null
  manager_display_name: string | null
  interview_type: string
  interview_type_display: string
  interview_format: string
  interview_format_display: string
  date: string | null
  time: string | null
  link: string | null
  vacancy_link: string | null
  interview_link: string | null
  video_link: string | null
  upload_task_id?: string | null
  has_video?: boolean
  transcription_media_url: string | null
  transcription_status: string
  transcription_error_message: string
  hr_name: string | null
  hr_contacts: string | null
  created_at: string
  updated_at: string
}

export type PaginatedInterviews = Paginated<InterviewListItem>

/** Параметры фильтрации списка (имена полей = query API). */
/** Параметры списка «База собеседований» (GET `/api/interviews-database/`). */
export interface InterviewsDatabaseListFilters {
  page?: number
  q?: string
  company?: number
  direction_id?: number
  interview_type?: string
  transcription?: InterviewsDatabaseTranscriptionFilterValue
  order_by?: string
  order_dir?: OrderDir
}

export interface InterviewListFilters {
  page?: number
  date_from?: string
  date_to?: string
  date_filter?: string
  interview_type?: string
  direction_id?: number
  q?: string
  manager?: string
  company?: number
  interview_format?: string
  has_video?: string
  order_by?: string
  order_dir?: OrderDir
}

export interface InterviewTypeBreakdownItem {
  type: string
  label: string
  count: number
}

export interface InterviewTypeBreakdown {
  total: number
  items: InterviewTypeBreakdownItem[]
}

/** Тело POST/PATCH собеседования (InterviewCreateUpdateSerializer) */
export interface InterviewWritePayload {
  intern: number
  direction_id: number
  company_id?: number | null
  /** Новая компания по имени (если нет в списке); бэкенд — get_or_create. */
  company_name?: string | null
  manager_email?: string | null
  interview_type: string
  interview_format: string
  date?: string | null
  time?: string | null
  link?: string | null
  vacancy_link?: string | null
  interview_link?: string | null
  hr_name?: string | null
  hr_contacts?: string | null
}

export type TranscriptionStatusResponse = {
  status: string
  error_message?: string
}

export type TranscriptionTextResponse = {
  text?: string
  error?: string
}
