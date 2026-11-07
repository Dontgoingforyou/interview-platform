import { DATA_TABLE_STICKY_FIRST_COL_ONLY, DATA_TABLE_STICKY_LEADING } from '../../../constants/dataTableLayout'
import { TableScroll } from '../../ui'
import DeveloperListTableHead from './DeveloperListTableHead'
import type { DeveloperListFilters, DeveloperStatRow } from '../../../types/developer'

function formatActivity(iso: string | null): string {
  if (!iso) {
    return '—'
  }
  const d = new Date(`${iso}T12:00:00`)
  if (Number.isNaN(d.getTime())) {
    return iso
  }
  return d.toLocaleDateString('ru-RU')
}

interface DeveloperListDesktopTableProps {
  filters: DeveloperListFilters
  onToggleSort: (field: string) => void
  results: DeveloperStatRow[]
}

function DeveloperListDesktopTable({ filters, onToggleSort, results }: DeveloperListDesktopTableProps) {
  return (
    <TableScroll className="table-scroll--plain developers-table-desktop developers-table-scroll">
      <table
        className={`data-table data-table--developers ${DATA_TABLE_STICKY_LEADING} ${DATA_TABLE_STICKY_FIRST_COL_ONLY}`}
      >
        <DeveloperListTableHead filters={filters} onToggleSort={onToggleSort} />
        <tbody>
          {results.map((row) => (
            <tr key={`${row.intern_id}-${row.direction_id ?? 'x'}`}>
              <td className="col-dev-name">{row.intern_name}</td>
              <td className="col-dev-direction">{row.direction_name ?? '—'}</td>
              <td className="col-dev-activity">{formatActivity(row.last_interview_date)}</td>
              <td className="col-dev-count">{row.interview_count}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </TableScroll>
  )
}

export default DeveloperListDesktopTable
