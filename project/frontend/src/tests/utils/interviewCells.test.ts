import { describe, expect, it } from 'vitest'

import {
  callLink,
  databaseRecordingCell,
  interviewRecordingWatchUrl,
  watchInterviewLink,
} from '../../utils/interviews/interviewCells'
import type { InterviewListItem } from '../../types/interview'

function row(partial: Partial<InterviewListItem>): InterviewListItem {
  return {
    id: 1,
    intern: 1,
    intern_name: 'Тест',
    direction_id: null,
    direction_name: null,
    company_id: null,
    company_name: null,
    manager_email: null,
    manager_display_name: null,
    interview_type: 'screening',
    interview_type_display: '',
    interview_format: 'online',
    interview_format_display: '',
    date: null,
    time: null,
    link: null,
    vacancy_link: null,
    interview_link: null,
    video_link: null,
    transcription_media_url: null,
    transcription_status: '',
    transcription_error_message: '',
    hr_name: null,
    hr_contacts: null,
    created_at: '',
    updated_at: '',
    ...partial,
  }
}

describe('callLink', () => {
  it('берёт только link, игнорируя interview_link', () => {
    expect(
      callLink(
        row({
          link: 'https://meet.example/x',
          interview_link: 'https://other.example/y',
        }),
      ),
    ).toBe('https://meet.example/x')
  })

  it('возвращает null без link даже при заполненном interview_link', () => {
    expect(callLink(row({ interview_link: 'https://other.example/y' }))).toBeNull()
  })
})

describe('watchInterviewLink', () => {
  it('берёт только video_link, не подставляет link', () => {
    expect(
      watchInterviewLink(
        row({
          video_link: 'https://disk.yandex.ru/i/v',
          link: 'https://meet.example/x',
        }),
      ),
    ).toBe('https://disk.yandex.ru/i/v')
  })

  it('возвращает null без video_link даже при link', () => {
    expect(watchInterviewLink(row({ link: 'https://meet.example/x' }))).toBeNull()
  })
})

describe('interviewRecordingWatchUrl', () => {
  it('приоритет video_link над Я.Диском в link', () => {
    expect(
      interviewRecordingWatchUrl(
        row({
          video_link: 'https://disk.yandex.ru/i/v',
          link: 'https://disk.yandex.ru/i/from-link',
        }),
      ),
    ).toBe('https://disk.yandex.ru/i/v')
  })

  it('берёт публичный Я.Диск из link без video_link', () => {
    expect(
      interviewRecordingWatchUrl(
        row({ link: 'https://disk.yandex.ru/i/only-link', video_link: null }),
      ),
    ).toBe('https://disk.yandex.ru/i/only-link')
  })

  it('не подставляет обычный URL созвона', () => {
    expect(interviewRecordingWatchUrl(row({ link: 'https://meet.example/x' }))).toBeNull()
  })

  it('берёт Я.Диск из interview_link', () => {
    expect(
      interviewRecordingWatchUrl(
        row({
          link: 'https://zoom.us/j/1',
          interview_link: 'https://yadi.sk/i/il',
        }),
      ),
    ).toBe('https://yadi.sk/i/il')
  })

  it('приоритет transcription_media_url с API над полями link/interview_link', () => {
    expect(
      interviewRecordingWatchUrl(
        row({
          transcription_media_url: 'https://disk.yandex.ru/i/from-api',
          video_link: null,
          link: 'https://disk.yandex.ru/i/from-link',
          interview_link: 'https://yadi.sk/i/other',
        }),
      ),
    ).toBe('https://disk.yandex.ru/i/from-api')
  })
})

describe('databaseRecordingCell', () => {
  it('тире при link на созвон без video_link', () => {
    expect(databaseRecordingCell(row({ link: 'https://meet.example/x' }))).toBe('—')
  })

  it('кнопка при Я.Диске только в link', () => {
    const el = databaseRecordingCell(row({ link: 'https://disk.yandex.ru/i/x', video_link: null }))
    expect(el).toBeTypeOf('object')
  })

  it('кнопка по video_link', () => {
    const el = databaseRecordingCell(
      row({ video_link: 'https://disk.yandex.ru/i/v', link: 'https://meet.example/x' }),
    )
    expect(el).toBeTypeOf('object')
  })

  it('Загрузка при upload_task_id без video_link', () => {
    const el = databaseRecordingCell(row({ upload_task_id: 't1', link: 'https://x.com' }))
    expect(el).toBeTypeOf('object')
  })
})
