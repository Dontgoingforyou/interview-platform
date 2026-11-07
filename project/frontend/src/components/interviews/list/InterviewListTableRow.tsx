import { Link } from 'react-router-dom'
import type { ReactNode } from 'react'

import {
  callLink,
  hrContactsCell,
  interviewRecordingWatchUrl,
  vacancyCell,
} from '../../../utils/interviews/interviewCells'
import { formatShortRuDate } from '../../../utils/dateFormat'
import { interviewTypeBadgeClass } from '../../../utils/interviews/interviewListUi'
import {
  mayAccessInterviewTranscription,
  showTranscriptionControls,
} from '../../../utils/interviews/interviewTranscription'
import type { AuthUser } from '../../../store/authStore'
import type { InterviewListItem } from '../../../types/interview'

interface InterviewListTableRowProps {
  row: InterviewListItem
  user: AuthUser | null
  canWrite: boolean
  isAdmin: boolean
  showReadonlyTranscriptionColumn: boolean
  renderTranscriptionCell: (row: InterviewListItem) => ReactNode
  onRequestDelete: (id: number) => void
}

const formatInterviewListDate = formatShortRuDate

function InterviewListTableRow({
  row,
  user,
  canWrite,
  isAdmin,
  showReadonlyTranscriptionColumn,
  renderTranscriptionCell,
  onRequestDelete,
}: InterviewListTableRowProps) {
  const call = callLink(row)

  return (
    <tr>
      <td>{row.id}</td>
      <td>{row.intern_name}</td>
      <td>{row.direction_name ?? '—'}</td>
      <td>{row.company_name ?? '—'}</td>
      <td>
        <span className={`interview-type-badge ${interviewTypeBadgeClass(row.interview_type)}`}>
          {row.interview_type_display}
        </span>
      </td>
      <td>{row.interview_format_display}</td>
      <td>{formatInterviewListDate(row.date)}</td>
      <td>{row.time ? row.time.slice(0, 5) : '—'}</td>
      <td>{row.manager_display_name ?? row.manager_email ?? '—'}</td>
      <td title={row.hr_name ?? ''}>{row.hr_name ?? '—'}</td>
      <td className="data-table-link-cell" title={row.hr_contacts ?? ''}>
        {hrContactsCell(row.hr_contacts)}
      </td>
      <td className="data-table-link-cell">
        {call ? (
          <a href={call} target="_blank" rel="noreferrer">
            Ссылка
          </a>
        ) : (
          '—'
        )}
      </td>
      <td className="data-table-link-cell">{vacancyCell(row.vacancy_link)}</td>
      <td className="data-table-link-cell">
        {(() => {
          const link = interviewRecordingWatchUrl(row)
          return link ? (
            <a href={link} target="_blank" rel="noreferrer">
              Смотреть запись
            </a>
          ) : (
            '—'
          )
        })()}
      </td>
      {canWrite ? (
        <td className="interviews-col-actions action-buttons">
          <span className={`interview-table-actions${isAdmin ? ' interview-table-actions--compact' : ''}`}>
            <Link
              className="btn-outline-primary btn-small interviews-action-emoji"
              title="Редактировать"
              aria-label="Редактировать"
              to={`/interviews/${row.id}/edit`}
            >
              ✏️
            </Link>
            <Link
              className="btn-outline-primary btn-small interviews-action-emoji"
              title="Дублировать"
              aria-label="Дублировать"
              to={`/interviews/${row.id}/duplicate`}
            >
              📋
            </Link>
            {renderTranscriptionCell(row)}
            {isAdmin ? (
              <button
                type="button"
                className="btn-outline-danger btn-small interviews-action-emoji"
                title="Удалить"
                aria-label="Удалить"
                onClick={() => {
                  if (window.confirm('Удалить запись? Это действие нельзя отменить.')) {
                    onRequestDelete(row.id)
                  }
                }}
              >
                🗑️
              </button>
            ) : null}
          </span>
        </td>
      ) : null}
      {showReadonlyTranscriptionColumn ? (
        <td className="action-buttons interview-table-actions">
          {showTranscriptionControls(row) && mayAccessInterviewTranscription(user, row)
            ? renderTranscriptionCell(row)
            : '—'}
        </td>
      ) : null}
    </tr>
  )
}

export default InterviewListTableRow
