import type { ReactNode } from 'react'

import { databaseRecordingCell, hrContactsCell, vacancyCell } from '../../../utils/interviews/interviewCells'
import { formatShortRuDate } from '../../../utils/dateFormat'
import { interviewTypeBadgeClass } from '../../../utils/interviews/interviewListUi'
import {
  mayAccessInterviewTranscription,
  showTranscriptionControls,
} from '../../../utils/interviews/interviewTranscription'
import type { AuthUser } from '../../../store/authStore'
import type { InterviewListItem } from '../../../types/interview'

interface InterviewsDatabaseMobileCardsProps {
  results: InterviewListItem[]
  user: AuthUser | null
  showTranscriptionColumn: boolean
  renderTranscriptionCell: (row: InterviewListItem) => ReactNode
}

function InterviewsDatabaseMobileCards({
  results,
  user,
  showTranscriptionColumn,
  renderTranscriptionCell,
}: InterviewsDatabaseMobileCardsProps) {
  return (
    <div className="interviews-mobile-cards" aria-label="База собеседований (компактный вид)">
      {results.map((row) => {
        const recording = databaseRecordingCell(row)
        const showTxBelow =
          !showTranscriptionColumn &&
          showTranscriptionControls(row) &&
          mayAccessInterviewTranscription(user, row)
        const txSlot = renderTranscriptionCell(row)

        return (
          <article key={row.id} className="interview-mobile-card">
            <header className="interview-mobile-card__head">
              <div className="interview-mobile-card__title">
                <span className="interview-mobile-card__name">{row.intern_name}</span>
                <span className="interview-mobile-card__id">#{row.id}</span>
              </div>
              <span className={`interview-type-badge ${interviewTypeBadgeClass(row.interview_type)}`}>
                {row.interview_type_display}
              </span>
            </header>
            <dl className="interview-mobile-card__dl">
              <div>
                <dt>Компания</dt>
                <dd>{row.company_name ?? '—'}</dd>
              </div>
              <div>
                <dt>Направление</dt>
                <dd>{row.direction_name ?? '—'}</dd>
              </div>
              <div>
                <dt>Дата</dt>
                <dd>{formatShortRuDate(row.date)}</dd>
              </div>
              <div>
                <dt>HR</dt>
                <dd>{row.hr_name ?? '—'}</dd>
              </div>
              <div className="interview-mobile-card__full">
                <dt>Контакты HR</dt>
                <dd>{hrContactsCell(row.hr_contacts)}</dd>
              </div>
              <div className="interview-mobile-card__full">
                <dt>Запись</dt>
                <dd>
                  <div className="interview-mobile-card__links interviews-database-recording-cell">
                    {recording}
                    {showTxBelow && txSlot ? (
                      <span className="interview-table-actions interview-table-actions--compact">{txSlot}</span>
                    ) : null}
                  </div>
                </dd>
              </div>
              <div className="interview-mobile-card__full">
                <dt>Вакансия</dt>
                <dd>{vacancyCell(row.vacancy_link)}</dd>
              </div>
              {showTranscriptionColumn ? (
                <div className="interview-mobile-card__full">
                  <dt>Транскрибация</dt>
                  <dd>
                    {showTranscriptionControls(row) && mayAccessInterviewTranscription(user, row) ? (
                      <span className="interview-table-actions interview-table-actions--compact">{txSlot}</span>
                    ) : (
                      '—'
                    )}
                  </dd>
                </div>
              ) : null}
            </dl>
          </article>
        )
      })}
    </div>
  )
}

export default InterviewsDatabaseMobileCards
