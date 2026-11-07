import SadInternOnProjectMobileCard from './SadInternOnProjectMobileCard'
import type { SadInternListItem } from '../../../types/sadIntern'

interface SadInternOnProjectMobileCardsProps {
  rows: SadInternListItem[]
  canWrite: boolean
  isAdmin: boolean
  onDelete: (id: number) => void
}

function SadInternOnProjectMobileCards({
  rows,
  canWrite,
  isAdmin,
  onDelete,
}: SadInternOnProjectMobileCardsProps) {
  return (
    <div className="sad-intern-mobile-cards">
      {rows.map((row) => (
        <SadInternOnProjectMobileCard
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

export default SadInternOnProjectMobileCards
