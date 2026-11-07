import { DATA_TABLE_STICKY_LEADING } from '../../../constants/dataTableLayout'
import { TableScroll } from '../../ui'
import type { DebtByMonthRow } from '../../../types/debt'
import {
  balanceCellClass,
  debtRowClassName,
  formatActDate,
  paymentStatusCellClass,
} from '../../../utils/debts/debtTableDisplay'

interface DebtByMonthDesktopTableProps {
  results: DebtByMonthRow[]
  exportMonths: string[]
}

function DebtByMonthDesktopTable({ results, exportMonths }: DebtByMonthDesktopTableProps) {
  return (
    <TableScroll className="table-scroll--plain debts-table-desktop">
      <table className={`data-table data-table--debts-by-month ${DATA_TABLE_STICKY_LEADING}`}>
        <thead className="table-light">
          <tr>
            <th scope="col">ФИО студента</th>
            <th scope="col">Направление</th>
            <th scope="col">Общая сумма</th>
            <th scope="col">Уже заплатил</th>
            <th scope="col">Остаток</th>
            <th scope="col">Дата акта</th>
            <th scope="col">Статус</th>
            <th scope="col">Сумма за период</th>
            {exportMonths.map((label) => (
              <th key={label} scope="col">
                {label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {results.map((row) => (
            <tr key={row.id} className={debtRowClassName(row)}>
              <td>{row.intern_name}</td>
              <td>{row.direction_name ?? '—'}</td>
              <td>{row.total_amount}</td>
              <td>{row.paid_amount}</td>
              <td className={balanceCellClass(row.balance)}>{row.balance}</td>
              <td>{formatActDate(row.act_date)}</td>
              <td className={paymentStatusCellClass(row.payment_status)}>
                {row.payment_status_label}
              </td>
              <td>{row.total_period_amount}</td>
              {exportMonths.map((label) => (
                <td key={label}>{row.period_amounts[label] ?? '—'}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </TableScroll>
  )
}

export default DebtByMonthDesktopTable
