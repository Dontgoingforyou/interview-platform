import { DATA_TABLE_STICKY_LEADING } from '../../../constants/dataTableLayout'
import { TableScroll } from '../../ui'
import type { ReactNode } from 'react'

import InterviewsDatabaseTableHead from './InterviewsDatabaseTableHead'
import InterviewsDatabaseTableRow from './InterviewsDatabaseTableRow'
import type { AuthUser } from '../../../store/authStore'
import type { InterviewListItem, InterviewsDatabaseListFilters } from '../../../types/interview'

interface InterviewsDatabaseDesktopTableProps {
  filters: InterviewsDatabaseListFilters
  onToggleSort: (field: string) => void
  results: InterviewListItem[]
  user: AuthUser | null
  showTranscriptionColumn: boolean
  renderTranscriptionCell: (row: InterviewListItem) => ReactNode
}

function InterviewsDatabaseDesktopTable({
  filters,
  onToggleSort,
  results,
  user,
  showTranscriptionColumn,
  renderTranscriptionCell,
}: InterviewsDatabaseDesktopTableProps) {
  return (
    <div className="interviews-table-desktop">
      <TableScroll className="table-scroll--plain">
        <table className={`data-table interviews-data-table ${DATA_TABLE_STICKY_LEADING}`}>
          <InterviewsDatabaseTableHead
            filters={filters}
            onToggleSort={onToggleSort}
            showTranscriptionColumn={showTranscriptionColumn}
          />
          <tbody>
            {results.map((row) => (
              <InterviewsDatabaseTableRow
                key={row.id}
                row={row}
                user={user}
                showTranscriptionColumn={showTranscriptionColumn}
                renderTranscriptionCell={renderTranscriptionCell}
              />
            ))}
          </tbody>
        </table>
      </TableScroll>
    </div>
  )
}

export default InterviewsDatabaseDesktopTable
