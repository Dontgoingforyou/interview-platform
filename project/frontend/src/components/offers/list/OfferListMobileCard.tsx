import { Link } from 'react-router-dom'

import type { OfferListItem } from '../../../types/offer'
import { formatOfferAmountCell, offerTelegramHref } from '../../../utils/offers/offerListDisplay'

interface OfferListMobileCardProps {
  row: OfferListItem
  isAdmin: boolean
  onDelete: (id: number) => void
}

function OfferListMobileCard({ row, isAdmin, onDelete }: OfferListMobileCardProps) {
  const tgUrl = offerTelegramHref(row.intern_telegram_username)
  const tgLabel = row.intern_telegram_username?.trim() || '—'

  return (
    <article className="offer-mobile-card">
      <header className="offer-mobile-card__head">
        <div className="offer-mobile-card__title">
          <span className="offer-mobile-card__name">{row.intern_name}</span>
          <span className="offer-mobile-card__id">#{row.id}</span>
        </div>
      </header>
      <dl className="offer-mobile-card__dl">
        <div>
          <dt>Направление</dt>
          <dd>{row.direction_name ?? '—'}</dd>
        </div>
        <div>
          <dt>Компания</dt>
          <dd>{row.company?.trim() ? row.company : '—'}</dd>
        </div>
        <div>
          <dt>Сумма</dt>
          <dd>{formatOfferAmountCell(row.amount)}</dd>
        </div>
        <div>
          <dt>Телеграм</dt>
          <dd>
            {tgUrl ? (
              <a href={tgUrl} target="_blank" rel="noreferrer">
                {tgLabel}
              </a>
            ) : (
              '—'
            )}
          </dd>
        </div>
      </dl>
      {isAdmin ? (
        <footer className="offer-mobile-card__actions">
          <Link className="btn-outline-primary btn-small" to={`/offers/${row.id}/edit`}>
            Изменить
          </Link>
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
        </footer>
      ) : null}
    </article>
  )
}

export default OfferListMobileCard
