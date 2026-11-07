import { DATA_TABLE_STICKY_LEADING } from '../../../constants/dataTableLayout'
import { TableScroll } from '../../ui'
import type { InternListFilters, InternListItem } from '../../../types/intern'
import InternListTableHead from './InternListTableHead'
import InternListTableRow from './InternListTableRow'

interface InternListDesktopTableProps {
  filters: InternListFilters
  onToggleSort: (field: string) => void
  results: InternListItem[]
  isAdmin: boolean
  onDeleteIntern: (id: number) => void
}

function InternListDesktopTable({
  filters,
  onToggleSort,
  results,
  isAdmin,
  onDeleteIntern,
}: InternListDesktopTableProps) {
  return (
    <TableScroll className="table-scroll--plain interns-table-desktop">
      <table className={`data-table data-table--interns ${DATA_TABLE_STICKY_LEADING}`}>
        <InternListTableHead filters={filters} onToggleSort={onToggleSort} />
        <tbody>
          {results.map((row) => (
            <InternListTableRow
              key={row.id}
              row={row}
              isAdmin={isAdmin}
              onDelete={onDeleteIntern}
            />
          ))}
        </tbody>
      </table>
    </TableScroll>
  )
}

export default InternListDesktopTable
