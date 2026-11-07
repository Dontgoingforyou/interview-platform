/**
 * Минимальные данные для тестов страницы списка собеседований (без запросов к API).
 */
import type { InterviewAnalytics, InterviewListItem } from '../../types/interview'

export function minimalInterviewAnalytics(): InterviewAnalytics {
  return {
    total: 0,
    companies: 0,
    upcoming: 0,
    'this-week': 0,
    'last-week': 0,
    success_rate: 0,
    cancelled: 0,
    fastest_manager: '—',
    fastest_manager_count: 0,
    avg_per_person: 0,
    avg_per_manager: 0,
    total_all_time: 0,
    companies_all_time: 0,
    upcoming_all_time: 0,
    this_week_all_time: 0,
    last_week_all_time: 0,
    success_rate_all_time: 0,
    cancelled_all_time: 0,
    top_manager_all_time: '—',
    top_manager_count_all_time: 0,
    avg_per_person_all_time: 0,
    avg_per_manager_all_time: 0,
    tooltips: {},
  }
}

export function sampleInterviewListItem(overrides: Partial<InterviewListItem> = {}): InterviewListItem {
  return {
    id: 1,
    intern: 10,
    intern_name: 'Кандидат Тестовый',
    direction_id: 1,
    direction_name: 'Java',
    company_id: null,
    company_name: null,
    manager_email: 'mgr@test',
    manager_display_name: 'Менеджер',
    interview_type: 'tech',
    interview_type_display: 'Техническое',
    interview_format: 'online',
    interview_format_display: 'Онлайн',
    date: '2025-06-01',
    time: '10:00',
    link: null,
    vacancy_link: null,
    interview_link: null,
    video_link: null,
    transcription_media_url: null,
    transcription_status: 'none',
    transcription_error_message: '',
    hr_name: null,
    hr_contacts: null,
    created_at: '2025-06-01T08:00:00Z',
    updated_at: '2025-06-01T08:00:00Z',
    ...overrides,
  }
}
