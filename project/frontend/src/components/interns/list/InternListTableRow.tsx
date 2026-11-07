import { Link } from 'react-router-dom'

import { formatRuDate } from '../../../utils/dateFormat'
import { internTelegramHref } from '../../../utils/interns/internTelegram'
import type { InternListItem } from '../../../types/intern'

interface InternListTableRowProps {
  row: InternListItem
  isAdmin: boolean
  onDelete: (id: number) => void
}

function InternListTableRow({ row, isAdmin, onDelete }: InternListTableRowProps) {
  const tg = internTelegramHref(row.telegram_username)
  return (
    <tr>
      <td>{row.id}</td>
      <td>{row.full_name}</td>
      <td>{row.direction_name ?? '—'}</td>
      <td>{row.group || '—'}</td>
      <td>{row.city || '—'}</td>
      <td>{row.type_of_training_display ?? row.type_of_training ?? '—'}</td>
      <td>{formatRuDate(row.date_of_receipt)}</td>
      <td>{formatRuDate(row.date_of_birth)}</td>
      <td>{row.hiring_hr || '—'}</td>
      <td>{row.responsible_hr || '—'}</td>
      <td>{formatRuDate(row.real_interview_date)}</td>
      <td>{row.manager_display_name ?? row.manager_email ?? '—'}</td>
      <td className="interns-table-link-cell">
        {tg ? (
          <a href={tg} target="_blank" rel="noreferrer">
            @{row.telegram_username?.replace(/^@/, '')}
          </a>
        ) : (
          '—'
        )}
      </td>
      <td className="interns-table-link-cell">
        {row.email ? <a href={`mailto:${row.email}`}>{row.email}</a> : '—'}
      </td>
      <td className="interns-table-link-cell">
        {row.cv ? (
          <a href={row.cv} target="_blank" rel="noreferrer">
            Резюме
          </a>
        ) : (
          '—'
        )}
      </td>
      <td className="interns-table-link-cell">
        {row.legend ? (
          <a href={row.legend} target="_blank" rel="noreferrer">
            Легенда
          </a>
        ) : (
          '—'
        )}
      </td>
      <td className="action-buttons interviews-col-actions interns-col-actions">
        {isAdmin ? (
          <span className="interview-table-actions interview-table-actions--compact">
            <Link
              to={`/interns/${row.id}/edit`}
              className="btn-outline-primary btn-small interviews-action-emoji"
              title="Редактировать"
              aria-label="Редактировать"
            >
              ✏️
            </Link>
            <button
              type="button"
              className="btn-outline-danger btn-small interviews-action-emoji"
              title="Удалить"
              aria-label="Удалить"
              onClick={() => {
                if (window.confirm('Удалить студента? Это действие нельзя отменить.')) {
                  onDelete(row.id)
                }
              }}
            >
              🗑️
            </button>
          </span>
        ) : null}
      </td>
    </tr>
  )
}

export default InternListTableRow
