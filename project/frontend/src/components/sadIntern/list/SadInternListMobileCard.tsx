import { Link } from 'react-router-dom'

import type { SadInternListItem } from '../../../types/sadIntern'
import { formatRuDate } from '../../../utils/dateFormat'
import { telegramHref } from '../../../utils/debts/debtTableDisplay'

function cardToneClass(status: string | null): string {
  if (status === 'accepted') {
    return ' sad-intern-mobile-card--positive'
  }
  if (status === 'rejected' || status === 'fired') {
    return ' sad-intern-mobile-card--negative'
  }
  return ''
}

interface SadInternListMobileCardProps {
  row: SadInternListItem
  canWrite: boolean
  isAdmin: boolean
  onDelete: (id: number) => void
}

/** Карточка строки списка ожидания (узкий экран). */
function SadInternListMobileCard({ row, canWrite, isAdmin, onDelete }: SadInternListMobileCardProps) {
  const tgUrl = telegramHref(row.telegram_username ?? '')
  return (
    <article className={`sad-intern-mobile-card${cardToneClass(row.status)}`}>
      <header className="sad-intern-mobile-card__head">
        <div className="sad-intern-mobile-card__title">
          <span className="sad-intern-mobile-card__name">{row.intern_name}</span>
          <span className="sad-intern-mobile-card__id">#{row.id}</span>
        </div>
      </header>
      <dl className="sad-intern-mobile-card__dl">
        <div>
          <dt>С нами с</dt>
          <dd>{formatRuDate(row.real_interview_date)}</dd>
        </div>
        <div>
          <dt>Дней с нами</dt>
          <dd>{row.days_waiting}</dd>
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
          <dt>Статус</dt>
          <dd>{row.status_display ?? '—'}</dd>
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

export default SadInternListMobileCard
