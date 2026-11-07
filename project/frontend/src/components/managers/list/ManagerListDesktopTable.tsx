import { DATA_TABLE_STICKY_FIRST_COL_ONLY, DATA_TABLE_STICKY_LEADING } from '../../../constants/dataTableLayout'
import { TableScroll } from '../../ui'
import type { ManagersDashboardTableRow } from '../../../types/managerDashboard'
import { formatRuDate } from '../../../utils/dateFormat'

interface ManagerListDesktopTableProps {
  rows: ManagersDashboardTableRow[]
}

function ManagerListDesktopTable({ rows }: ManagerListDesktopTableProps) {
  return (
    <TableScroll className="table-scroll--plain managers-table-desktop">
      <table
        className={`data-table data-table--managers ${DATA_TABLE_STICKY_LEADING} ${DATA_TABLE_STICKY_FIRST_COL_ONLY}`}
      >
        <thead className="table-light">
          <tr>
            <th className="col-manager-name">Менеджер</th>
            <th className="col-manager-total">Всего</th>
            <th className="col-manager-hot" title="Активно проходят интервью (за 7 дней)">
              Горячие
            </th>
            <th className="col-manager-active" title="Текущий активный пайплайн (за 20 дней)">
              В работе
            </th>
            <th className="col-manager-portfolio" title="Все кандидаты в работе (за 60 дней)">
              В портфеле
            </th>
            <th className="col-manager-interviews">Интервью</th>
            <th className="col-manager-successful">Успешные</th>
            <th className="col-manager-directions">Направления</th>
            <th className="col-manager-last-date">Последнее интервью</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.email}>
              <td>{row.full_name || '—'}</td>
              <td>{row.candidates_count}</td>
              <td>{row.hot_candidates_count}</td>
              <td>{row.active_candidates_count}</td>
              <td>{row.portfolio_candidates_count}</td>
              <td>{row.interviews_count}</td>
              <td>{row.successful_candidates_count}</td>
              <td className="col-manager-directions">{row.directions || '—'}</td>
              <td className="col-manager-last-date">{formatRuDate(row.last_interview_date)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </TableScroll>
  )
}

export default ManagerListDesktopTable
