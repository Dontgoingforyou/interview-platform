import type { ReactNode } from 'react'

import { InterviewMobileCard } from '../InterviewMobileCard'
import type { InterviewListItem } from '../../../types/interview'

interface InterviewListMobileCardsProps {
  results: InterviewListItem[]
  canWrite: boolean
  isAdmin: boolean
  onDelete: (id: number) => void
  renderTranscriptionCell: (row: InterviewListItem) => ReactNode
}

function InterviewListMobileCards({
  results,
  canWrite,
  isAdmin,
  onDelete,
  renderTranscriptionCell,
}: InterviewListMobileCardsProps) {
  return (
    <div className="interviews-mobile-cards" aria-label="Список собеседований (компактный вид)">
      {results.map((row) => (
        <InterviewMobileCard
          key={row.id}
          row={row}
          canWrite={canWrite}
          isAdmin={isAdmin}
          onDelete={onDelete}
          transcriptionSlot={renderTranscriptionCell(row)}
        />
      ))}
    </div>
  )
}

export default InterviewListMobileCards
