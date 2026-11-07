import SadInternListMobileCard from './SadInternListMobileCard'
import type { SadInternListItem } from '../../../types/sadIntern'

interface SadInternListMobileCardsProps {
  rows: SadInternListItem[]
  canWrite: boolean
  isAdmin: boolean
  onDelete: (id: number) => void
}

function SadInternListMobileCards({ rows, canWrite, isAdmin, onDelete }: SadInternListMobileCardsProps) {
  return (
    <div className="sad-intern-mobile-cards">
      {rows.map((row) => (
        <SadInternListMobileCard
          key={row.id}
          row={row}
          canWrite={canWrite}
          isAdmin={isAdmin}
          onDelete={onDelete}
        />
      ))}
    </div>
  )
}

export default SadInternListMobileCards
