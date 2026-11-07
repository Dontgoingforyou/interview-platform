import type { ReactNode } from 'react'

import type { InterviewListItem } from '../../types/interview'
import { isYandexDiskPublicFileUrl } from '../yandexDiskUrl'

/** Ссылка на созвон: только поле link (без interview_link). */
export function callLink(row: InterviewListItem): string | null {
  const t = row.link?.trim()
  return t || null
}

/** Ссылка на запись собеседования: только video_link (каноническое поле). */
export function watchInterviewLink(row: InterviewListItem): string | null {
  const t = row.video_link?.trim()
  return t || null
}

/**
 * URL для кнопки «Смотреть запись»: video_link; иначе публичный Я.Диск в link / interview_link.
 * URL записи с API (transcription_media_url / video_link; S3 — presigned на бэкенде).
 */
export function interviewRecordingWatchUrl(row: InterviewListItem): string | null {
  const fromApi = row.transcription_media_url?.trim()
  if (fromApi) {
    return fromApi
  }
  const v = row.video_link?.trim()
  if (v) {
    return v
  }
  const l = row.link?.trim()
  if (l && isYandexDiskPublicFileUrl(l)) {
    return l
  }
  const il = row.interview_link?.trim()
  if (il && isYandexDiskPublicFileUrl(il)) {
    return il
  }
  return null
}

/** Колонка «Запись созвона» в базе: video_link или Я.Диск в link/interview_link; иначе загрузка / тире. */
export function databaseRecordingCell(row: InterviewListItem): ReactNode {
  const video = interviewRecordingWatchUrl(row)
  if (video) {
    return (
      <a href={video} target="_blank" rel="noreferrer" className="btn-outline-primary btn-small">
        Смотреть запись
      </a>
    )
  }
  if (row.upload_task_id?.trim()) {
    return <span style={{ color: 'var(--text-muted)' }}>Загрузка…</span>
  }
  return '—'
}

/** Ячейка ссылки на вакансию: URL → ссылка «Вакансия», текст → обрезанный span. */
export function vacancyCell(link: string | null): ReactNode {
  const raw = link?.trim()
  if (!raw) {
    return '—'
  }
  if (raw.startsWith('http://') || raw.startsWith('https://')) {
    return (
      <a href={raw} target="_blank" rel="noreferrer">
        Вакансия
      </a>
    )
  }
  const short = raw.length > 10 ? `${raw.slice(0, 10)}…` : raw
  return <span title={raw}>{short}</span>
}

/** Ячейка контактов HR: @username → ссылка t.me, URL → ссылка, текст → текст. */
export function hrContactsCell(contacts: string | null): ReactNode {
  const raw = contacts?.trim()
  if (!raw) {
    return '—'
  }
  let href: string | null = null
  if (raw.startsWith('@')) {
    href = `https://t.me/${raw.slice(1)}`
  } else if (raw.startsWith('http://') || raw.startsWith('https://')) {
    href = raw
  }
  if (href) {
    return (
      <a href={href} target="_blank" rel="noreferrer">
        {raw}
      </a>
    )
  }
  return raw
}
