import { Link } from 'react-router-dom'

import { DATA_TABLE_STICKY_LEADING } from '../../../constants/dataTableLayout'
import { TableScroll } from '../../ui'
import type { DebtListFilters, DebtListItem } from '../../../types/debt'
import {
  balanceCellClass,
  debtRowClassName,
  formatActDate,
  formatPaymentStatusLabel,
  paymentStatusCellClass,
  telegramHref,
} from '../../../utils/debts/debtTableDisplay'
import DebtListTableHead from './DebtListTableHead'

interface DebtListDesktopTableProps {
  filters: DebtListFilters
  onToggleSort: (field: string) => void
  results: DebtListItem[]
  lastFourMonthLabels: string[]
  isAdmin: boolean
  onDeleteDebt: (id: number) => void
}

function DebtListDesktopTable({
  filters,
  onToggleSort,
  results,
  lastFourMonthLabels,
  isAdmin,
  onDeleteDebt,
}: DebtListDesktopTableProps) {
  return (
    <TableScroll className="table-scroll--plain debts-table-desktop">
      <table className={`data-table data-table--debts ${DATA_TABLE_STICKY_LEADING}`}>
        <DebtListTableHead
          filters={filters}
          onToggleSort={onToggleSort}
          lastFourMonthLabels={lastFourMonthLabels}
          isAdmin={isAdmin}
        />
        <tbody>
          {results.map((row) => {
            const tgUrl = telegramHref(row.display_telegram)
            const lastPay =
              row.last_payment_month != null && row.last_payment_year != null
                ? `${row.last_payment_month}/${row.last_payment_year}`
                : '—'
            return (
              <tr key={row.id} className={debtRowClassName(row)}>
                <td>{row.id}</td>
                <td>{row.intern_name}</td>
                <td>{row.direction_name ?? '—'}</td>
                <td>
                  {tgUrl ? (
                    <a href={tgUrl} target="_blank" rel="noreferrer">
                      {row.display_telegram || '—'}
                    </a>
                  ) : (
                    '—'
                  )}
                </td>
                <td>{row.display_email || '—'}</td>
                <td>{row.total_amount}</td>
                <td>{row.paid_amount}</td>
                <td className={balanceCellClass(row.balance)}>{row.balance}</td>
                <td>{formatActDate(row.act_date)}</td>
                <td className="debts-col--spread debts-col--lastpay">{lastPay}</td>
                {lastFourMonthLabels.map((label) => (
                  <td key={label} className="debts-col--spread debts-col--month">
                    {row.payments_four_months[label] ?? '—'}
                  </td>
                ))}
                <td
                  className={[
                    'debts-col--spread',
                    'debts-col--status',
                    paymentStatusCellClass(row.payment_status),
                  ]
                    .filter(Boolean)
                    .join(' ')}
                >
                  {formatPaymentStatusLabel(row.payment_status)}
                </td>
                {isAdmin ? (
                  <td className="interviews-col-actions action-buttons">
                    <span className="interview-table-actions interview-table-actions--compact">
                      <Link
                        className="btn-outline-primary btn-small interviews-action-emoji"
                        title="Редактировать"
                        aria-label="Редактировать"
                        to={`/debts/${row.id}/edit`}
                      >
                        ✏️
                      </Link>
                      <button
                        type="button"
                        className="btn-outline-danger btn-small interviews-action-emoji"
                        title="Удалить"
                        aria-label="Удалить"
                        onClick={() => {
                          if (window.confirm('Удалить запись о долге? Это действие нельзя отменить.')) {
                            onDeleteDebt(row.id)
                          }
                        }}
                      >
                        🗑️
                      </button>
                    </span>
                  </td>
                ) : null}
              </tr>
            )
          })}
        </tbody>
      </table>
    </TableScroll>
  )
}

export default DebtListDesktopTable
