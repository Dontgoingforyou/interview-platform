import type { InternListItem } from '../../../types/intern'
import InternListMobileCard from './InternListMobileCard'

interface InternListMobileCardsProps {
  results: InternListItem[]
  isAdmin: boolean
  onDeleteIntern: (id: number) => void
}

function InternListMobileCards({
  results,
  isAdmin,
  onDeleteIntern,
}: InternListMobileCardsProps) {
  return (
    <div className="interns-mobile-cards">
      {results.map((row) => (
        <InternListMobileCard
          key={row.id}
          row={row}
          isAdmin={isAdmin}
          onDelete={onDeleteIntern}
        />
      ))}
    </div>
  )
}

export default InternListMobileCards
