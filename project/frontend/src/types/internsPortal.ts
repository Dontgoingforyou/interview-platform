/** Строка списка «Мои собеседования» (API портала студента). */
export interface InternPortalInterviewRow {
  id: number
  intern_full_name: string
  direction_name: string | null
  company_name: string | null
  interview_type_display: string
  date: string | null
  time: string | null
  vacancy_link: string | null
  video_link: string | null
  upload_task_id: string | null
  upload_action_state: 'video' | 'uploading' | 'office' | 'phone' | 'none'
  upload_action_url: string | null
  interview_display: { url: string | null; label: string | null }
  needs_student_video_upload: boolean
}

/** Ответ опроса Celery (как /api/import/status/). */
export interface InternPortalUploadTaskStatus {
  state: string
  status: string
  current: number
  total: number
  result?: unknown
}
