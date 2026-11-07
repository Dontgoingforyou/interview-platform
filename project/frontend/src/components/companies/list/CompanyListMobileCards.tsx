import { Link } from 'react-router-dom'

import type { CompanyListItem } from '../../../types/company'

type Props = {
  rows: CompanyListItem[]
  canWrite: boolean
  isAdmin: boolean
  onDelete: (row: CompanyListItem) => void
  deletingId: number | null
}

/**
 * Карточки списка компаний на узких экранах.
 */
function CompanyListMobileCards({ rows, canWrite, isAdmin, onDelete, deletingId }: Props) {
  return (
    <ul className="company-mobile-cards list-page-mobile-cards">
      {rows.map((row) => (
        <li key={row.id} className="company-mobile-card">
          <div className="company-mobile-card__head">
            <strong>{row.name}</strong>
            {row.is_bigtech ? <span className="status-active company-mobile-card__badge">Бигтех</span> : null}
          </div>
          <dl className="company-mobile-card__dl">
            <div>
              <dt>Собеседований</dt>
              <dd>
                {row.interviews_count > 0 ? (
                  <Link to={`/interviews?company=${row.id}`}>{row.interviews_count}</Link>
                ) : (
                  '0'
                )}
              </dd>
            </div>
            {row.aliases_list.length ? (
              <div>
                <dt>Псевдонимы</dt>
                <dd>{row.aliases_list.join(', ')}</dd>
              </div>
            ) : null}
          </dl>
          {canWrite || isAdmin ? (
            <div className="company-mobile-card__actions">
              {canWrite ? (
                <Link to={`/companies/${row.id}/edit`} className="btn-outline-primary btn-small">
                  Изменить
                </Link>
              ) : null}
              {isAdmin ? (
                <button
                  type="button"
                  className="btn-outline-danger btn-small"
                  disabled={deletingId === row.id}
                  onClick={() => onDelete(row)}
                >
                  Удалить
                </button>
              ) : null}
            </div>
          ) : null}
        </li>
      ))}
    </ul>
  )
}

export default CompanyListMobileCards
