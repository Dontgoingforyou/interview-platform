import { Link } from 'react-router-dom'

import type { DebtListItem } from '../../../types/debt'
import {
  balanceCellClass,
  debtRowClassName,
  formatActDate,
  formatPaymentStatusLabel,
  paymentStatusCellClass,
  telegramHref,
} from '../../../utils/debts/debtTableDisplay'

interface DebtListMobileCardsProps {
  results: DebtListItem[]
  lastFourMonthLabels: string[]
  isAdmin: boolean
  onDeleteDebt: (id: number) => void
}

function DebtListMobileCards({
  results,
  lastFourMonthLabels,
  isAdmin,
  onDeleteDebt,
}: DebtListMobileCardsProps) {
  return (
    <div className="debts-mobile-cards" aria-label="Список долгов (компактный вид)">
      {results.map((row) => {
        const tgUrl = telegramHref(row.display_telegram)
        const lastPay =
          row.last_payment_month != null && row.last_payment_year != null
            ? `${row.last_payment_month}/${row.last_payment_year}`
            : '—'
        return (
          <article
            key={row.id}
            className={`debt-mobile-card debts-mobile-card ${debtRowClassName(row)}`.trim()}
          >
            <header className="debt-mobile-card__head">
              <div className="debt-mobile-card__title">
                <span className="debt-mobile-card__name">{row.intern_name}</span>
                <span className="debt-mobile-card__id">#{row.id}</span>
              </div>
            </header>
            <dl className="debt-mobile-card__dl">
              <div>
                <dt>Направление</dt>
                <dd>{row.direction_name ?? '—'}</dd>
              </div>
              <div>
                <dt>Email</dt>
                <dd>{row.display_email?.trim() ? row.display_email : '—'}</dd>
              </div>
              <div>
                <dt>Общая сумма</dt>
                <dd>{row.total_amount}</dd>
              </div>
              <div>
                <dt>Уже заплатил</dt>
                <dd>{row.paid_amount}</dd>
              </div>
              <div>
                <dt>Остаток</dt>
                <dd>
                  <span className={balanceCellClass(row.balance)}>{row.balance}</span>
                </dd>
              </div>
              <div>
                <dt>Дата акта</dt>
                <dd>{formatActDate(row.act_date)}</dd>
              </div>
              <div>
                <dt>Последний платёж</dt>
                <dd>{lastPay}</dd>
              </div>
              {lastFourMonthLabels.map((label) => (
                <div key={label}>
                  <dt>{label}</dt>
                  <dd>{row.payments_four_months[label] ?? '—'}</dd>
                </div>
              ))}
              <div>
                <dt>Статус</dt>
                <dd className={paymentStatusCellClass(row.payment_status)}>
                  {formatPaymentStatusLabel(row.payment_status)}
                </dd>
              </div>
            </dl>
            {tgUrl ? (
              <div className="debt-mobile-card__links">
                <a href={tgUrl} target="_blank" rel="noreferrer">
                  {row.display_telegram}
                </a>
              </div>
            ) : null}
            {isAdmin ? (
              <footer className="debt-mobile-card__actions">
                <Link className="btn-outline-primary btn-small" to={`/debts/${row.id}/edit`}>
                  Изменить
                </Link>
                <button
                  type="button"
                  className="btn-outline-danger btn-small"
                  onClick={() => {
                    if (window.confirm('Удалить запись о долге?')) {
                      onDeleteDebt(row.id)
                    }
                  }}
                >
                  Удалить
                </button>
              </footer>
            ) : null}
          </article>
        )
      })}
    </div>
  )
}

export default DebtListMobileCards
