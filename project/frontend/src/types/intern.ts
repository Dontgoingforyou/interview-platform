import type { OrderDir, Paginated } from './common'

export interface InternListItem {
  id: number
  full_name: string
  email: string | null
  telegram_username: string | null
  direction_id: number
  direction_name: string | null
  group: string
  city: string | null
  type_of_training: string
  type_of_training_display: string | null
  status: string
  status_display: string
  manual_status: string | null
  manager_email: string | null
  manager_display_name: string | null
  date_of_receipt: string | null
  date_of_birth: string | null
  hiring_hr: string
  responsible_hr: string
  real_interview_date: string | null
  cv: string | null
  legend: string | null
}

export interface InternListFilters {
  page?: number
  q?: string
  status?: string
  manager?: string
  direction_id?: number | null
  group?: string
  order_by?: string
  order_dir?: OrderDir
}

export interface InternDetail extends InternListItem {
  hr_feedback: string | null
  mentor_feedback: string | null
}

export type PaginatedInterns = Paginated<InternListItem>

/** Тело создания/обновления (InternCreateUpdateSerializer). */
export interface InternWritePayload {
  full_name: string
  email?: string | null
  telegram_username?: string | null
  direction_id: number
  city?: string | null
  cv?: string | null
  date_of_receipt?: string | null
  date_of_birth?: string | null
  hiring_hr: string
  responsible_hr: string
  group: string
  type_of_training: string
  legend?: string | null
  hr_feedback?: string | null
  mentor_feedback?: string | null
  real_interview_date?: string | null
  manual_status?: string | null
  manager_email?: string | null
}
