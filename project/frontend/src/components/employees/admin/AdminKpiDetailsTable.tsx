import type { AdminKpiRow } from '../../../types/employee'

interface AdminKpiDetailsTableProps {
  row: AdminKpiRow
}

export default function AdminKpiDetailsTable({ row }: AdminKpiDetailsTableProps) {
  return (
    <div className="kpi-details-inner">
      <table className="kpi-sub-table">
        <thead>
          <tr>
            <th className="col-quarter">Неделя</th>
            <th className="col-quarter td-center">KPI</th>
            <th className="col-quarter td-center">Всего собеседований</th>
            <th className="col-quarter td-center">Активных разработчиков</th>
          </tr>
        </thead>
        <tbody>
          {row.qualifying_weeks.map((w) => (
            <tr key={`${w.week_start}-${w.week_end}`}>
              <td>
                {w.week_start} — {w.week_end}
              </td>
              <td className="td-center">
                <strong className="text-accent-green">{w.kpi}</strong>
              </td>
              <td className="td-center">{w.total_interviews}</td>
              <td className="td-center">{w.active_count}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
