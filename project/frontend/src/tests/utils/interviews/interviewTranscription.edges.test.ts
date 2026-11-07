import { describe, expect, it } from 'vitest'

import type { AuthUser } from '../../../store/authStore'
import type { InterviewListItem } from '../../../types/interview'
import { KEYCLOAK_GROUP_EMPLOYMENT } from '../../../constants/keycloakGroups'
import { mayAccessInterviewTranscription } from '../../../utils/interviews/interviewTranscription'

function authUser(partial: Partial<AuthUser> = {}): AuthUser {
  return {
    email: 'm@example.com',
    username: 'm',
    full_name: 'M',
    manager_role: 'manager',
    groups: [KEYCLOAK_GROUP_EMPLOYMENT],
    ...partial,
  }
}

function row(partial: Partial<InterviewListItem> = {}): InterviewListItem {
  return {
    id: 1,
    intern: 1,
    intern_name: 'Иван',
    direction_id: 1,
    direction_name: 'Java',
    company_id: null,
    company_name: null,
    manager_email: 'm@example.com',
    manager_display_name: null,
    interview_type: 'screening',
    interview_type_display: 'Скрининг',
    interview_format: 'online',
    interview_format_display: 'Онлайн',
    date: '2025-12-01',
    time: '10:00:00',
    link: null,
    vacancy_link: null,
    interview_link: null,
    video_link: null,
    transcription_media_url: null,
    transcription_status: 'none',
    transcription_error_message: '',
    hr_name: null,
    hr_contacts: null,
    created_at: '',
    updated_at: '',
    ...partial,
  }
}

describe('mayAccessInterviewTranscription edges', () => {
  it('null user / student / без manager group / без email', () => {
    expect(mayAccessInterviewTranscription(null, row())).toBe(false)
    expect(mayAccessInterviewTranscription(authUser({ manager_role: 'student', groups: [] }), row())).toBe(
      false,
    )
    expect(mayAccessInterviewTranscription(authUser({ manager_role: 'no_access', groups: [] }), row())).toBe(
      false,
    )
    expect(
      mayAccessInterviewTranscription(authUser({ manager_role: 'manager', groups: [] }), row()),
    ).toBe(false)
    expect(
      mayAccessInterviewTranscription(
        authUser({ manager_role: 'manager', groups: [KEYCLOAK_GROUP_EMPLOYMENT], email: '' }),
        row(),
      ),
    ).toBe(false)
  })
})
