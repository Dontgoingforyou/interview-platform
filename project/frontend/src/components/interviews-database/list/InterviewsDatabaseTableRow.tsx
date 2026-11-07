import type { ReactNode } from 'react'

import {
  databaseRecordingCell,
  hrContactsCell,
  vacancyCell,
} from '../../../utils/interviews/interviewCells'
import { formatShortRuDate } from '../../../utils/dateFormat'
import { interviewTypeBadgeClass } from '../../../utils/interviews/interviewListUi'
import {
  mayAccessInterviewTranscription,
  showTranscriptionControls,
} from '../../../utils/interviews/interviewTranscription'
import type { AuthUser } from '../../../store/authStore'
import type { InterviewListItem } from '../../../types/interview'

interface InterviewsDatabaseTableRowProps {
  row: InterviewListItem
  user: AuthUser | null
  showTranscriptionColumn: boolean
  renderTranscriptionCell: (row: InterviewListItem) => ReactNode
}

function InterviewsDatabaseTableRow({
  row,
  user,
  showTranscriptionColumn,
  renderTranscriptionCell,
}: InterviewsDatabaseTableRowProps) {
  const recording = databaseRecordingCell(row)
  const showTxInRecording =
    !showTranscriptionColumn &&
    showTranscriptionControls(row) &&
    mayAccessInterviewTranscription(user, row)
  const txSlot = renderTranscriptionCell(row)

  return (
    <tr>
      <td>{row.id}</td>
      <td>{row.intern_name}</td>
      <td>{row.company_name ?? '—'}</td>
      <td>{row.direction_name ?? '—'}</td>
      <td>
        <span className={`interview-type-badge ${interviewTypeBadgeClass(row.interview_type)}`}>
          {row.interview_type_display}
        </span>
      </td>
      <td>{formatShortRuDate(row.date)}</td>
      <td title={row.hr_name ?? ''}>{row.hr_name ?? '—'}</td>
      <td className="data-table-link-cell" title={row.hr_contacts ?? ''}>
        {hrContactsCell(row.hr_contacts)}
      </td>
      <td className="data-table-link-cell">
        <div className="interviews-database-recording-cell">
          {recording}
          {showTxInRecording && txSlot ? (
            <span className="interview-table-actions interview-table-actions--compact">{txSlot}</span>
          ) : null}
        </div>
      </td>
      <td className="data-table-link-cell">{vacancyCell(row.vacancy_link)}</td>
      {showTranscriptionColumn ? (
        <td className="action-buttons interview-table-actions">
          {showTranscriptionControls(row) && mayAccessInterviewTranscription(user, row) ? (
            <span className="interview-table-actions interview-table-actions--compact">{txSlot}</span>
          ) : (
            '—'
          )}
        </td>
      ) : null}
    </tr>
  )
}

export default InterviewsDatabaseTableRow
