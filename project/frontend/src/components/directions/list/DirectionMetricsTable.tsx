import { DATA_TABLE_STICKY_FIRST_COL_ONLY, DATA_TABLE_STICKY_LEADING } from '../../../constants/dataTableLayout'
import TableScroll from '../../ui/TableScroll'
import type { DirectionMetricRow } from '../../../types/direction'

function formatTableDate(iso: string | null): string {
  if (!iso) {
    return '—'
  }
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso)
  if (m) {
    return `${m[3]}.${m[2]}.${m[1]}`
  }
  return iso
}

interface DirectionMetricsTableProps {
  rows: DirectionMetricRow[]
  totalInterviews: number
  totalTechInterviews: number
  totalCandidates: number
  totalUpcoming: number
}

/** Таблица метрик по направлениям. */
function DirectionMetricsTable({
  rows,
  totalInterviews,
  totalTechInterviews,
  totalCandidates,
  totalUpcoming,
}: DirectionMetricsTableProps) {
  if (rows.length === 0) {
    return null
  }

  return (
    <TableScroll className="table-scroll--plain">
      <table
        className={`data-table data-table--directions ${DATA_TABLE_STICKY_LEADING} ${DATA_TABLE_STICKY_FIRST_COL_ONLY}`}
      >
        <caption className="visually-hidden">Метрики по направлениям</caption>
        <thead className="table-light">
          <tr>
            <th className="col-dir-name" scope="col">
              Направление
            </th>
            <th className="col-dir-num" scope="col">
              Интервью
            </th>
            <th className="col-dir-num" scope="col">
              Тех интервью
            </th>
            <th className="col-dir-num" scope="col">
              Кандидатов
            </th>
            <th className="col-dir-num" scope="col">
              Конверсия
            </th>
            <th className="col-dir-num" scope="col">
              Предстоящие
            </th>
            <th className="col-dir-date" scope="col">
              Последнее интервью
            </th>
          </tr>
        </thead>
        <tbody>
          {rows.map((metric) => (
            <tr key={metric.direction.id}>
              <td>{metric.direction.name ?? '—'}</td>
              <td>{metric.interviews}</td>
              <td>{metric.tech_interviews}</td>
              <td>{metric.candidates}</td>
              <td>{metric.conversion_rate}%</td>
              <td>{metric.upcoming_interviews}</td>
              <td>{formatTableDate(metric.last_interview_date)}</td>
            </tr>
          ))}
          <tr className="directions-table-total">
            <td>Итого:</td>
            <td>{totalInterviews}</td>
            <td>{totalTechInterviews}</td>
            <td>{totalCandidates}</td>
            <td>—</td>
            <td>{totalUpcoming}</td>
            <td>—</td>
          </tr>
        </tbody>
      </table>
    </TableScroll>
  )
}

export default DirectionMetricsTable
