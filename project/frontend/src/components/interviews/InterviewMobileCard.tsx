import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'

import { formatShortRuDate } from '../../utils/dateFormat'
import { interviewTypeBadgeClass } from '../../utils/interviews/interviewListUi'
import {
  vacancyCell,
  hrContactsCell,
  callLink,
  interviewRecordingWatchUrl,
} from '../../utils/interviews/interviewCells'
import type { InterviewListItem } from '../../types/interview'

/** Мобильная карточка собеседования в списке. */
export function InterviewMobileCard({
  row,
  canWrite,
  isAdmin,
  onDelete,
  transcriptionSlot = null,
}: {
  row: InterviewListItem
  canWrite: boolean
  isAdmin: boolean
  onDelete: (id: number) => void
  transcriptionSlot?: ReactNode
}) {
  const badgeMod = interviewTypeBadgeClass(row.interview_type)
  const callLinkHref = callLink(row)
  const watchLinkHref = interviewRecordingWatchUrl(row)
  return (
    <article className="interview-mobile-card">
      <header className="interview-mobile-card__head">
        <div className="interview-mobile-card__title">
          <span className="interview-mobile-card__name">{row.intern_name}</span>
          <span className="interview-mobile-card__id">#{row.id}</span>
        </div>
        <span className={`interview-type-badge ${badgeMod}`}>{row.interview_type_display}</span>
      </header>
      <dl className="interview-mobile-card__dl">
        <div>
          <dt>Направление</dt>
          <dd>{row.direction_name ?? '—'}</dd>
        </div>
        <div>
          <dt>Компания</dt>
          <dd>{row.company_name ?? '—'}</dd>
        </div>
        <div>
          <dt>Формат</dt>
          <dd>{row.interview_format_display}</dd>
        </div>
        <div>
          <dt>Дата</dt>
          <dd>{formatShortRuDate(row.date)}</dd>
        </div>
        <div>
          <dt>Время</dt>
          <dd>{row.time ? row.time.slice(0, 5) : '—'}</dd>
        </div>
        <div>
          <dt>Менеджер</dt>
          <dd>{row.manager_display_name ?? row.manager_email ?? '—'}</dd>
        </div>
        <div>
          <dt>HR</dt>
          <dd>{row.hr_name ?? '—'}</dd>
        </div>
        <div>
          <dt>Контакты HR</dt>
          <dd>{hrContactsCell(row.hr_contacts)}</dd>
        </div>
      </dl>
      <div className="interview-mobile-card__links">
        {callLinkHref ? (
          <a href={callLinkHref} target="_blank" rel="noreferrer">
            Созвон
          </a>
        ) : null}
        {watchLinkHref ? (
          <a href={watchLinkHref} target="_blank" rel="noreferrer">
            Запись
          </a>
        ) : null}
        {row.vacancy_link?.trim() ? vacancyCell(row.vacancy_link) : null}
      </div>
      {!canWrite && transcriptionSlot ? (
        <div className="interview-mobile-card__transcription">{transcriptionSlot}</div>
      ) : null}
      {canWrite ? (
        <footer className="interview-mobile-card__actions">
          {transcriptionSlot}
          <Link className="btn-outline-primary btn-small" to={`/interviews/${row.id}/edit`}>
            Изменить
          </Link>
          <Link className="btn-outline-primary btn-small" to={`/interviews/${row.id}/duplicate`}>
            Дублировать
          </Link>
          {isAdmin ? (
            <button
              type="button"
              className="btn-outline-danger btn-small"
              onClick={() => {
                if (window.confirm('Удалить запись? Это действие нельзя отменить.')) {
                  onDelete(row.id)
                }
              }}
            >
              Удалить
            </button>
          ) : null}
        </footer>
      ) : null}
    </article>
  )
}
