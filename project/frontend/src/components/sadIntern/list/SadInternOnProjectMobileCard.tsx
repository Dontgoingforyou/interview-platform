import { Link } from 'react-router-dom'

import type { SadInternListItem } from '../../../types/sadIntern'
import { formatRuDate } from '../../../utils/dateFormat'
import { telegramHref } from '../../../utils/debts/debtTableDisplay'

interface SadInternOnProjectMobileCardProps {
  row: SadInternListItem
  canWrite: boolean
  isAdmin: boolean
  onDelete: (id: number) => void
}

/** Карточка строки блока «Вышли на проект» (узкий экран). */
function SadInternOnProjectMobileCard({
  row,
  canWrite,
  isAdmin,
  onDelete,
}: SadInternOnProjectMobileCardProps) {
  const tgUrl = telegramHref(row.telegram_username ?? '')
  return (
    <article className="sad-intern-mobile-card sad-intern-mobile-card--positive">
      <header className="sad-intern-mobile-card__head">
        <div className="sad-intern-mobile-card__title">
          <span className="sad-intern-mobile-card__name">{row.intern_name}</span>
          <span className="sad-intern-mobile-card__id">#{row.id}</span>
        </div>
      </header>
      <dl className="sad-intern-mobile-card__dl">
        <div>
          <dt>Направление</dt>
          <dd>{row.direction_name ?? '—'}</dd>
        </div>
        <div>
          <dt>С нами с</dt>
          <dd>{formatRuDate(row.real_interview_date)}</dd>
        </div>
        <div>
          <dt>Вышел на проект</dt>
          <dd>{formatRuDate(row.date_added)}</dd>
        </div>
        <div>
          <dt>Telegram</dt>
          <dd>
            {tgUrl ? (
              <a href={tgUrl} target="_blank" rel="noopener noreferrer">
                {row.telegram_username}
              </a>
            ) : (
              (row.telegram_username ?? '—')
            )}
          </dd>
        </div>
        <div>
          <dt>Менеджер</dt>
          <dd>{row.intern_manager_name ?? '—'}</dd>
        </div>
        <div>
          <dt>Примечание</dt>
          <dd>{row.note?.trim() ? row.note : '—'}</dd>
        </div>
      </dl>
      {canWrite ? (
        <footer className="sad-intern-mobile-card__actions">
          <Link className="btn-outline-primary btn-small" to={`/sad-intern/${row.id}/edit`}>
            Изменить
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

export default SadInternOnProjectMobileCard
