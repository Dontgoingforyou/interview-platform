import type { ReactNode } from 'react'

import { DataTable } from '../../ui'
import { DATA_TABLE_STICKY_LEADING } from '../../../constants/dataTableLayout'
import InterviewListTableHead from './InterviewListTableHead'
import InterviewListTableRow from './InterviewListTableRow'
import type { AuthUser } from '../../../store/authStore'
import type { InterviewListFilters, InterviewListItem } from '../../../types/interview'

interface InterviewListDesktopTableProps {
  filters: InterviewListFilters
  onToggleSort: (field: string) => void
  results: InterviewListItem[]
  user: AuthUser | null
  canWrite: boolean
  isAdmin: boolean
  showReadonlyTranscriptionColumn: boolean
  renderTranscriptionCell: (row: InterviewListItem) => ReactNode
  onRequestDelete: (id: number) => void
}

/** Десктопная таблица списка собеседований. */
function InterviewListDesktopTable({
  filters,
  onToggleSort,
  results,
  user,
  canWrite,
  isAdmin,
  showReadonlyTranscriptionColumn,
  renderTranscriptionCell,
  onRequestDelete,
}: InterviewListDesktopTableProps) {
  return (
    <div className="interviews-table-desktop">
      <DataTable
        className={`data-table interviews-data-table ${DATA_TABLE_STICKY_LEADING}`}
        scrollClassName="table-scroll--plain"
      >
        <InterviewListTableHead
          filters={filters}
          onToggleSort={onToggleSort}
          canWrite={canWrite}
          showReadonlyTranscriptionColumn={showReadonlyTranscriptionColumn}
        />
        <tbody>
          {results.map((row) => (
            <InterviewListTableRow
              key={row.id}
              row={row}
              user={user}
              canWrite={canWrite}
              isAdmin={isAdmin}
              showReadonlyTranscriptionColumn={showReadonlyTranscriptionColumn}
              renderTranscriptionCell={renderTranscriptionCell}
              onRequestDelete={onRequestDelete}
            />
          ))}
        </tbody>
      </DataTable>
    </div>
  )
}

export default InterviewListDesktopTable
