import { describe, expect, it } from 'vitest'

import type { AuthUser } from '../../store/authStore'
import type { InterviewListItem } from '../../types/interview'
import {
  KEYCLOAK_GROUP_EMPLOYMENT,
  KEYCLOAK_GROUP_HR,
} from '../../constants/keycloakGroups'
import {
  mayAccessInterviewTranscription,
  showTranscriptionControls,
} from '../../utils/interviews/interviewTranscription'

function baseRow(over: Partial<InterviewListItem> = {}): InterviewListItem {
  return {
    id: 1,
    intern: 10,
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
    ...over,
  }
}

function authUser(over: Partial<AuthUser> = {}): AuthUser {
  return {
    email: 'm@example.com',
    username: 'm',
    full_name: 'М',
    manager_role: 'manager',
    groups: [KEYCLOAK_GROUP_EMPLOYMENT],
    ...over,
  }
}

describe('showTranscriptionControls', () => {
  it('true при непустом transcription_media_url с API (как на бэкенде), статус none', () => {
    expect(
      showTranscriptionControls(
        baseRow({ transcription_media_url: 'https://disk.yandex.ru/i/x', transcription_status: 'none' }),
      ),
    ).toBe(true)
  })

  it('true при непустом video_link', () => {
    expect(
      showTranscriptionControls(
        baseRow({
          video_link: 'https://disk.yandex.ru/i/x',
          transcription_status: 'none',
          transcription_media_url: null,
        }),
      ),
    ).toBe(true)
  })

  it('true при публичном Я.Диске в link без video_link', () => {
    expect(
      showTranscriptionControls(
        baseRow({
          link: 'https://disk.yandex.ru/i/x',
          video_link: null,
          transcription_status: 'none',
          transcription_media_url: null,
        }),
      ),
    ).toBe(true)
  })

  it('true при статусе не none даже без video_link', () => {
    expect(showTranscriptionControls(baseRow({ transcription_status: 'pending' }))).toBe(true)
  })

  it('false без источника медиа и статуса none', () => {
    expect(showTranscriptionControls(baseRow())).toBe(false)
  })
})

describe('mayAccessInterviewTranscription', () => {
  it('admin — всегда true', () => {
    expect(
      mayAccessInterviewTranscription(authUser({ manager_role: 'admin' }), baseRow({ id: 99 })),
    ).toBe(true)
  })

  it('HR — true', () => {
    expect(
      mayAccessInterviewTranscription(
        authUser({ manager_role: 'hr', groups: [KEYCLOAK_GROUP_HR] }),
        baseRow({ manager_email: 'other@example.com' }),
      ),
    ).toBe(true)
  })

  it('mentor — true для любого собеседования (read-only)', () => {
    expect(
      mayAccessInterviewTranscription(
        authUser({ manager_role: 'mentor', groups: ['mentors'], email: 'mentor@example.com' }),
        baseRow({ manager_email: 'other@example.com' }),
      ),
    ).toBe(true)
  })

  it('менеджер — только своё по manager_email', () => {
    expect(mayAccessInterviewTranscription(authUser({ email: 'm@example.com' }), baseRow())).toBe(
      true,
    )
    expect(
      mayAccessInterviewTranscription(authUser({ email: 'm@example.com' }), baseRow({ manager_email: 'x@y.ru' })),
    ).toBe(false)
  })
})
