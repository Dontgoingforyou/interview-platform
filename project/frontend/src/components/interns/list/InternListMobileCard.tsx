import { Link } from 'react-router-dom'

import type { InternListItem } from '../../../types/intern'

interface InternListMobileCardProps {
  row: InternListItem
  isAdmin: boolean
  onDelete: (id: number) => void
}

function InternListMobileCard({ row, isAdmin, onDelete }: InternListMobileCardProps) {
  return (
    <article className="intern-mobile-card">
      <header className="intern-mobile-card__head">
        <div className="intern-mobile-card__title">
          <span className="intern-mobile-card__name">{row.full_name}</span>
          <span className="intern-mobile-card__id">#{row.id}</span>
        </div>
      </header>
      <dl className="intern-mobile-card__dl">
        <div>
          <dt>Направление</dt>
          <dd>{row.direction_name ?? '—'}</dd>
        </div>
        <div>
          <dt>Группа</dt>
          <dd>{row.group || '—'}</dd>
        </div>
        <div>
          <dt>Город</dt>
          <dd>{row.city || '—'}</dd>
        </div>
        <div>
          <dt>Менеджер</dt>
          <dd>{row.manager_display_name ?? row.manager_email ?? '—'}</dd>
        </div>
      </dl>
      <footer className="intern-mobile-card__actions">
        {isAdmin ? (
          <Link className="btn-outline-primary btn-small" to={`/interns/${row.id}/edit`}>
            Изменить
          </Link>
        ) : null}
        {isAdmin ? (
          <button
            type="button"
            className="btn-outline-danger btn-small"
            onClick={() => {
              if (window.confirm('Удалить студента? Это действие нельзя отменить.')) {
                onDelete(row.id)
              }
            }}
          >
            Удалить
          </button>
        ) : null}
      </footer>
    </article>
  )
}

export default InternListMobileCard
