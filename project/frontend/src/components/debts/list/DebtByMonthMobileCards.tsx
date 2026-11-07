import type { DebtByMonthRow } from '../../../types/debt'
import {
  balanceCellClass,
  debtRowClassName,
  formatActDate,
  paymentStatusCellClass,
} from '../../../utils/debts/debtTableDisplay'

interface DebtByMonthMobileCardsProps {
  results: DebtByMonthRow[]
  exportMonths: string[]
}

function DebtByMonthMobileCards({ results, exportMonths }: DebtByMonthMobileCardsProps) {
  return (
    <div className="debts-mobile-cards" aria-label="Долги за период (компактный вид)">
      {results.map((row) => (
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
              <dt>Статус</dt>
              <dd className={paymentStatusCellClass(row.payment_status)}>
                {row.payment_status_label}
              </dd>
            </div>
            <div>
              <dt>Сумма за период</dt>
              <dd>{row.total_period_amount}</dd>
            </div>
            {exportMonths.map((label) => (
              <div key={label}>
                <dt>{label}</dt>
                <dd>{row.period_amounts[label] ?? '—'}</dd>
              </div>
            ))}
          </dl>
        </article>
      ))}
    </div>
  )
}

export default DebtByMonthMobileCards
